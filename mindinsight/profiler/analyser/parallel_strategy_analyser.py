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
import json
import time
import threading
from pathlib import Path
from enum import Enum
from collections import namedtuple
from multiprocessing import Pool

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.exceptions.exceptions import NotFoundParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import WrongParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import ParseParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import UnsupportedParallelTypeException
from mindinsight.utils.exceptions import MindInsightException

from .base_analyser import BaseAnalyser
from .graph import GraphManager, Graph, SupportedParallelType


class Status(Enum):
    PENDING = 'pending'
    LOADING = 'loading'
    FINISH = 'finish'


FileData = namedtuple('FileData', ['graph_proto', 'rank_id'])
STRATEGY_FILE_PATTERN = "parallel_strategy*.json"


class ParallelStrategyAnalyser(BaseAnalyser):
    """The analyser for parallel strategy."""

    _instance = None
    _lock = threading.Lock()
    _should_init = None

    def __init__(self, *args, **kwargs):
        if not self._should_init:
            return

        self._status = Status.PENDING.value
        super(ParallelStrategyAnalyser, self).__init__(*args, **kwargs)
        self._profiler_dir_mtime = self._get_strategy_file_mtime(self._profiling_dir)
        self._exception = None

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
        strategy_files = sorted(path.rglob(STRATEGY_FILE_PATTERN), key=lambda file: os.path.getmtime(file))
        if strategy_files:
            file_path = os.path.join(profiling_dir, strategy_files[-1])
            return os.path.getmtime(file_path)
        return -1

    @property
    def data(self):
        if self._exception is not None:
            raise self._exception

        if self._status == Status.FINISH.value:
            response = {'status': self._status}
            response.update(self._data)
            if not response.get('graphs'):
                raise WrongParallelStrategyDataException("Can not find any data or load data failed.")
            return response

        response = dict(
            metadata={},
            graphs=[],
            status=self._status
        )
        return response

    def _load(self):
        """Load data according to the parsed profiling files."""
        if self._status in (Status.LOADING.value, Status.FINISH.value):
            return

        thread = threading.Thread(target=self._load_data_with_catch_exception, name='parallel_strategy_analyser')
        thread.start()

    def _load_data_with_catch_exception(self):
        """Wrap load data with try"""
        start = time.time()
        try:
            # Consider processing data from up to 8 cards at a time
            with Pool(processes=8) as pool:
                self._load_data(pool)
        except MindInsightException as exc:
            self._exception = exc
        except Exception as exc:
            self._exception = ParseParallelStrategyDataException(str(exc))
            logger.exception("Load parallel strategy data failed, detail: %s.", str(exc))
        finally:
            self._status = Status.FINISH.value
            logger.info("Load data from %s use time: %s", self._profiling_dir, (time.time()-start))

    def _load_data(self, pool):
        """Load data in thread."""
        logger.info("Start to load data, status: %s.", self._status)
        self._status = Status.LOADING.value
        path = Path(self._profiling_dir)
        files = sorted(path.rglob(STRATEGY_FILE_PATTERN),
                       key=lambda filepath: int(filepath.name.split('.')[0].split('_')[-1]))
        if not files:
            logger.error("Can not find any data in path %s", path.name)
            raise NotFoundParallelStrategyDataException()

        manager = None
        file_data_dict = {}
        parallels = []
        for parallel, exc in pool.imap(self._load_file, files):
            if exc:
                raise exc
            parallels.append(parallel)

        for parallel in parallels:
            if 'config' not in parallel or not isinstance(parallel.get('config'), dict):
                raise WrongParallelStrategyDataException("Can not find 'config' key in the given data.")

            parallel_type = parallel['config'].get('parallelType', '')
            if parallel_type not in SupportedParallelType.list_members():
                raise UnsupportedParallelTypeException(f"Only support {SupportedParallelType.list_members()} "
                                                       f"parallel type, but current parallel type is {parallel_type}.")

            if manager is None:
                stage_devices = parallel['config'].get('stageDevices', [])
                manager = GraphManager(parallel_type, stage_devices)

            rank_id = str(parallel['config']['rankId'])
            if rank_id in file_data_dict:
                raise WrongParallelStrategyDataException(f"The file with the same rank id was found. "
                                                         f"There should be no file names with the same rank id.")

            file_data_dict[rank_id] = FileData(graph_proto=parallel['graph'], rank_id=rank_id)

            if parallel_type == SupportedParallelType.DATA_PARALLEL.value:
                break

        for graph, rank_id, exc in pool.imap(self._build_graph, file_data_dict.values()):
            if exc is not None:
                raise exc

            manager.add_graph(graph, rank_id)

        manager.merge_graph()
        self._data = manager.to_dict()
        self._status = Status.FINISH.value

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
            return None, WrongParallelStrategyDataException("The file is not a valid json file.")

    @staticmethod
    def _build_graph(file_data):
        """This function is used for multiprocessing to build graph."""
        graph = Graph()
        try:
            graph.build_graph(graph_proto=file_data.graph_proto, rank_id=file_data.rank_id)
        except Exception as exc:
            return graph, file_data.rank_id, exc
        return graph, file_data.rank_id, None

    def _filter(self, filter_condition):
        """Inherits from the parent class, but doesn't need to do anything."""
