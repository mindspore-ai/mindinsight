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
# ==============================================================================
"""Debugger python API."""

from typing import Iterable

from mindinsight.debugger.api.conditions import WatchpointHit
from mindinsight.debugger.api.debugger_tensor import DebuggerTensor
from mindinsight.debugger.api.node import Node


class DumpAnalyzer:
    """
    Analyzer to inspect the dump data.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change and/or deletion.

    Args:
        summary_dir (str): The path of the summary directory which contains
            dump folder.
        mem_limit (int, optional): The memory limit for this debugger session in
            MB. Default: None, which means no limit.
    """

    def __init__(self, summary_dir, mem_limit=None):
        self._summary_dir = summary_dir
        self._mem_limit = mem_limit

    def export_graphs(self, output_dir=None):
        """
        Export the computational graph(s) in xlsx file(s) to the output_dir.

        The file(s) will contain the stack info of graph nodes.

        Args:
            output_dir (str, optional): Output directory to save the file.
                Default: None, which means to use the current working directory.

        Returns:
            str. The path of the generated file.
        """

    def select_nodes(
            self,
            query_string,
            use_regex=False,
            select_by="node_name",
            ranks=None,
            case_sensitive=True) -> Iterable[Node]:
        """
        Select nodes.

        Select the matched nodes in the computational graph according to the
        query_string. The nodes can be matched by "node_name" or "code_stack",
        see the args document for detail.

        Args:
            query_string (str): Query string. For a node to be selected, the
                match target field must contains or matches the query string.
            use_regex (bool): Indicates whether query is a regex. Default:
                False.
            select_by (str, optional): The field to search when selecting
                nodes. Available values are "node_name", "code_stack".
                "node_name" means to search the name of the nodes in the
                graph. "code_stack" means the stack info of
                the node. Default: "node_name".
            ranks (list(int], optional): The ranks to select. The selected
                nodes must exist on the specified ranks. Default: None,
                which means all ranks will be considered.
            case_sensitive (bool, optional): Whether case-sensitive when
                selecting tensors. Default: True.

        Returns:
            Iterable[Node], the matched nodes.
        """

    def select_tensors(
            self,
            query_string,
            use_regex=False,
            select_by="node_name",
            iterations=None,
            ranks=None,
            slots=None,
            case_sensitive=True) -> Iterable[DebuggerTensor]:
        """
        Select tensors.

        Select the matched tensors in the directory according to the
        query_string. The tensors can be matched by "node_name" or
        "code_stack", see the args document for detail.

        Args:
            query_string (str): Query string. For a tensor to be selected, the
                match target field must contains or matches the query string.
            use_regex (bool): Indicates whether query is a regex. Default:
                False.
            select_by (str, optional): The field to search when selecting
                tensors. Available values are "node_name", "code_stack".
                "node_name" means to search the node name of the tensors in the
                graph. "code_stack" means the stack info of
                the node that outputs this tensor. Default: "node_name".
            iterations (list[int], optional): The iterations to select. Default:
                None, which means all iterations will be selected.
            ranks (list(int], optional): The ranks to select. Default: None,
                which means all ranks will be selected.
            slots (list[int], optional): The slot of the selected tensor.
                Default: None, which means all slots will be selected.
            case_sensitive (bool, optional): Whether case-sensitive when
                selecting tensors. Default: True.

        Returns:
          Iterable[DebuggerTensor], the matched tensors.
        """

    def get_iterations(self) -> Iterable[int]:
        """Get the available iterations this run."""

    def get_ranks(self) -> Iterable[int]:
        """Get the available ranks in this run."""

    def check_watchpoints(
            self,
            watchpoints,
            error_on_no_value=False) -> Iterable[WatchpointHit]:
        """
        Check the given watch points on specified nodes(if available) on the
        given iterations(if available) in a batch.

        Note:
            For speed, all watchpoints for the iteration should be given at
            the same time to avoid reading tensors len(watchpoints) times.

        Args:
            watchpoints (Iterable[Watchpoint]): The list of watchpoints.
            error_on_no_value (bool): Whether report error code in watchpoint
                hit when the specified tensor have no value stored in
                summary_dir. Default: False.

        Returns:
            Iterable[WatchpointHit], the watchpoint hist list is carefully
            sorted so that the user can see the most import hit on the top of
            the list. When there are many many watchpoint hits, we will
            display the list in a designed clear way.
        """

    def list_affected_nodes(self, tensor):
        """
        List the nodes that use given tensor as input.

        Affected nodes is defined as the nodes use the given tensor as input. If
        a node is affected by the given tensor, the node's output value is
        likely to change when the given tensor changes.

        Args:
            tensor (DebuggerTensor): The tensor of which affected nodes will be
                returned.

        Returns:
            Iterable[Node], the affected nodes of the given tensor.
        """

    def get_input_nodes(self, node):
        """
        Get the input nodes of the given node.

        Args:
            node (Node): The node of which input nodes will be returned.

        Returns:
            Iterable[Node], the input nodes of the given node.
        """

    def get_output_nodes(self, node):
        """
        Get the nodes that use the output tensors of the given node.

        Args:
            node (Node): The node of which output nodes will be returned.

        Returns:
            Iterable[Node], the output nodes of this node.
        """
