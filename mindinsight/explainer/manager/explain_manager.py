# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""ExplainManager."""

import os
import threading
import time
from collections import OrderedDict
from datetime import datetime
from typing import Optional

from mindinsight.conf import settings
from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import BaseEnum
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_loader import ExplainLoader
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.utils.exceptions import MindInsightException, ParamValueError, UnknownError

_MAX_LOADERS_NUM = 3


class _ExplainManagerStatus(BaseEnum):
    """Manager status."""
    INIT = 'INIT'
    LOADING = 'LOADING'
    DONE = 'DONE'
    INVALID = 'INVALID'


class ExplainManager:
    """ExplainManager."""

    def __init__(self, summary_base_dir: str):
        self._summary_base_dir = summary_base_dir
        self._loader_pool = OrderedDict()
        self._loading_status = _ExplainManagerStatus.INIT.value
        self._status_mutex = threading.Lock()
        self._loader_pool_mutex = threading.Lock()
        self._max_loaders_num = _MAX_LOADERS_NUM
        self._summary_watcher = SummaryWatcher()

    @property
    def summary_base_dir(self):
        """Return the base directory for summary records."""
        return self._summary_base_dir

    def start_load_data(self, reload_interval: int = 0):
        """
        Start individual thread to cache explain_jobs and loading summary data periodically.

        Args:
            reload_interval (int): Specify the loading period in seconds. If interval == 0, data will only be loaded
            once. Default: 0.
        """
        thread = threading.Thread(target=self._repeat_loading,
                                  name='start_load_thread',
                                  args=(reload_interval,),
                                  daemon=True)
        time.sleep(1)
        thread.start()

    def get_job(self, loader_id: str) -> Optional[ExplainLoader]:
        """
        Return ExplainLoader given loader_id.

        If explain job w.r.t given loader_id is not found, None will be returned.

        Args:
            loader_id (str): The id of expected ExplainLoader

        Return:
            explain_job
        """
        self._check_status_valid()

        with self._loader_pool_mutex:
            if loader_id in self._loader_pool:
                self._loader_pool[loader_id].query_time = datetime.now().timestamp()
                self._loader_pool.move_to_end(loader_id, last=False)
                return self._loader_pool[loader_id]

            try:
                loader = self._generate_loader_from_relative_path(loader_id)
                loader.query_time = datetime.now().timestamp()
                self._add_loader(loader)
                self._reload_data_again()
            except ParamValueError:
                logger.warning('Cannot find summary in path: %s. No explain_job will be returned.', loader_id)
                return None
        return loader

    def get_job_list(self, offset=0, limit=None):
        """
        Return List of explain jobs. includes job ID, create and update time.

        Args:
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1. Default value is 0.
            limit (int): The max data items for per page. Default value is 10.

        Returns:
            tuple[total, directories], total indicates the overall number of explain directories and directories
                    indicate list of summary directory info including the following attributes.
                - relative_path (str): Relative path of summary directory, referring to settings.SUMMARY_BASE_DIR,
                                        starting with "./".
                - create_time (datetime): Creation time of summary file.
                - update_time (datetime): Modification time of summary file.
        """
        total, dir_infos = \
            self._summary_watcher.list_explain_directories(self._summary_base_dir, offset=offset, limit=limit)
        return total, dir_infos

    def _repeat_loading(self, repeat_interval):
        """Periodically loading summary."""
        while True:
            try:
                logger.info('Start to load data, repeat interval: %r.', repeat_interval)
                self._load_data()
                if not repeat_interval:
                    return
                time.sleep(repeat_interval)
            except UnknownError as ex:
                logger.exception(ex)
                logger.error('Unexpected error happens when loading data. Loading status: %s, loading pool size: %d'
                             'Detail: %s', self._loading_status, len(self._loader_pool), str(ex))

    def _load_data(self):
        """
        Prepare loaders in cache and start loading the data from summaries.

        Only a limited number of loaders will be cached in terms of updated_time or query_time. The size of cache
        pool is determined by _MAX_LOADERS_NUM. When the manager start loading data, only the lastest _MAX_LOADER_NUM
        summaries will be loaded in cache. If a cached loader if queries by 'get_job', the query_time of the loader
        will be updated as well as the the loader moved to the end of cache. If an uncached summary is queried,
        a new loader instance will be generated and put to the end cache.
        """
        try:
            with self._status_mutex:
                if self._loading_status == _ExplainManagerStatus.LOADING.value:
                    logger.info('Current status is %s, will ignore to load data.', self._loading_status)
                    return

                self._loading_status = _ExplainManagerStatus.LOADING.value

                self._cache_loaders()
                self._execute_loading()

                if not self._loader_pool:
                    self._loading_status = _ExplainManagerStatus.INVALID.value
                else:
                    self._loading_status = _ExplainManagerStatus.DONE.value

                logger.info('Load event data end, status: %s, and loader pool size: %d',
                            self._loading_status, len(self._loader_pool))

        except Exception as ex:
            self._loading_status = _ExplainManagerStatus.INVALID.value
            logger.exception(ex)
            raise UnknownError(str(ex))

    def _cache_loaders(self):
        """Cache explain loader in cache pool."""
        dir_map_mtime_dict = []
        _, summaries_info = self._summary_watcher.list_explain_directories(self._summary_base_dir)

        for summary_info in summaries_info:
            summary_path = summary_info.get('relative_path')
            summary_update_time = summary_info.get('update_time').timestamp()

            if summary_path in self._loader_pool:
                summary_update_time = max(summary_update_time, self._loader_pool[summary_path].query_time)

            dir_map_mtime_dict.append((summary_info, summary_update_time))

        sorted_summaries_info = sorted(dir_map_mtime_dict, key=lambda x: x[1])[-_MAX_LOADERS_NUM:]

        with self._loader_pool_mutex:
            for summary_info, query_time in sorted_summaries_info:
                summary_path = summary_info['relative_path']
                if summary_path not in self._loader_pool:
                    loader = self._generate_loader_from_relative_path(summary_path)
                    self._add_loader(loader)
                else:
                    self._loader_pool[summary_path].query_time = query_time
                    self._loader_pool.move_to_end(summary_path, last=False)

    def _generate_loader_from_relative_path(self, relative_path: str) -> ExplainLoader:
        """Generate explain loader from the given relative path."""
        self._check_summary_exist(relative_path)
        current_dir = os.path.realpath(FileHandler.join(self._summary_base_dir, relative_path))
        loader_id = self._generate_loader_id(relative_path)
        loader = ExplainLoader(loader_id=loader_id, summary_dir=current_dir)
        return loader

    def _add_loader(self, loader):
        """add loader to the loader_pool."""
        if loader.train_id not in self._loader_pool:
            self._loader_pool[loader.train_id] = loader
        else:
            self._loader_pool.move_to_end(loader.train_id)

        while len(self._loader_pool) > self._max_loaders_num:
            self._loader_pool.popitem(last=False)

    def _execute_loading(self):
        """Execute the data loading."""
        for loader_id in list(self._loader_pool.keys()):
            try:
                with self._loader_pool_mutex:
                    loader = self._loader_pool.get(loader_id, None)
                    if loader is None:
                        logger.debug('Loader %r has been deleted, will not load data', loader_id)
                        return
                loader.load()

            except MindInsightException as ex:
                logger.warning('Data loader %r load data failed. Delete data_loader. Detail: %s', loader_id, ex)
                with self._loader_pool_mutex:
                    self._delete_loader(loader_id)

    def _delete_loader(self, loader_id):
        """delete loader given loader_id"""
        if loader_id in self._loader_pool:
            self._loader_pool.pop(loader_id)
            logger.debug('delete loader %s', loader_id)

    def _check_status_valid(self):
        """Check manager status."""
        if self._loading_status == _ExplainManagerStatus.INIT.value:
            raise exceptions.SummaryLogIsLoading('Data is loading, current status is %s' % self._loading_status)

    def _check_summary_exist(self, loader_id):
        """Verify thee train_job is existed given loader_id."""
        if not self._summary_watcher.is_summary_directory(self._summary_base_dir, loader_id):
            raise ParamValueError('Can not find the train job in the manager.')

    def _reload_data_again(self):
        """Reload the data one more time."""
        logger.debug('Start to reload data again.')
        thread = threading.Thread(target=self._load_data, name='reload_data_thread')
        thread.daemon = False
        thread.start()

    @staticmethod
    def _generate_loader_id(relative_path):
        """Generate loader id for given path"""
        loader_id = relative_path
        return loader_id


EXPLAIN_MANAGER = ExplainManager(summary_base_dir=settings.SUMMARY_BASE_DIR)
