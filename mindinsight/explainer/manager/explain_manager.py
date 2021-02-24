# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_loader import ExplainLoader, _LoaderStatus
from mindinsight.utils.exceptions import ParamValueError, UnknownError

_MAX_LOADERS_NUM = 3


class _ExplainManagerStatus(BaseEnum):
    """Manager status."""
    INIT = 'INIT'
    LOADING = 'LOADING'
    STOPPING = 'STOPPING'
    DONE = 'DONE'


class ExplainManager:
    """ExplainManager."""

    def __init__(self, summary_base_dir: str):
        self._summary_base_dir = summary_base_dir
        self._loader_pool = OrderedDict()
        self._loading_status = _ExplainManagerStatus.INIT.value
        self._status_mutex = threading.Lock()
        self._load_data_mutex = threading.Lock()
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
                                  name='explainer.start_load_thread',
                                  args=(reload_interval,),
                                  daemon=True)
        thread.start()

    def get_job(self, loader_id: str) -> Optional[ExplainLoader]:
        """
        Return ExplainLoader given loader_id.

        If explain job w.r.t given loader_id is not found, None will be returned.

        Args:
            loader_id (str): The id of expected ExplainLoader.

        Returns:
            ExplainLoader, the data loader specified by loader_id.
        """
        self._check_status_valid()

        with self._loader_pool_mutex:
            if loader_id in self._loader_pool:
                self._loader_pool[loader_id].query_time = datetime.now().timestamp()
                self._loader_pool.move_to_end(loader_id, last=True)
                loader = self._loader_pool[loader_id]
                if loader.status == _LoaderStatus.STOP.value:
                    self._reload_data_again()
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
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1. Default: 0.
            limit (int): The max data items for per page. Default: 10.

        Returns:
            tuple, the elements of the returned tuple are:

                - total (int): The overall number of explain directories
                - dir_infos (list): List of summary directory info including the following attributes:

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
        # Allocate CPU resources to enable gunicorn to start the web service.
        time.sleep(1)
        while True:
            try:
                if self.status == _ExplainManagerStatus.STOPPING.value:
                    logger.debug('Current loading status is %s, we will not trigger repeat loading.',
                                 _ExplainManagerStatus.STOPPING.value)
                else:
                    logger.info('Starts triggering repeat loading, repeat interval: %r.', repeat_interval)
                    self._load_data()
                    if not repeat_interval:
                        return
                time.sleep(repeat_interval)
            except UnknownError as ex:
                logger.error('Unexpected error happens when loading data. Loading status: %s, loading pool size: %d'
                             'Detail: %s', self.status, len(self._loader_pool), str(ex))

    def _load_data(self):
        """
        Prepare loaders in cache and start loading the data from summaries.

        Only a limited number of loaders will be cached in terms of updated_time or query_time. The size of cache
        pool is determined by _MAX_LOADERS_NUM. When the manager start loading data, only the latest _MAX_LOADER_NUM
        summaries will be loaded in cache. If a cached loader if queries by 'get_job', the query_time of the loader
        will be updated as well as the the loader moved to the end of cache. If an uncached summary is queried,
        a new loader instance will be generated and put to the end cache.
        """
        try:
            with self._load_data_mutex:
                if self.status == _ExplainManagerStatus.LOADING.value:
                    logger.info('Current status is %s, will ignore to load data.', self.status)
                    return

                logger.info('Start to load data, and status change to %s.', _ExplainManagerStatus.LOADING.value)
                self.status = _ExplainManagerStatus.LOADING.value
                self._cache_loaders()

                if self.status == _ExplainManagerStatus.STOPPING.value:
                    logger.info('The manager status has been %s, will not execute loading.', self.status)
                    return
                self._execute_loading()

                logger.info('Load event data end, current status: %s, next status: %s, loader pool size: %d.',
                            self.status, _ExplainManagerStatus.DONE.value, len(self._loader_pool))

        except Exception as ex:
            logger.exception(ex)
            raise UnknownError(str(ex))
        finally:
            self.status = _ExplainManagerStatus.DONE.value

    def _cache_loaders(self):
        """Cache explain loader in cache pool."""
        dir_map_mtimes = []
        _, summaries_info = self._summary_watcher.list_explain_directories(self._summary_base_dir)

        for summary_info in summaries_info:
            summary_path = summary_info.get('relative_path')
            summary_update_time = summary_info.get('update_time').timestamp()

            if summary_path in self._loader_pool:
                summary_update_time = max(summary_update_time, self._loader_pool[summary_path].query_time)

            dir_map_mtimes.append((summary_info, summary_update_time))

        sorted_summaries_info = sorted(dir_map_mtimes, key=lambda x: x[1])[-_MAX_LOADERS_NUM:]

        with self._loader_pool_mutex:
            for summary_info, query_time in sorted_summaries_info:
                summary_path = summary_info['relative_path']
                if summary_path not in self._loader_pool:
                    loader = self._generate_loader_from_relative_path(summary_path)
                    # The added loader by automatically refresh, using file creation time as the query time
                    self._add_loader(loader)
                else:
                    self._loader_pool[summary_path].query_time = query_time
                    self._loader_pool.move_to_end(summary_path, last=True)

    def _generate_loader_from_relative_path(self, relative_path: str) -> ExplainLoader:
        """Generate explain loader from the given relative path."""
        self._check_summary_exist(relative_path)
        current_dir = os.path.realpath(FileHandler.join(self._summary_base_dir, relative_path))
        loader_id = self._generate_loader_id(relative_path)
        loader = ExplainLoader(loader_id=loader_id, summary_dir=current_dir)
        return loader

    def _add_loader(self, loader):
        """Add loader to the loader_pool."""
        if loader.train_id not in self._loader_pool:
            self._loader_pool[loader.train_id] = loader
        else:
            self._loader_pool.move_to_end(loader.train_id, last=True)

        while len(self._loader_pool) > self._max_loaders_num:
            self._loader_pool.popitem(last=False)

    def _execute_loading(self):
        """Execute the data loading."""
        # We will load the newest loader first.
        for loader_id in list(self._loader_pool.keys())[::-1]:
            with self._loader_pool_mutex:
                loader = self._loader_pool.get(loader_id, None)
                if loader is None:
                    logger.debug('Loader %r has been deleted, will not load data.', loader_id)
                    continue

            if self.status == _ExplainManagerStatus.STOPPING.value:
                logger.info('Loader %s status is %s, will return.', loader_id, loader.status)
                return

            loader.load()

    def _delete_loader(self, loader_id):
        """Delete loader given loader_id."""
        if loader_id in self._loader_pool:
            self._loader_pool.pop(loader_id)
            logger.debug('delete loader %s, and stop this loader loading data.', loader_id)

    def _check_status_valid(self):
        """Check manager status."""
        if self.status == _ExplainManagerStatus.INIT.value:
            raise exceptions.SummaryLogIsLoading('Data is loading, current status is %s' % self.status)

    def _check_summary_exist(self, loader_id):
        """Verify thee train_job is existed given loader_id."""
        if not self._summary_watcher.is_summary_directory(self._summary_base_dir, loader_id):
            raise ParamValueError('Can not find the train job in the manager.')

    def _reload_data_again(self):
        """Reload the data one more time."""
        logger.debug('Start to reload data again.')

        def _wrapper():
            if self.status == _ExplainManagerStatus.STOPPING.value:
                return
            self._stop_load_data()
            self._load_data()

        thread = threading.Thread(target=_wrapper, name='explainer.reload_data_thread')
        thread.daemon = False
        thread.start()

    def _stop_load_data(self):
        """Stop loading data, status changes to Stopping."""
        if self.status != _ExplainManagerStatus.LOADING.value:
            return

        logger.info('Start to stop loading data, set status to %s.', _ExplainManagerStatus.STOPPING.value)
        self.status = _ExplainManagerStatus.STOPPING.value

        for loader in self._loader_pool.values():
            loader.stop()

        while self.status != _ExplainManagerStatus.DONE.value:
            continue
        logger.info('Stop loading data end.')

    @property
    def status(self):
        """Get the status of this manager with lock."""
        with self._status_mutex:
            return self._loading_status

    @status.setter
    def status(self, status):
        """Set the status of this manager with lock."""
        with self._status_mutex:
            self._loading_status = status

    @staticmethod
    def _generate_loader_id(relative_path):
        """Generate loader id for given path"""
        loader_id = relative_path
        return loader_id


EXPLAIN_MANAGER = ExplainManager(summary_base_dir=settings.SUMMARY_BASE_DIR)
