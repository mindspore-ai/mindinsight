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

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.exceptions.exceptions import NotFoundParallelStrategyDataException
from mindinsight.profiler.common.exceptions.exceptions import WrongParallelStrategyDataException

from .base_analyser import BaseAnalyser
from .graph import GraphManager


class Status(Enum):
    PENDING = 'pending'
    LOADING = 'loading'
    FINISH = 'finish'


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
        self._profiler_dir_mtime = os.path.getmtime(self._profiling_dir)

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
        if getattr(cls._instance, '_profiling_dir') != profiler_dir:
            return True
        if getattr(cls._instance, '_profiler_dir_mtime') != os.path.getmtime(getattr(cls._instance, '_profiling_dir')):
            return True
        return False

    @property
    def data(self):
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

        thread = threading.Thread(target=self._load_data_with_exception)
        thread.start()

    def _load_data_with_exception(self):
        """Wrap load data with try"""
        try:
            self._load_data()
        except Exception as exc:
            self._status = Status.FINISH.value
            logger.exception(exc)
            self._data = dict(
                metadata={},
                graphs=[]
            )

    def _load_data(self):
        """Load data in thread."""
        logger.info("Start to load data, status: %s.", self._status)
        start = time.time()
        self._status = Status.LOADING.value
        path = Path(self._profiling_dir)
        files = sorted(path.rglob("parallel_strategy*.json"))
        if not files:
            logger.error("Can not find any data in path %s", path)
            raise NotFoundParallelStrategyDataException()

        with files[0].open(mode='r') as fp:
            parallel = json.load(fp)
            if 'config' not in parallel or not isinstance(parallel.get('config'), dict):
                raise WrongParallelStrategyDataException("Can not find 'config' key in the given data.")

            parallel_type = parallel['config'].get('parallelType', '')
            stage_devices = parallel['config'].get('stageDevices', [])
            manager = GraphManager(parallel_type, stage_devices)

        threads = []
        for file in files:
            thread = threading.Thread(target=self._load_single_file, args=(file, manager))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        manager.merge_graph()
        self._data = manager.to_dict()
        self._status = Status.FINISH.value
        logger.info('Load data finish, use time: %s.', (time.time() - start))

    def _load_single_file(self, file, manager):
        with file.open(mode='r') as fp:
            parallel = json.load(fp)
            rank_id = str(parallel['config']['rankId'])
            logger.info("Load single file, parallel path %s, config message : %s. rank id: %s.",
                        file, str(parallel['config']), rank_id)
            manager.add_graph(parallel['graph'], rank_id)

    def _filter(self, filter_condition):
        """Inherits from the parent class, but doesn't need to do anything."""
