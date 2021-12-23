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
"""This module is aimed to provide with GraphRuns."""
from collections import defaultdict
from dataclasses import field, dataclass, asdict
from typing import List

from mindinsight.debugger.common.exceptions.exceptions import DebuggerHistoryNotFoundError, \
    DebuggerHistoryValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import Streams, enter_tag


@dataclass
class GraphRun:
    """Graph run data class."""
    count: int = 0
    graph_name: str = 'None'
    has_data: bool = False
    sub_graph_names: List[str] = field(default_factory=list)

    @staticmethod
    def _get_graph_id(graph_name):
        """Get graph id by graph name."""
        graph_id_str = graph_name.rsplit('_', 1)[-1]
        graph_id = int(graph_id_str) if graph_id_str.isdigit() else 0
        return graph_id

    def __lt__(self, other):
        if self.count != other.count:
            return self.count < other.count
        cur_graph_id = self._get_graph_id(self.graph_name)
        other_graph_id = self._get_graph_id(other.graph_name)
        return cur_graph_id < other_graph_id


class GraphRunsOperator:
    """Manage Graph runs information."""

    def __init__(self, cache):
        self._cache = cache
        self._multi_card_graph_stream = cache.get_stream_handler(Streams.GRAPH)
        self._graph_history_stream = cache.get_stream_handler(Streams.GRAPH_HISTORY)

    def get_graph_runs(self, rank_id):
        """
        Get graph runs info of specified rank.

        Args:
            rank_id (int): The rank id.

        Returns:
            dict, the graph runs. The format is like {'graph_runs': List[GraphRun]}
            The GraphRun object = {
                "count": int,
                "graph_name": str,
                "has_data": bool,
                "sub_graph_names": List[str]
            }
        """
        graph_history = self._graph_history_stream.get(rank_id)
        graph_run_count = graph_history.get_total_count()
        if not graph_run_count:
            log.warning("No graph runs found.")
            return {'graph_runs': []}
        graph_run_map = self.get_basic_graph_runs(rank_id)
        graph_run_map = self.update_has_data_field(graph_run_map, rank_id)
        res = self.get_sorted_graph_runs(graph_run_map)
        return {'graph_runs': res}

    @enter_tag
    def get_basic_graph_runs(self, rank_id):
        """
        Get basic graph runs.

        Args:
            rank_id (int): The rank id.

        Returns:
            dict, the key is count id, the value is dict of <root_graph_id, GraphRun>.
        """
        graph_history = self._graph_history_stream.get(rank_id)
        root_graphs = self._multi_card_graph_stream.get_graph_handler_by_rank_id(rank_id).root_graphs
        graph_run_map = defaultdict(dict)
        for root_graph_id, graph_run_ids in graph_history.history.items():
            root_graph = root_graphs.get(root_graph_id)
            if root_graph is None:
                log.error("Didn't find relative graph info of graph %s. "
                          "Please check the dump structure.", root_graph_id)
                raise DebuggerHistoryNotFoundError(root_graph_id)
            for graph_run_id in graph_run_ids:
                graph_run = GraphRun(count=graph_run_id + 1,
                                     graph_name=root_graph.graph_name,
                                     sub_graph_names=root_graph.sub_graph_names)
                graph_run_map[graph_run_id][root_graph_id] = graph_run
        return graph_run_map

    def update_has_data_field(self, graph_run_map, rank_id):
        """Update has_data field in GraphRun."""
        dumped_steps = self._graph_history_stream.get_dumped_step(rank_id)
        for root_graph_id, dumped_steps in dumped_steps.items():
            for step_id in dumped_steps:
                graph_run = graph_run_map.get(step_id, {}).get(root_graph_id)
                if graph_run is None:
                    log.error("Didn't find step_id %s in graph history of rank %s", step_id, rank_id)
                    raise DebuggerHistoryValueError(root_graph_id)
                graph_run.has_data = True
        return graph_run_map

    @staticmethod
    def get_sorted_graph_runs(graph_run_map):
        """Turn graph run map into ordered list."""
        graph_runs = []
        for graph_runs_per_step in graph_run_map.values():
            for graph_run in graph_runs_per_step.values():
                graph_runs.append(graph_run)
        graph_runs.sort()
        graph_runs = [asdict(graph_run) for graph_run in graph_runs]
        return graph_runs
