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
"""This file is used to define the GraphHistory."""
from mindinsight.debugger.common.log import LOGGER as log


class GraphHistory:
    """Graph history of a device."""

    def __init__(self, rank_id, graph_history):
        self._rank_id = rank_id
        # the key is graph id, the value is list of executed graph run id.
        self._graph_history = graph_history
        self._count = None

    @property
    def rank_id(self):
        """Return rank id."""
        return self._rank_id

    @property
    def history(self):
        """Return execution history of all graphs."""
        return self._graph_history

    def clear(self):
        """Clear Graph History."""
        self._graph_history = {}
        self._count = 0

    def get_total_count(self):
        """Get the last graph run id."""
        if self._count is not None:
            return self._count
        last_id = -1
        for history in self._graph_history.values():
            if not history:
                continue
            last_id = last_id if last_id > history[-1] else history[-1]
        self._count = last_id + 1
        self._check_history()
        return self._count

    def _check_history(self):
        """Check history."""
        expect_count = self._count
        total_count = 0
        for history in self._graph_history.values():
            total_count += len(history)
        if total_count != expect_count:
            msg = f"The graph history is missing graph runs. " \
                  f"The total count is {total_count}/{expect_count}"
            log.warning(msg)

    def get_run_ids(self, graph_id):
        """
        Get executed graph run ids.

        Args:
            graph_id (int): The root graph id.

        Returns:
            list[int], the list of graph run ids.
        """
        return self._graph_history.get(graph_id, [])
