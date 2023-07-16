# Copyright 2021 Huawei Technologies Co., Ltd
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
"""The ParallelStrategyAnalyser analyser class."""
import os
import stat
import json
import time
import threading
from pathlib import Path
from enum import Enum
from collections import defaultdict, namedtuple
from multiprocessing import Pool
from marshmallow import ValidationError

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.exceptions.exceptions import NotFoundParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import WrongParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import ParseParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import UnsupportedParallelTypeException
from mindinsight.profiler.common.exceptions.exceptions import FileNumNotMatchException
from mindinsight.profiler.common.exceptions.exceptions import ProfilerPathErrorException
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.util import get_parallel_message

from .graph import GraphManager, Graph, SupportedParallelType


class Status(Enum):
    PENDING = 'pending'
    LOADING = 'loading'
    FINISH = 'finish'


FileData = namedtuple('FileData', ['graph_proto', 'rank_id'])
STRATEGY_FILE_PATTERN = "parallel_strategy*.json"


class ParallelStrategyCache:
    """Cache the ParallelStrategy Data"""
    _paraller_data = defaultdict(dict)
    _lock = threading.Lock()
    _graph_file = "/graph_{}"

    @classmethod
    def set_cache(cls, key, data, profiler_dir, save=False):
        """cache parallel data"""
        try:
            with cls._lock:
                cls._paraller_data[profiler_dir].update({key: data})
            if save:
                sub_graph_path = profiler_dir + cls._graph_file.format(key)
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                modes = stat.S_IWGRP | stat.S_IWOTH | stat.S_IWUSR
                with os.fdopen(os.open(sub_graph_path, flags, modes), "w") as fw:
                    json.dump(data, fw)
        except FileExistsError as exc:
            logger.warning("Cache parallel strategy data failed, detail: %s.", str(exc))
        except Exception as exc:
            logger.exception("Cache parallel strategy data failed, detail: %s.", str(exc))

    @classmethod
    def get_cache(cls, key, profiler_dir):
        """get cached parallel data"""
        try:
            res_data = cls._paraller_data.get(profiler_dir, {}).get(key, {})
            sub_graph_path = profiler_dir + cls._graph_file.format(key)
            if not res_data and os.path.exists(sub_graph_path):
                logger.warning("get data from l2 cache")
                with open(sub_graph_path, 'r') as fr:
                    res_data = json.load(fr)
                thread = threading.Thread(target=cls.set_cache, args=(key, res_data, profiler_dir))
                thread.start()
            elif res_data:
                logger.warning("get data from l1 cache")
                if not os.path.exists(sub_graph_path):
                    thread = threading.Thread(target=cls.set_cache, args=(key, res_data, profiler_dir, True))
                    thread.start()
            else:
                logger.warning("data not cached")
            return res_data

        except Exception as exc:
            logger.exception("Get cached parallel strategy data failed, detail: %s.", str(exc))
            return {}


class ParallelStrategyAnalyser:
    """The analyser for parallel strategy."""

    _instance = None
    _lock = threading.Lock()
    _should_init = None

    def __new__(cls, *args):
        """Create a new object."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    setattr(cls._instance, '_should_init', True)
                return cls._instance

        with cls._lock:
            if cls._is_create_new_instance(args[0]):
                cls._instance = super().__new__(cls)
                setattr(cls._instance, '_should_init', True)
                return cls._instance

        setattr(cls._instance, '_should_init', False)
        return cls._instance

    def __init__(self, profiler_dir):
        if not self._should_init:
            return
        self._status = {}
        self._data = {}
        self._profiling_dir = self._normalize_profiling_dir(profiler_dir)
        self._profiler_dir_mtime = self._get_strategy_file_mtime(self._profiling_dir)
        self._exception = None

        parallel_message = get_parallel_message(self._profiling_dir)
        self.parallel_type = parallel_message.get('parallel_mode')
        self.stage_num = parallel_message.get('stage_num')
        self.rank_size = parallel_message.get('rank_size')
        self.group_num = self.rank_size // self.stage_num
        self.stage_devices = {}
        for stage_id in range(self.stage_num):
            self._status.update({stage_id: Status.PENDING.value})
            start = stage_id * self.group_num
            end = start + self.group_num
            self.stage_devices[stage_id] = list(range(start, end))
        self._status.update({'metadata': Status.FINISH.value})
        self.set_data('metadata', {'parallel_type': self.parallel_type, 'stage_devices': self.stage_devices})

        path = Path(self._profiling_dir)
        self.files = sorted(path.glob(STRATEGY_FILE_PATTERN),
                            key=lambda filepath: int(filepath.name.split('.')[0].split('_')[-1]))
        if not self.files:
            logger.error("Can not find any data in path %s", path.name)
            raise NotFoundParallelStrategyDataException()
        if len(self.files) != self.rank_size:
            logger.error("The num of parallel data is not %s , in path %s", str(self.rank_size), path.name)
            raise FileNumNotMatchException()

        if self.parallel_type not in SupportedParallelType.list_members():
            raise UnsupportedParallelTypeException(f"Only support {SupportedParallelType.list_members()} "
                                                   f"parallel type, but current parallel type is {self.parallel_type}.")

    @classmethod
    def _is_create_new_instance(cls, profiler_dir):
        """Determine whether to create a new instance object."""
        # Note: This could be due to multithreading. As a result, instance has not been initialized successfully
        if getattr(cls._instance, '_profiling_dir', None) is None:
            return False
        if getattr(cls._instance, '_profiling_dir') != profiler_dir:
            return True
        if getattr(cls._instance, '_profiler_dir_mtime') != cls._get_strategy_file_mtime(profiler_dir):
            return True
        return False

    @staticmethod
    def _get_strategy_file_mtime(profiling_dir):
        """Get strategy file mtime from profiling dir."""
        path = Path(profiling_dir)
        strategy_files = sorted(path.glob(STRATEGY_FILE_PATTERN), key=lambda file: os.path.getmtime(file))
        if strategy_files:
            file_path = os.path.join(profiling_dir, strategy_files[-1])
            return os.path.getmtime(file_path)
        return -1

    @staticmethod
    def _build_graph(file_data):
        """This function is used for multiprocessing to build graph."""
        graph = Graph()
        try:
            graph.build_graph(graph_proto=file_data.graph_proto, rank_id=file_data.rank_id)
        except Exception as exc:
            return graph, file_data.rank_id, exc
        return graph, file_data.rank_id, None

    @staticmethod
    def _load_file(file: Path):
        """Load data from one file."""
        try:
            with file.open('r') as fp:
                parallel = json.load(fp)
                return parallel, None
        except OSError as exc:
            return None, exc
        except json.JSONDecodeError:
            return None, WrongParallelStrategyDataException(f"The file is not a valid json file: {file.name}.")

    @staticmethod
    def _normalize_profiling_dir(profiling_dir):
        """Normalize the profiling dir."""
        try:
            return validate_and_normalize_path(profiling_dir, 'profiler')
        except ValidationError:
            raise ProfilerPathErrorException('The profiling dir is invalid.')

    def set_data(self, stage_id, data):
        self._data[stage_id] = data
        thread = threading.Thread(target=ParallelStrategyCache.set_cache,
                                  args=(stage_id, data, self._profiling_dir, True))
        thread.start()

    def get_data(self, stage_id):
        """Get the one of stages data."""

        if self._exception is not None:
            raise self._exception

        response = {'status': self._status.get(stage_id), 'data': {}}
        if self._status.get(stage_id) == Status.FINISH.value:
            data = self._data.get(stage_id, {})
            if not data:
                raise WrongParallelStrategyDataException("Can not find any data or load data failed.")
            response.update({'data': data})
        return response

    def load_by_stage_id(self, stage_id):
        """Load the parallel data by stage_id"""
        if self._status.get(stage_id) in (Status.LOADING.value, Status.FINISH.value):
            return
        thread = threading.Thread(target=self._load_data_with_catch_exception,
                                  args=(stage_id, self.stage_devices.get(stage_id)))
        thread.start()

    def _load_data_with_catch_exception(self, stage_id, stage_devices):
        """Wrap load data with try"""
        start = time.time()
        self._status[stage_id] = Status.LOADING.value
        logger.info('Start to load data, status: %s.', self._status.get(stage_id))
        try:
            # Consider processing data from up to 8 cards at a time
            with Pool(processes=8) as pool:
                self._load_data(pool, stage_id, stage_devices)
        except MindInsightException as exc:
            self._exception = exc
        except Exception as exc:
            self._exception = ParseParallelStrategyDataException(str(exc))
            logger.exception("Load parallel strategy data failed, detail: %s.", str(exc))
        finally:
            self._status[stage_id] = Status.FINISH.value
            logger.info("Load data from %s use time: %s", self._profiling_dir, (time.time() - start))

    def _load_data(self, pool, stage_id, stage_devices):
        """Load data in thread."""
        start = stage_id * self.group_num
        end = start + self.group_num
        files = self.files[start: end]

        file_data_dict = {}
        for parallel, exc in pool.imap(self._load_file, files):
            if exc:
                raise exc

            if 'config' not in parallel or not isinstance(parallel.get('config'), dict):
                raise WrongParallelStrategyDataException("Can not find 'config' key in the given data.")

            rank_id = parallel['config']['rankId']
            if rank_id in file_data_dict:
                raise WrongParallelStrategyDataException(f"The file with the same rank id was found. "
                                                         f"There should be no file names with the same rank id.")

            file_data_dict[rank_id] = FileData(graph_proto=parallel['graph'], rank_id=rank_id)

        graph_manager = GraphManager(self.parallel_type, stage_id, stage_devices)
        for graph, rank_id, exc in pool.imap(self._build_graph, file_data_dict.values()):
            if exc:
                raise exc
            graph_manager.add_graph(graph, rank_id)

        graph_manager.merge_graph()
        self.set_data(stage_id, graph_manager.to_dict())
        self._status[stage_id] = Status.FINISH.value
