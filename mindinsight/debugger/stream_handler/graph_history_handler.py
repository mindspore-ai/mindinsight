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
"""Define the GraphHistory stream handler."""
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import enter_tag
from mindinsight.debugger.stream_cache.graph_history import GraphHistory
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class GraphHistoryHandler(StreamHandlerBase):
    """GraphHistory Handler."""

    def __init__(self):
        # the key is rank id, the value is GraphHistory
        self._history = {}
        # the key is rank id, the value is like Dict[<graph_id>, List[<step_id>]]
        self._dumped_step = {}

    def put(self, value):
        """
        Put graph history into cache.

        Args:
            value (dict): The key is the rank id, the value is like {<graph_id>: list[<step_id>]}.
        """
        for rank_id, graph_history in value.items():
            self._history[rank_id] = GraphHistory(rank_id, graph_history)

    def put_dumped_step(self, dumped_step):
        """
        Put dumped step info.

        Args:
            dumped_step (dict): The key is rank id, the
                value is like Dict[<graph_id>, List[<step_id>]].
        """
        self._check_dumped_step(dumped_step)
        self._dumped_step = dumped_step

    @enter_tag
    def _check_dumped_step(self, dumped_step):
        """Check if all dumped step in is graph history."""
        def _matched(dumped_steps, run_history):
            diff_set = dumped_steps - run_history
            if not diff_set:
                return True
            if len(diff_set) != 1:
                return False
            # check if it is a data sink exception case
            max_step_id = max(dumped_steps)
            if max_step_id in diff_set and (max_step_id - 1) in run_history:
                msg = f"The dumped iteration {max_step_id} is not expected. It may be normal if " \
                          f"the data is dumped in dataset sink mode and there is only AssignAdd operator " \
                          f"in that directory. Otherwise, the dump structure is not correct."
                log.warning(msg)
                dumped_steps.remove(max_step_id)
                return True
            return False

        for rank_id, value in dumped_step.items():
            graph_history = self.get(rank_id)
            is_matched = True
            for root_graph_id, dumped_steps_per_graph in value.items():
                whole_run_ids = graph_history.get_run_ids(root_graph_id)
                if not whole_run_ids:
                    # in case there is no graph history file
                    log.warning("Graph History file of %s in rank_%s is empty.", root_graph_id, rank_id)
                    continue
                is_matched = is_matched and _matched(dumped_steps_per_graph, whole_run_ids)
                if not is_matched:
                    log.warning("Dumped step value of graph %s in rank_%s mismatch the graph history. "
                                "Clear the history graph.", root_graph_id, rank_id)
                    graph_history.clear()

    def get(self, filter_condition=None):
        """
        Get GraphHistory of specified rank id.

        Args:
            filter_condition (int): The rank id.

        Returns:
            GraphHistory, the GraphHistory.
        """
        rank_id = filter_condition
        if rank_id not in self._history:
            log.error("Invalid rank id. Failed to find graph history with rank id %s", rank_id)
            raise DebuggerParamValueError("Invalid rank_id.")
        return self._history.get(rank_id)

    def get_dumped_step(self, rank_id):
        """
        Get dumped step info of specified device.

        Args:
            rank_id (int): The rank id.

        Returns:
            dict, the key is graph id, the value is the list of dumped steps.
        """
        if rank_id not in self._dumped_step:
            log.error("Invalid rank id. Failed to find dumped steps with rank id %s", rank_id)
            raise DebuggerParamValueError("Invalid rank_id.")
        return self._dumped_step.get(rank_id)

    def get_total_count(self):
        """
        Get total count per device.

        Returns:
            dict, the key is rank id, the value is the total count of each device.
        """
        total_count = {}
        for rank_id, graph_history in self._history.items():
            total_count_per_rank = graph_history.get_total_count()
            if not total_count_per_rank:
                log.warning("Failed to get total graph run count from graph history of rank_%s. "
                            "Try to get it based on dumped iterations.", rank_id)
                total_count_per_rank = self._get_max_dumped_step_id(rank_id)
            total_count[rank_id] = total_count_per_rank
        return total_count

    def _get_max_dumped_step_id(self, rank_id):
        """Get the maximum step id of specified device."""
        max_step_id = -1
        for dumped_step_per_graph in self._dumped_step.get(rank_id, {}).values():
            if not dumped_step_per_graph:
                continue
            max_step_id = max(max_step_id, max(dumped_step_per_graph))
        return max_step_id + 1
