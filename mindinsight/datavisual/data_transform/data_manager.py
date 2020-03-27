# Copyright 2019 Huawei Technologies Co., Ltd
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
"""
Management of all events data.

This module exists to all loaders.
It can read events data through the DataLoader.

This module also acts as a thread pool manager.
"""
import threading
import time

from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from mindinsight.conf import settings
from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.enums import DataManagerStatus
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import MAX_DATA_LOADER_SIZE
from mindinsight.datavisual.data_transform.loader_generators.data_loader_generator import DataLoaderGenerator
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.exceptions import ParamValueError


class DataManager:
    """
    DataManager manages a pool of loader which help access events data.

    Each loader helps deal the data of the events.
    A loader corresponds to an events_data.
    The DataManager build a pool including all the data_loader.
    The data_loader provides extracting
    method to get the information of events.
    """
    def __init__(self, loader_generators):
        """
        Initialize the pool of loader and the dict of name-to-path.

        Args:
            loader_generators (list[LoaderGenerator]): Loader generators help generate loaders.

        self._status: Refer `datavisual.common.enums.DataManagerStatus`.
        self._loader_pool: {'loader_id': <LoaderStruct>}.

        """
        self._loader_pool = {}
        self._deleted_id_list = []
        self._status = DataManagerStatus.INIT.value
        self._status_mutex = threading.Lock()
        self._loader_pool_mutex = threading.Lock()
        self._max_threads_count = 30
        self._reload_interval = 3

        self._loader_generators = loader_generators

    def _add_loader(self, loader):
        """
        Add a loader to load data.

        Args:
            loader (LoaderStruct): A object of `Loader`.

        """
        if len(self._loader_pool) >= MAX_DATA_LOADER_SIZE:
            delete_number = len(self._loader_pool) - MAX_DATA_LOADER_SIZE + 1
            sorted_loaders = sorted(self._loader_pool.items(),
                                    key=lambda loader: loader[1].latest_update_time)
            for index in range(delete_number):
                delete_loader_id = sorted_loaders[index][0]
                self._delete_loader(delete_loader_id)
        self._loader_pool.update({loader.loader_id: loader})

    def _delete_loader(self, loader_id):
        """
        Delete loader from loader pool by loader id.

        Args:
            loader_id (str): ID of loader.
        """
        if self._loader_pool.get(loader_id) is not None:
            logger.debug("delete loader %s", loader_id)
            self._loader_pool.pop(loader_id)

    def _execute_loader(self, loader_id):
        """
        Load data form data_loader.

        If there is something wrong by loading, add logs and delete the loader.

        Args:
            loader_id (str): An ID for `Loader`.

        """
        try:
            with self._loader_pool_mutex:
                loader = self._loader_pool.get(loader_id, None)
                if loader is None:
                    logger.debug("Loader %r has been deleted, will not load data.", loader_id)
                    return
            loader.data_loader.load()
        except MindInsightException as ex:
            logger.warning("Data loader %r load data failed. "
                           "Delete data_loader. Detail: %s", loader_id, ex)

            with self._loader_pool_mutex:
                self._delete_loader(loader_id)

    def start_load_data(self,
                        reload_interval=settings.RELOAD_INTERVAL,
                        max_threads_count=MAX_DATA_LOADER_SIZE):
        """
        Start threads for loading data.

        Args:
            reload_interval (int): Time to reload data once.
            max_threads_count (int): Max number of threads of execution.

        """
        logger.info("Start to load data, reload_interval: %s, "
                    "max_threads_count: %s.", reload_interval, max_threads_count)
        DataManager.check_reload_interval(reload_interval)
        DataManager.check_max_threads_count(max_threads_count)

        self._reload_interval = reload_interval
        self._max_threads_count = max_threads_count

        thread = threading.Thread(target=self._reload_data,
                                  name='start_load_data_thread')
        thread.daemon = True
        thread.start()

    def _reload_data(self):
        """This function periodically loads the data."""
        # Let gunicorn load other modules first.
        time.sleep(1)
        while True:
            self._load_data()

            if not self._reload_interval:
                break
            time.sleep(self._reload_interval)

    def reload_data(self):
        """
        Reload the data once.

        This function needs to be used after `start_load_data` function.
        """
        logger.debug("start to reload data")
        thread = threading.Thread(target=self._load_data,
                                  name='reload_data_thread')
        thread.daemon = False
        thread.start()

    def _load_data(self):
        """This function will load data once and ignore it if the status is loading."""
        logger.info("Start to load data, reload interval: %r.", self._reload_interval)
        with self._status_mutex:
            if self.status == DataManagerStatus.LOADING.value:
                logger.debug("Current status is %s , will ignore to load data.", self.status)
                return
            self.status = DataManagerStatus.LOADING.value

        self._generate_loaders()
        self._execute_load_data()

        if not self._loader_pool:
            self.status = DataManagerStatus.INVALID.value
        else:
            self.status = DataManagerStatus.DONE.value

        logger.info("Load event data end, status: %r, and loader pool size is %r.",
                    self.status, len(self._loader_pool))

    def _generate_loaders(self):
        """This function generates the loader from given path."""
        loader_dict = {}
        for generator in self._loader_generators:
            loader_dict.update(generator.generate_loaders(self._loader_pool))

        sorted_loaders = sorted(loader_dict.items(), key=lambda loader: loader[1].latest_update_time)
        latest_loaders = sorted_loaders[-MAX_DATA_LOADER_SIZE:]
        self._deal_loaders(latest_loaders)

    def _deal_loaders(self, latest_loaders):
        """
        This function determines which loaders to keep or remove or added.

        It is based on the given dict of loaders.

        Args:
            latest_loaders (list[dict]): A list of <loader_id: LoaderStruct>.
        """

        with self._loader_pool_mutex:
            for loader_id, loader in latest_loaders:
                if self._loader_pool.get(loader_id, None) is None:
                    self._add_loader(loader)
                    continue

                # If this loader was updated manually before,
                # its latest_update_time may bigger than update_time in summary.
                if self._loader_pool[loader_id].latest_update_time < loader.latest_update_time:
                    self._update_loader_latest_update_time(loader_id, loader.latest_update_time)

    def _execute_load_data(self):
        """Load data through multiple threads."""
        threads_count = self._get_threads_count()
        if not threads_count:
            logger.info("Can not find any valid train log path to load, loader pool is empty.")
            return

        logger.info("Start to execute load data. threads_count: %s.", threads_count)

        with ThreadPoolExecutor(max_workers=threads_count) as executor:
            futures = []
            loader_pool = self._get_snapshot_loader_pool()
            for loader_id in loader_pool:
                future = executor.submit(self._execute_loader, loader_id)
                futures.append(future)
            wait(futures, return_when=ALL_COMPLETED)

    @staticmethod
    def check_reload_interval(reload_interval):
        """
        Check reload interval is valid.

        Args:
            reload_interval (int): Reload interval >= 0.
        """
        if not isinstance(reload_interval, int):
            raise ParamValueError("The value of reload interval should be integer.")

        if reload_interval < 0:
            raise ParamValueError("The value of reload interval should be >= 0.")

    @staticmethod
    def check_max_threads_count(max_threads_count):
        """
        Threads count should be a integer, and should > 0.

        Args:
            max_threads_count (int), should > 0.
        """
        if not isinstance(max_threads_count, int):
            raise ParamValueError("The value of max threads count should be integer.")
        if max_threads_count <= 0:
            raise ParamValueError("The value of max threads count should be > 0.")

    def _get_threads_count(self):
        """
        Use the maximum number of threads available.

        Returns:
            int, number of threads.

        """
        threads_count = min(self._max_threads_count, len(self._loader_pool))

        return threads_count

    def get_train_job_by_plugin(self, train_id, plugin_name):
        """
        Get a train job by train job id.

        If the given train job does not has the given plugin data, the tag list will be empty.

        Args:
            train_id (str): Get train job info by the given id.
            plugin_name (str): Get tags by given plugin.

        Returns:
            TypedDict('TrainJobEntity', {'id': str, 'name': str, 'tags': List[str]}),
                a train job object.

        """
        self._check_status_valid()
        self._check_train_job_exist(train_id, self._loader_pool)

        loader = self._get_loader(train_id)
        if loader is None:
            logger.warning("No valid summary log in train job %s, "
                           "or it is not in the cache.", train_id)
            return None

        name = loader.name
        data_loader = loader.data_loader

        tags = []
        try:
            events_data = data_loader.get_events_data()
            tags = events_data.list_tags_by_plugin(plugin_name)
        except KeyError:
            logger.debug("Plugin name %r does not exist "
                         "in train job %r, and set tags to empty list.", plugin_name, name)
        except AttributeError:
            logger.debug("Train job %r has been deleted or it has not loaded data, "
                         "and set tags to empty list.", name)

        result = dict(id=train_id, name=name, tags=tags)
        return result

    def delete_train_job(self, train_id):
        """
        Delete train job with a train id.

        Args:
            train_id (str): ID for train job.

        """
        with self._loader_pool_mutex:
            self._delete_loader(train_id)

    def list_tensors(self, train_id, tag):
        """
        List tensors of the given train job and tag.

        If the tensor can not find by the given tag, will raise exception.

        Args:
            train_id (str): ID for train job.
            tag (str): The tag name.

        Returns:
            NamedTuple, the tuple format is `collections.namedtuple('_Tensor', ['wall_time', 'event_step', 'value'])`.
                the value will contain the given tag data.

        """
        self._check_status_valid()
        loader_pool = self._get_snapshot_loader_pool()
        if not self._is_loader_in_loader_pool(train_id, loader_pool):
            raise ParamValueError("Can not find any data in loader pool about the train job.")

        data_loader = loader_pool[train_id].data_loader
        events_data = data_loader.get_events_data()

        try:
            tensors = events_data.tensors(tag)
        except KeyError:
            error_msg = "Can not find any data in this train job by given tag."
            raise ParamValueError(error_msg)

        return tensors

    def _check_train_job_exist(self, train_id, loader_pool):
        """
        Check train job exist, if not exist, will raise exception.

        Args:
            train_id (str): The given train job id.
            loader_pool (dict[str, LoaderStruct]): Refer to self._loader_pool.

        Raises:
            ParamValueError: Can not found train job in data manager.
        """
        is_exist = False
        if train_id in loader_pool:
            return
        for generator in self._loader_generators:
            if generator.check_train_job_exist(train_id):
                is_exist = True
                break
        if not is_exist:
            raise ParamValueError("Can not find the train job in data manager.")

    def _is_loader_in_loader_pool(self, train_id, loader_pool):
        """
        Check train job exist, if not exist, return False. Else, return True.

        Args:
            train_id (str): The given train job id.
            loader_pool (dict): See self._loader_pool.

        Returns:
            bool, if loader in loader pool, return True.
        """
        if train_id in loader_pool:
            return True
        return False

    def _get_snapshot_loader_pool(self):
        """
        Create a snapshot of data loader pool to avoid concurrent mutation and iteration issues.

        Returns:
            dict, a copy of `self._loader_pool`.
        """
        with self._loader_pool_mutex:
            return dict(self._loader_pool)

    def _check_status_valid(self):
        """Check if the status is valid to load data."""

        if self.status == DataManagerStatus.INIT.value:
            raise exceptions.SummaryLogIsLoading("Data is being loaded, "
                                                 "current status: %s." % self._status)

    def get_single_train_job(self, train_id, manual_update=False):
        """
        Get train job by train ID.

        Args:
            train_id (str): Train ID for train job.
            manual_update (bool): If manual update, True.

        Returns:
            dict, single train job, if can not find any data, will return None.
        """
        self._check_status_valid()
        self._check_train_job_exist(train_id, self._loader_pool)

        loader = self._get_loader(train_id, manual_update)
        if loader is None:
            logger.warning("No valid summary log in train job %s, "
                           "or it is not in the cache.", train_id)
            return None

        train_job = loader.to_dict()
        train_job.pop('data_loader')

        plugin_data = {}
        for plugin_name in PluginNameEnum.list_members():
            job = self.get_train_job_by_plugin(train_id, plugin_name=plugin_name)
            if job is None:
                plugin_data[plugin_name] = []
            else:
                plugin_data[plugin_name] = job['tags']

        train_job.update({'tag_mapping': plugin_data})

        return train_job

    def _get_loader(self, train_id, manual_update=False):
        """
        Get loader by train id.

        Args:
            train_id (str): Train Id.
            manual_update (bool): If manual, True. Else False.

        Returns:
            LoaderStruct, the loader.
        """
        loader = None
        is_reload = False
        with self._loader_pool_mutex:
            if self._is_loader_in_loader_pool(train_id, self._loader_pool):
                loader = self._loader_pool.get(train_id)

            if manual_update and loader is None:
                for generator in self._loader_generators:
                    tmp_loader = generator.generate_loader_by_train_id(train_id)
                    if loader and loader.latest_update_time > tmp_loader.latest_update_time:
                        continue
                    loader = tmp_loader

                if loader is None:
                    return None

                self._add_loader(loader)
                is_reload = True

            if manual_update:
                self._update_loader_latest_update_time(loader.loader_id)

        if is_reload:
            self.reload_data()

        return loader

    def _update_loader_latest_update_time(self, loader_id, latest_update_time=None):
        """
        Update loader with latest_update_time.

        Args:
            loader_id (str): ID of loader.
            latest_update_time (float): Timestamp.
        """
        if latest_update_time is None:
            latest_update_time = time.time()
        self._loader_pool[loader_id].latest_update_time = latest_update_time

    @property
    def status(self):
        """
        Get the status of data manager.

        Returns:
            DataManagerStatus, the status of data manager.
        """
        return self._status

    @status.setter
    def status(self, status):
        """Set data manger status."""
        self._status = status


_loader_generators = [DataLoaderGenerator(settings.SUMMARY_BASE_DIR)]
DATA_MANAGER = DataManager(_loader_generators)
