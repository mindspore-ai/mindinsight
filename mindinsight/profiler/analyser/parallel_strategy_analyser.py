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

from pathlib import Path

from mindinsight.datavisual.proto_files.mindinsight_profiling_parallel_pb2 import ProfilingParallel

from .base_analyser import BaseAnalyser
from .graph import GraphManager


class ParallelStrategyAnalyser(BaseAnalyser):
    """The analyser for parallel strategy."""

    def _load(self):
        """Load data according to the parsed profiling files."""
        path = Path(self._profiling_dir)
        manager = None
        # TODO use multi thread or multi process to handle the pb file.
        for file in sorted(path.rglob("parallel_strategy*.pb")):
            with file.open(mode='rb') as fp:
                parallel = ProfilingParallel()
                parallel.ParseFromString(fp.read())

                if manager is None:
                    parallel_type = parallel.config.parallel_type
                    stage_devices = parallel.config.stage_devices
                    manager = GraphManager(parallel_type, stage_devices)

                manager.add_graph(parallel.graph, parallel.config.rank_id)

        manager.merge_graph()
        self._data = manager.to_dict()

    def _filter(self, filter_condition):
        """Inherits from the parent class, but doesn't need to do anything."""
