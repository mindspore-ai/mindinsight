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

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import BaseEnum
from mindinsight.explainer.common.log import logger
from mindinsight.explainer.manager.explain_job import ExplainJob
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.utils.exceptions import MindInsightException, ParamValueError, UnknownError

_MAX_LOADER_NUM = 3
_MAX_INTERVAL = 3


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
        self._loader_pool = {}
        self._deleted_ids = []
        self._status = _ExplainManagerStatus.INIT.value
        self._status_mutex = threading.Lock()
        self._loader_pool_mutex = threading.Lock()
        self._max_loader_num = _MAX_LOADER_NUM
        self._reload_interval = None

    def _reload_data(self):
        """periodically load summary from file."""
        while True:
            try:
                self._load_data()

                if not self._reload_interval:
                    break
                time.sleep(self._reload_interval)
            except UnknownError:
                self._status = _ExplainManagerStatus.INVALID.value

    def _load_data(self):
        """Loading the summary in the given base directory."""
        logger.info(
            'Start to load data, reload interval: %r.', self._reload_interval)

        with self._status_mutex:
            if self._status == _ExplainManagerStatus.LOADING.value:
                logger.info('Current status is %s, will ignore to load data.',
                            self._status)
                return

            self._status = _ExplainManagerStatus.LOADING.value

            try:
                self._generate_loaders()
                self._execute_load_data()
            except Exception as ex:
                raise UnknownError(ex)

            if not self._loader_pool:
                self._status = _ExplainManagerStatus.INVALID.value
            else:
                self._status = _ExplainManagerStatus.DONE.value

            logger.info('Load event data end, status: %r, '
                        'and loader pool size is %r',
                        self._status, len(self._loader_pool))

    def _update_loader_latest_update_time(self, loader_id, latest_update_time=None):
        """update the update time of loader of given id."""
        if latest_update_time is None:
            latest_update_time = time.time()
        self._loader_pool[loader_id].latest_update_time = latest_update_time

    def _delete_loader(self, loader_id):
        """delete loader given loader_id"""
        if self._loader_pool.get(loader_id, None) is not None:
            self._loader_pool.pop(loader_id)
            logger.debug('delete loader %s', loader_id)

    def _add_loader(self, loader):
        """add loader to the loader_pool."""
        if len(self._loader_pool) >= _MAX_LOADER_NUM:
            delete_num = len(self._loader_pool) - _MAX_LOADER_NUM + 1
            sorted_loaders = sorted(
                self._loader_pool.items(),
                key=lambda x: x[1].latest_update_time)

            for index in range(delete_num):
                delete_loader_id = sorted_loaders[index][0]
                self._delete_loader(delete_loader_id)
        self._loader_pool.update({loader.loader_id: loader})

    def _deal_loaders(self, latest_loaders):
        """"update the loader pool."""
        with self._loader_pool_mutex:
            for loader_id, loader in latest_loaders:
                if self._loader_pool.get(loader_id, None) is None:
                    self._add_loader(loader)
                    continue

                if (self._loader_pool[loader_id].latest_update_time
                        < loader.latest_update_time):
                    self._update_loader_latest_update_time(
                        loader_id, loader.latest_update_time)

    @staticmethod
    def _generate_loader_id(relative_path):
        """Generate loader id for given path"""
        loader_id = relative_path
        return loader_id

    @staticmethod
    def _generate_loader_name(relative_path):
        """Generate_loader name for given path."""
        loader_name = relative_path
        return loader_name

    def _generate_loader_by_relative_path(self, relative_path: str) -> ExplainJob:
        """Generate explain job from given relative path."""
        current_dir = os.path.realpath(FileHandler.join(
            self._summary_base_dir, relative_path
        ))
        loader_id = self._generate_loader_id(relative_path)
        loader = ExplainJob(
            job_id=loader_id,
            summary_dir=current_dir,
            create_time=ExplainJob.get_create_time(current_dir),
            latest_update_time=ExplainJob.get_update_time(current_dir))
        return loader

    def _generate_loaders(self):
        """Generate job loaders from the summary watcher."""
        dir_map_mtime_dict = {}
        loader_dict = {}
        min_modify_time = None
        _, summaries = SummaryWatcher().list_explain_directories(
            self._summary_base_dir)

        for item in summaries:
            relative_path = item.get('relative_path')
            modify_time = item.get('update_time').timestamp()
            loader_id = self._generate_loader_id(relative_path)

            loader = self._loader_pool.get(loader_id, None)
            if loader is not None and loader.latest_update_time > modify_time:
                modify_time = loader.latest_update_time

            if min_modify_time is None:
                min_modify_time = modify_time

            if len(dir_map_mtime_dict) < _MAX_LOADER_NUM:
                if modify_time < min_modify_time:
                    min_modify_time = modify_time
                dir_map_mtime_dict.update({relative_path: modify_time})
            else:
                if modify_time >= min_modify_time:
                    dir_map_mtime_dict.update({relative_path: modify_time})

        sorted_dir_tuple = sorted(dir_map_mtime_dict.items(),
                                  key=lambda d: d[1])[-_MAX_LOADER_NUM:]

        for relative_path, modify_time in sorted_dir_tuple:
            loader_id = self._generate_loader_id(relative_path)
            loader = self._generate_loader_by_relative_path(relative_path)
            loader_dict.update({loader_id: loader})

        sorted_loaders = sorted(loader_dict.items(),
                                key=lambda x: x[1].latest_update_time)
        latest_loaders = sorted_loaders[-_MAX_LOADER_NUM:]
        self._deal_loaders(latest_loaders)

    def _execute_loader(self, loader_id):
        """Execute the data loading."""
        try:
            with self._loader_pool_mutex:
                loader = self._loader_pool.get(loader_id, None)
                if loader is None:
                    logger.debug('Loader %r has been deleted, will not load'
                                 'data', loader_id)
                    return
            loader.load()

        except MindInsightException as e:
            logger.warning('Data loader %r load data failed. Delete data_loader. Detail: %s', loader_id, e)
            with self._loader_pool_mutex:
                self._delete_loader(loader_id)

    def _execute_load_data(self):
        """Execute the loader in the pool to load data."""
        loader_pool = self._get_snapshot_loader_pool()
        for loader_id in loader_pool:
            self._execute_loader(loader_id)

    def _get_snapshot_loader_pool(self):
        """Get snapshot of loader_pool."""
        with self._loader_pool_mutex:
            return dict(self._loader_pool)

    def _check_status_valid(self):
        """Check manager status."""
        if self._status == _ExplainManagerStatus.INIT.value:
            raise exceptions.SummaryLogIsLoading('Data is loading, current status is %s' % self._status)

    @staticmethod
    def _check_train_id_valid(train_id: str):
        """Verify the train_id is valid."""
        if not train_id.startswith('./'):
            logger.warning('train_id does not start with "./"')
            return False

        if len(train_id.split('/')) > 2:
            logger.warning('train_id contains multiple "/"')
            return False
        return True

    def _check_train_job_exist(self, train_id):
        """Verify thee train_job is existed given train_id."""
        if train_id in self._loader_pool:
            return
        self._check_train_id_valid(train_id)
        if SummaryWatcher().is_summary_directory(self._summary_base_dir, train_id):
            return
        raise ParamValueError('Can not find the train job in the manager, train_id: %s' % train_id)

    def _reload_data_again(self):
        """Reload the data one more time."""
        logger.debug('Start to reload data again.')
        thread = threading.Thread(target=self._load_data,
                                  name='reload_data_thread')
        thread.daemon = False
        thread.start()

    def _get_job(self, train_id):
        """Retrieve train_job given train_id."""
        is_reload = False
        with self._loader_pool_mutex:
            loader = self._loader_pool.get(train_id, None)

            if loader is None:
                relative_path = train_id
                temp_loader = self._generate_loader_by_relative_path(
                    relative_path)

                if temp_loader is None:
                    return None

                self._add_loader(temp_loader)
                is_reload = True

        if is_reload:
            self._reload_data_again()
        return loader

    @property
    def summary_base_dir(self):
        """Return the base directory for summary records."""
        return self._summary_base_dir

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
        watcher = SummaryWatcher()
        total, dir_infos = \
            watcher.list_explain_directories(self._summary_base_dir,
                                             offset=offset, limit=limit)
        return total, dir_infos

    def get_job(self, train_id):
        """
        Return ExplainJob given train_id.

        If explain job w.r.t given train_id is not found, None will be returned.

        Args:
            train_id (str): The id of expected ExplainJob

        Return:
            explain_job
        """
        self._check_status_valid()
        self._check_train_job_exist(train_id)

        loader = self._get_job(train_id)
        if loader is None:
            return None
        return loader

    def start_load_data(self,
                        reload_interval=_MAX_INTERVAL):
        """
        Start threads for loading data.

        Args:
            reload_interval (int): interval to reload the summary from file
        """
        self._reload_interval = reload_interval

        thread = threading.Thread(target=self._reload_data, name='start_load_data_thread')
        thread.daemon = True
        thread.start()

        # wait for data loading
        time.sleep(1)
