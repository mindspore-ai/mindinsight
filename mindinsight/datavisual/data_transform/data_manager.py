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
import abc
import datetime
import threading
import time
import os
from typing import Iterable, Optional

from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher

from mindinsight.conf import settings
from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import CacheStatus
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.enums import DataManagerStatus
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import MAX_DATA_LOADER_SIZE
from mindinsight.datavisual.data_transform.loader_generators.data_loader_generator import DataLoaderGenerator
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.exceptions import ParamValueError


class _BasicTrainJob:
    """
    Basic info about train job.

    Args:
        train_id (str): Id of the train job.
        abs_summary_base_dir (str): The canonical path of summary base directory. It should be the return value of
            realpath().
        abs_summary_dir (str): The canonical path of summary directory. It should be the return value of realpath().
        create_time (DateTime): The create time of summary directory.
        update_time (DateTime): The latest modify time of summary files directly in the summary directory.
        profiler_dir (str): The relative path of profiler directory.
    """
    def __init__(self, train_id, abs_summary_base_dir, abs_summary_dir, create_time, update_time, profiler_dir):
        self._train_id = train_id
        self._abs_summary_base_dir = abs_summary_base_dir
        self._abs_summary_dir = abs_summary_dir
        self._create_time = create_time
        self._update_time = update_time
        self._profiler_dir = profiler_dir

    @property
    def abs_summary_dir(self):
        """Get summary directory path."""
        return self._abs_summary_dir

    @property
    def summary_base_dir(self):
        """Get summary base directory path."""
        return self._abs_summary_base_dir

    @property
    def train_id(self):
        """Get train id."""
        return self._train_id

    @property
    def profiler_dir(self):
        """Get profiler directory path."""
        return self._profiler_dir

    @property
    def create_time(self):
        """Get create time."""
        return self._create_time

    @property
    def update_time(self):
        """Get update time."""
        return self._update_time


class CachedTrainJob:
    """
    Cache item for BriefCacheManager.

    DetailCacheManager will also wrap it's return value with this class.

    Args:
        basic_info (_BasicTrainJob): Basic info about the train job.
    """
    def __init__(self, basic_info: _BasicTrainJob):
        self._basic_info = basic_info
        self._last_access_time = datetime.datetime.utcnow()

        # Other cached content is stored here.
        self._content = {}

        self._cache_status = CacheStatus.NOT_IN_CACHE
        self._key_locks = {}

    @property
    def cache_status(self):
        """Get cache status."""
        return self._cache_status

    @cache_status.setter
    def cache_status(self, value):
        """Set cache status."""
        self._cache_status = value

    def update_access_time(self):
        """Update last access time of this cache item."""
        self._last_access_time = datetime.datetime.utcnow()

    @property
    def last_access_time(self):
        """Get last access time for purposes such as LRU."""
        return self._last_access_time

    @property
    def abs_summary_dir(self):
        """Get summary directory path."""
        return self._basic_info.abs_summary_dir

    @property
    def summary_base_dir(self):
        """Get summary base directory path."""
        return self._basic_info.summary_base_dir

    def set(self, key, value):
        """Set value to cache."""
        self._content[key] = value

    def delete(self, key):
        """Delete key in cache."""
        if key in self._content:
            self._content.pop(key)

    def get(self, key, raise_exception=True):
        """
        Get value from cache.

        Args:
            key (str): Key of content.
            raise_exception (bool): If the key does not exist and
                raise_exception is True, it will raise an Exception.

        Returns:
            Union[Object, None], Return value if key in content,
                return False else if raise_exception is False.
        Raises:
            ParamValueError, if the key does not exist and raise_exception is True.

        """
        try:
            return self._content[key]
        except KeyError:
            if raise_exception:
                raise ParamValueError("Invalid cache key({}).".format(key))
            return None

    @property
    def basic_info(self):
        """Get basic train job info."""
        return self._basic_info

    @basic_info.setter
    def basic_info(self, value):
        """Set basic train job info."""
        self._basic_info = value

    def lock_key(self, key):
        """Threading lock with given key."""
        return self._key_locks.setdefault(key, threading.Lock())


class TrainJob:
    """
    Train job object.

    You must not create TrainJob objects manually. You should always get TrainJob objects from DataManager.

    Args:
        brief_train_job (CachedTrainJob): Brief info about train job.
        detail_train_job (Optional[CachedTrainJob]): Detailed info about train job. Default: None.
    """
    def __init__(self,
                 brief_train_job: CachedTrainJob,
                 detail_train_job: Optional[CachedTrainJob] = None):
        self._brief = brief_train_job
        self._detail = detail_train_job
        if self._detail is None:
            self._cache_status = CacheStatus.NOT_IN_CACHE
        else:
            self._cache_status = self._detail.cache_status

    def has_detail(self):
        """Whether this train job has detailed info in cache."""
        return bool(self._detail is not None)

    def get_detail(self, key):
        """
        Get detail content.

        Args:
            key (Any): Cache key.

        Returns:
            Any, cache content.

        Raises:
            TrainJobDetailNotInCacheError: when this train job has no detail cache.

        """
        if not self.has_detail():
            raise exceptions.TrainJobDetailNotInCacheError()
        return self._detail.get(key)

    def get_brief(self, key):
        """
        Get brief content.

        Args:
            key (Any): Cache key.

        Returns:
            Any, cache content.
        """
        return self._brief.get(key)

    def get_basic_info(self):
        """
        Get basic info.

        Returns:
            basic_info (_BasicTrainJob): Basic info about the train job.
        """
        return self._brief.basic_info

    @property
    def cache_status(self):
        """Get cache status."""
        return self._cache_status

    @cache_status.setter
    def cache_status(self, cache_status):
        """Set cache status."""
        self._cache_status = cache_status


class BaseCacheItemUpdater(abc.ABC):
    """Abstract base class for other modules to update cache content."""
    def update_item(self, cache_item: CachedTrainJob):
        """
        Update cache item in place.

        Args:
            cache_item (CachedTrainJob): The cache item to be processed.
        """
        raise NotImplementedError()


class _BaseCacheManager:
    """Base class for cache manager."""

    def __init__(self):
        # Use dict to remove duplicate updaters.
        self._updaters = {}

        # key is train_id
        self._lock = threading.Lock()
        self._cache_items = {}

    def size(self):
        """Gets used cache slots."""
        return len(self._cache_items)

    def register_cache_item_updater(self, updater: BaseCacheItemUpdater):
        """Register cache item updater."""
        self._updaters[updater.__class__.__qualname__] = updater

    def get_train_jobs(self):
        """Get cached train jobs."""
        copied_train_jobs = dict(self._cache_items)
        return copied_train_jobs

    def get_train_job(self, train_id):
        """Get cached train job."""
        try:
            return self._cache_items[train_id]
        except KeyError:
            raise TrainJobNotExistError(train_id)

    def cache_train_job(self, train_id) -> bool:
        """
        Cache given train job and update train job's last access time.

        This method should return true if reload actions should be taken to cache the train job.

        Args:
            train_id (str): Train Id.
        """
        raise NotImplementedError()

    def delete_train_job(self, train_id):
        """Delete train job from cache."""
        if train_id in self._cache_items:
            del self._cache_items[train_id]

    def has_content(self):
        """Whether this cache manager has train jobs."""
        return bool(self._cache_items)

    def update_cache(self, disk_train_jobs: Iterable[_BasicTrainJob]):
        """
        Update cache according to given train jobs on disk.

        Different cache manager should implement different cache update policies in this method.

        Args:
            disk_train_jobs (Iterable[_BasicTrainJob]): Train jobs on disk.
        """
        raise NotImplementedError()

    def _merge_with_disk(self, disk_train_jobs: Iterable[_BasicTrainJob]):
        """
        Merge train jobs in cache with train jobs from disk

        This method will remove train jobs not on disk. Call this function with lock for thread safety.

        Args:
            disk_train_jobs (Iterable[_BasicTrainJob]): Basic train jobs info from disk.

        Returns:
            dict, a dict containing train jobs to be cached.
        """
        new_cache_items = {}
        for train_job in disk_train_jobs:
            if train_job.train_id not in self._cache_items:
                new_cache_items[train_job.train_id] = CachedTrainJob(train_job)
            else:
                reused_train_job = self._cache_items[train_job.train_id]
                reused_train_job.basic_info = train_job
                new_cache_items[train_job.train_id] = reused_train_job

        return new_cache_items


class _BriefCacheManager(_BaseCacheManager):
    """A cache manager that holds all disk train jobs on disk."""

    def cache_train_job(self, train_id):
        """
        Cache given train job.

        All disk train jobs are cached on every reload, so this method always return false.

        Args:
            train_id (str): Train Id.
        """
        if train_id in self._cache_items:
            self._cache_items[train_id].update_access_time()

        return False

    def update_cache(self, disk_train_jobs):
        """Update cache."""
        with self._lock:
            new_cache_items = self._merge_with_disk(disk_train_jobs)
            self._cache_items = new_cache_items
        for updater in self._updaters.values():
            for cache_item in self._cache_items.values():
                updater.update_item(cache_item)

    @property
    def cache_items(self):
        """Get cache items."""
        return self._cache_items


# Key for plugin tags.
DATAVISUAL_PLUGIN_KEY = "tag_mapping"
# Detail train job cache key for datavisual content.
DATAVISUAL_CACHE_KEY = "datavisual"


class _DetailCacheManager(_BaseCacheManager):
    """A cache manager that holds detailed info for most recently used train jobs."""
    def __init__(self, loader_generators):
        super().__init__()
        self._loader_pool = {}
        self._deleted_id_list = []
        self._loader_pool_mutex = threading.Lock()
        self._max_threads_count = 30
        self._loader_generators = loader_generators

    def has_content(self):
        """Whether this cache manager has train jobs."""
        return bool(self._loader_pool)

    def size(self):
        """
        Get the number of items in this cache manager.

        To be implemented.

        Returns:
            int, the number of items in this cache manager.
        """
        raise NotImplementedError()

    def loader_pool_size(self):
        """Get loader pool size."""
        return len(self._loader_pool)

    def update_cache(self, disk_train_jobs: Iterable[_BasicTrainJob]):
        """
        Update cache.

        Will switch to using disk_train_jobs in the future.

        Args:
            disk_train_jobs (Iterable[_BasicTrainJob]): Basic info about train jobs on disk.

        """
        self._generate_loaders()
        self._execute_load_data()

    def cache_train_job(self, train_id):
        """Cache given train job."""
        loader = None
        need_reload = False
        with self._loader_pool_mutex:
            if self._is_loader_in_loader_pool(train_id, self._loader_pool):
                loader = self._loader_pool.get(train_id)

            if loader is None:
                for generator in self._loader_generators:
                    tmp_loader = generator.generate_loader_by_train_id(train_id)
                    if loader and loader.latest_update_time > tmp_loader.latest_update_time:
                        continue
                    loader = tmp_loader

                if loader is None:
                    raise TrainJobNotExistError(train_id)

                # Update cache status loader to CACHING if loader is NOT_IN_CACHE
                # before triggering the next interval.
                if loader.cache_status == CacheStatus.NOT_IN_CACHE:
                    loader.cache_status = CacheStatus.CACHING

                self._add_loader(loader)
                need_reload = True

        self._update_loader_latest_update_time(loader.loader_id)
        return need_reload

    def get_train_jobs(self):
        """
        Get train jobs

        To be implemented.
        """

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

            # Update loader cache status to CACHED.
            # Loader with cache status CACHED should remain the same cache status.
            loader.cache_status = CacheStatus.CACHED

        except MindInsightException as ex:
            logger.warning("Data loader %r load data failed. "
                           "Delete data_loader. Detail: %s", loader_id, ex)

            with self._loader_pool_mutex:
                self._delete_loader(loader_id)

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

    def _get_threads_count(self):
        """
        Use the maximum number of threads available.

        Returns:
            int, number of threads.

        """
        threads_count = min(self._max_threads_count, len(self._loader_pool))

        return threads_count

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
        loader_pool = self._get_snapshot_loader_pool()
        if not self._is_loader_in_loader_pool(train_id, loader_pool):
            raise TrainJobNotExistError("Can not find the given train job in cache.")

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
            TrainJobNotExistError: Can not find train job in data manager.
        """
        is_exist = False
        if train_id in loader_pool:
            return
        for generator in self._loader_generators:
            if generator.check_train_job_exist(train_id):
                is_exist = True
                break
        if not is_exist:
            raise TrainJobNotExistError("Can not find the train job in data manager.")

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

    def get_train_job(self, train_id):
        """
        Get train job by train ID.

        This method overrides parent method.

        Args:
            train_id (str): Train ID for train job.
        Returns:
            dict, single train job, if can not find any data, will return None.
        """
        self._check_train_job_exist(train_id, self._loader_pool)

        loader = self._get_loader(train_id)
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

        train_job.update({DATAVISUAL_PLUGIN_KEY: plugin_data})

        # Will fill basic_info value in future.
        train_job_obj = CachedTrainJob(basic_info=None)
        train_job_obj.set(DATAVISUAL_CACHE_KEY, train_job)

        train_job_obj.cache_status = loader.cache_status

        return train_job_obj

    def _get_loader(self, train_id):
        """
        Get loader by train id.

        Args:
            train_id (str): Train Id.

        Returns:
            LoaderStruct, the loader.
        """
        loader = None
        with self._loader_pool_mutex:
            if self._is_loader_in_loader_pool(train_id, self._loader_pool):
                loader = self._loader_pool.get(train_id)

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


class DataManager:
    """
    DataManager manages a pool of loader which help access events data.

    Each loader helps deal the data of the events.
    A loader corresponds to an events_data.
    The DataManager build a pool including all the data_loader.
    The data_loader provides extracting
    method to get the information of events.
    """
    def __init__(self, summary_base_dir):
        """
        Initialize the pool of loader and the dict of name-to-path.

        Args:
            summary_base_dir (str): Base summary directory.

        self._status: Refer `datavisual.common.enums.DataManagerStatus`.

        """
        self._summary_base_dir = os.path.realpath(summary_base_dir)
        self._status = DataManagerStatus.INIT.value
        self._status_mutex = threading.Lock()

        self._reload_interval = 3

        loader_generators = [DataLoaderGenerator(self._summary_base_dir)]
        self._detail_cache = _DetailCacheManager(loader_generators)
        self._brief_cache = _BriefCacheManager()

    @property
    def summary_base_dir(self):
        """Get summary base dir."""
        return self._summary_base_dir

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

        thread = threading.Thread(target=self._reload_data_in_thread,
                                  name='start_load_data_thread')
        thread.daemon = True
        thread.start()

    def _reload_data_in_thread(self):
        """This function periodically loads the data."""
        # Let gunicorn load other modules first.
        time.sleep(1)
        while True:
            self._load_data_in_thread()

            if not self._reload_interval:
                break
            time.sleep(self._reload_interval)

    def reload_data(self):
        """
        Reload the data once.

        This function needs to be used after `start_load_data` function.
        """
        logger.debug("start to reload data")
        thread = threading.Thread(target=self._load_data_in_thread,
                                  name='reload_data_thread')
        thread.daemon = False
        thread.start()

    def _load_data_in_thread(self):
        """Log (but not swallow) exceptions in thread to help debugging."""
        try:
            self._load_data()
        except Exception as exc:
            logger.exception(exc)
            raise

    def _load_data(self):
        """This function will load data once and ignore it if the status is loading."""
        logger.info("Start to load data, reload interval: %r.", self._reload_interval)
        with self._status_mutex:
            if self.status == DataManagerStatus.LOADING.value:
                logger.debug("Current status is %s , will ignore to load data.", self.status)
                return
            self.status = DataManagerStatus.LOADING.value

        summaries_info = SummaryWatcher().list_summary_directories(self._summary_base_dir)

        basic_train_jobs = []
        for info in summaries_info:
            profiler = info['profiler']
            basic_train_jobs.append(_BasicTrainJob(
                train_id=info['relative_path'],
                abs_summary_base_dir=self._summary_base_dir,
                abs_summary_dir=os.path.realpath(os.path.join(
                    self._summary_base_dir,
                    info['relative_path']
                )),
                create_time=info['create_time'],
                update_time=info['update_time'],
                profiler_dir=None if profiler is None else profiler['directory'],
            ))

        self._brief_cache.update_cache(basic_train_jobs)
        self._detail_cache.update_cache(basic_train_jobs)

        if not self._brief_cache.has_content() and not self._detail_cache.has_content():
            self.status = DataManagerStatus.INVALID.value
        else:
            self.status = DataManagerStatus.DONE.value

        logger.info("Load event data end, status: %r, and loader pool size is %r.",
                    self.status, self._detail_cache.loader_pool_size())

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
        return self._detail_cache.get_train_job_by_plugin(train_id, plugin_name)

    def delete_train_job(self, train_id, only_delete_from_cache=True):
        """
        Delete train job with a train id.

        Args:
            train_id (str): ID for train job.

        """
        if not only_delete_from_cache:
            raise NotImplementedError("Delete from both cache and disk is not supported.")

        self._brief_cache.delete_train_job(train_id)
        self._detail_cache.delete_train_job(train_id)

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
        return self._detail_cache.list_tensors(train_id, tag)

    def _check_status_valid(self):
        """Check if the status is valid to load data."""

        if self.status == DataManagerStatus.INIT.value:
            raise exceptions.SummaryLogIsLoading("Data is being loaded, current status: %s." % self._status)

    def get_train_job(self, train_id):
        """
        Get train job by train ID.

        Args:
            train_id (str): Train ID for train job.

        Returns:
            dict, single train job, if can not find any data, will return None.
        """
        self._check_status_valid()
        detail_train_job = self._detail_cache.get_train_job(train_id)
        brief_train_job = self._brief_cache.get_train_job(train_id)

        return TrainJob(brief_train_job, detail_train_job)

    def list_train_jobs(self):
        """
        List train jobs.

        To be implemented.
        """
        raise NotImplementedError()

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

    def cache_train_job(self, train_id):
        """Cache given train job (async)."""
        brief_need_reload = self._brief_cache.cache_train_job(train_id)
        detail_need_reload = self._detail_cache.cache_train_job(train_id)
        if brief_need_reload or detail_need_reload:
            self.reload_data()

    def register_brief_cache_item_updater(self, updater: BaseCacheItemUpdater):
        """Register brief cache item updater for brief cache manager."""
        self._brief_cache.register_cache_item_updater(updater)

    def get_brief_cache(self):
        """Get brief cache."""
        return self._brief_cache

    def get_brief_train_job(self, train_id):
        """Get brief train job."""
        return self._brief_cache.get_train_job(train_id)


DATA_MANAGER = DataManager(settings.SUMMARY_BASE_DIR)
