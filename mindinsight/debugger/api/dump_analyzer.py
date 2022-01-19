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
import os.path
from typing import Iterable

from mindinsight.debugger.api.conditions import WatchpointHit, HitDetail, WatchpointHandle, WatchpointHitImpl
from mindinsight.debugger.api.debugger_engine import DebuggerEngine
from mindinsight.debugger.api.debugger_tensor import DebuggerTensor, DebuggerTensorImpl
from mindinsight.debugger.api.node import Node, NodeImpl, NodeUniqueId
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import (
    validate_type, validate_slots, parse_param_to_iterable_obj
)
from mindinsight.debugger.dump.parser import DebuggerParser
from mindinsight.debugger.stream_cache.data_loader import DataLoader
from mindinsight.domain.graph.base import NodeType
from mindinsight.domain.graph.query import construct_filter_func


class DumpAnalyzer:
    """
    Analyzer to inspect the dump data.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        dump_dir (str): The path of the dump folder.
        mem_limit (int, optional): The memory limit for checking watchpoints in MB.
            Default: None, which means no limit. Optional values: from 2048 MB to 2147483647 MB.

    Examples:
            >>> from mindinsight.debugger import DumpAnalyzer
            >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
    """

    def __init__(self, dump_dir, mem_limit=None):
        self._dump_dir = os.path.realpath(dump_dir)
        self._mem_limit = 0 if mem_limit is None else mem_limit
        self._data_loader = None
        self._debuger_engine = None
        self._parser = None
        # the key is rank_id, the value is <tensor_feature, TensorImpl> map
        self._nodes = {}
        self._initialize()

    def _initialize(self):
        """Initialize."""
        self._validate_mem_limit(self._mem_limit)
        self._data_loader = DataLoader(self._dump_dir)
        self._debugger_engine = DebuggerEngine(self._data_loader, self._mem_limit)
        self._parse()

    @staticmethod
    def _validate_mem_limit(mem_limit):
        """Validate memory limit."""
        validate_type(mem_limit, 'mem_limit', int, 'int or None')
        # The unit is MB, from 2G to max value of int32 MB
        min_limit_value = 2 * 1024
        max_limit_value = 2147483647
        if mem_limit and mem_limit < min_limit_value or mem_limit > max_limit_value:
            msg = f"If mem_limit is not None, it should be set in [{min_limit_value}, {max_limit_value}]."
            raise DebuggerParamValueError(msg)

    def _parse(self):
        """Parse graph into nodes and tensors."""

        def _add_node_impl(base_nodes, node_type, nodes):
            nonlocal id_to_name_map
            for b_node in base_nodes:
                new_node = NodeImpl(b_node, node_type)
                new_node.debugger_engine = self._debugger_engine
                nodes[new_node.rank][new_node.unique_id] = new_node
                id_to_name_map[new_node.rank][(b_node.graph_name, b_node.name)] = new_node.name

        def _update_node_list(node_list, dst_id, cur_node, cur_node_map):
            nonlocal id_to_name_map
            dst_node_name = id_to_name_map[cur_node.rank].get(dst_id)
            if not dst_node_name:
                log.info("Failed to find %s in id_to_name_map", dst_id)
                return
            unique_id = NodeUniqueId(name=dst_node_name,
                                     rank=cur_node.rank, graph_name=cur_node.graph_name)
            target_node = cur_node_map.get(unique_id)
            if not target_node:
                log.error("Failed to find %s in node_map", unique_id)
                return
            node_list.append(target_node)

        self._parser = DebuggerParser(self._data_loader)
        ranks = self.get_ranks()
        # the key is rank_id, the value is <node_unique_id, NodeImpl> map
        self._nodes = {rank_id: {} for rank_id in ranks}
        id_to_name_map = {rank_id: {} for rank_id in ranks}
        _add_node_impl(self._parser.constants, NodeType.CONSTANT, self._nodes)
        _add_node_impl(self._parser.parameters, NodeType.PARAMETER, self._nodes)
        _add_node_impl(self._parser.operators, NodeType.OPERATOR, self._nodes)
        # update input and output nodes
        for node_map in self._nodes.values():
            for node in node_map.values():
                base_node = node.base_node
                if hasattr(base_node, 'inputs'):
                    # parameter or const node has no inputs
                    for node_input in base_node.inputs:
                        _update_node_list(node.input_nodes, (base_node.graph_name, node_input.name), node, node_map)

        for node_map in self._nodes.values():
            for node in node_map.values():
                for node_input in node.input_nodes:
                    node_input.downstream.append(node)

    def export_graphs(self, output_dir=None):
        """
        Export the computational graph(s) in xlsx file(s) to the output_dir.

        The file(s) will contain the stack info of graph nodes.

        Args:
            output_dir (str, optional): Output directory to save the file.
                Default: None, which means to use the current working directory.

        Returns:
            str, The path of the generated file.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> my_run.export_graphs()
        """
        return self._parser.export_xlsx(output_dir)

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
            ranks (Union[int, list[int], None], optional): The ranks to select.
                The selected nodes must exist on the specified ranks. Default: None,
                which means all ranks will be considered.
            case_sensitive (bool, optional): Whether case-sensitive when
                selecting tensors. Default: True.

        Returns:
            Iterable[Node], the matched nodes.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> nodes = my_run.select_nodes("Conv2D-op13")
        """
        validate_type(query_string, 'query_string', str, 'str')
        validate_type(use_regex, 'use_regex', bool, 'bool')
        validate_type(case_sensitive, 'case_sensitive', bool, 'bool')
        node_filter_func = self._get_filter_func(select_by)
        ranks = self._get_iterable_ranks(ranks)

        query_filter_func = construct_filter_func(query_string, case_sensitive, use_regex)
        nodes = []
        for rank_id in ranks:
            for node in self._nodes.get(rank_id, {}).values():
                if node_filter_func(node, query_filter_func):
                    nodes.append(node.copy())
        return nodes

    @staticmethod
    def _match_name(node, filter_func):
        """Check if name matched."""
        return filter_func(node.name)

    @staticmethod
    def _match_stack(node, filter_func):
        """Check if stack matched."""
        for res in map(filter_func, node.stack):
            if res:
                return True
        return False

    @staticmethod
    def _get_filter_func(select_by):
        """Get filter function."""
        if select_by == 'node_name':
            return DumpAnalyzer._match_name
        if select_by == 'code_stack':
            return DumpAnalyzer._match_stack
        raise DebuggerParamValueError(
            "The param `select_by` only support `node_name` or `code_stack`.")

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
            iterations (Union[int, list[int], None], optional): The iterations to select. Default:
                None, which means all dumped iterations will be selected.
            ranks (Union[int, list[int], None], optional): The ranks to select. Default: None,
                which means all ranks will be selected.
            slots (list[int], optional): The slot of the selected tensor.
                Default: None, which means all slots will be selected.
            case_sensitive (bool, optional): Whether case-sensitive when
                selecting tensors. Default: True.

        Returns:
          Iterable[DebuggerTensor], the matched tensors.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = my_run.select_tensors("Conv2D-op13")
        """
        validate_type(query_string, 'query_string', str, 'str')
        validate_type(use_regex, 'use_regex', bool, 'bool')
        validate_type(case_sensitive, 'case_sensitive', bool, 'bool')
        validate_slots(slots)
        node_filter_func = self._get_filter_func(select_by)
        ranks = self._get_iterable_ranks(ranks)
        dumped_iterations = self.get_iterations(ranks)
        iterations = parse_param_to_iterable_obj(iterations, 'iterations', dumped_iterations)

        tensors = []
        query_filter_func = construct_filter_func(query_string, case_sensitive, use_regex)
        for rank_id in ranks:
            for node in self._nodes.get(rank_id, {}).values():
                if node_filter_func(node, query_filter_func):
                    tensors.extend(node.get_output_tensors(slots=slots, iterations=iterations))
        return tensors

    def get_iterations(self, ranks=None) -> Iterable[int]:
        """
        Get available iterations which have data dumped in this run.

        Args:
            ranks (Union[int, list[int], None], optional): The ranks to select.
                Get available iterations which are under the specified ranks.
                If None, return iterations of all ranks. Default: None.

        Returns:
            Iterable[int], sorted dumped iteration list.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> iterations = my_run.get_iterations()
                >>> print(list(iterations))
                [0]
        """
        total_dumped_steps = self._data_loader.load_dumped_step()
        ranks = self._get_iterable_ranks(ranks)
        iterations = set()
        for rank_id in ranks:
            for iters_per_graph in total_dumped_steps.get(rank_id, {}).values():
                iterations.update(iters_per_graph)
        res = list(iterations)
        res.sort()
        return res

    def get_ranks(self) -> Iterable[int]:
        """
        Get the available ranks in this run.

        Returns:
            Iterable[int], the list of rank id in current dump directory.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> ranks = my_run.get_ranks()
                >>> print(list(ranks))
                [0]
        """
        return [rank_dir.rank_id for rank_dir in self._data_loader.rank_dirs]

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


        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> from mindinsight.debugger import (TensorTooLargeCondition,
                ...                                    Watchpoint)
                >>>
                >>> def test_watchpoints():
                >>>     my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>>     tensors = my_run.select_tensors(
                ...                                         query_string="Conv2D-op13",
                ...                                         use_regex=True,
                ...                                         iterations=[0],
                ...                                         ranks=[0],
                ...                                         slots=[0]
                ...                                         )
                >>>     watchpoint = Watchpoint(tensors=tensors,
                ...                             condition=TensorTooLargeCondition(abs_mean_gt=0.0))
                >>>     hit = list(my_run.check_watchpoints(watchpoints=[watchpoint]))[0]
                >>>     print(str(hit))
                >>>
                >>> if __name__ == "__main__":
                >>>     test_watchpoints()
                Watchpoint TensorTooLarge triggered on tensor:
                rank: 0
                graph_name: kernel_graph_0
                node_name: Default/network-WithLossCell/ _backbone-AlexNet/conv2-Conv2d/Conv2D-op13
                slot: 0
                iteration: 0
                Threshold: {'abs_mean_gt': 0.0}
                Hit detail: the setting for watchpoint is abs_mean_gt = 0.0.
                The actual value of the tensor is abs_mean_gt = 0.06583755487478116.
        """
        wp_hit_list = []
        # key is watchpoint_id, value is a dict with iteration as the key and check_nodes as values
        iterations = set()
        wp_handles = {wp_id: WatchpointHandle(wp_id, wp) for wp_id, wp in enumerate(watchpoints)}
        for wp_handle in wp_handles.values():
            iterations.update(wp_handle.get_iterations())
        debugger_backend = self._debugger_engine.dbg_service
        # check all the watchpoint for the iterations
        for iteration in iterations:
            log.info("Check watchpoints for iteration %s", iteration)
            if not self._data_loader.has_data(iteration):
                log.info("No data dumped with iteration id: %s. Ignore checking watchpoint.", iteration)
                continue
            # adding the watchpoint for current iteration
            for wp_handle in wp_handles.values():
                wp_handle.add_watchpoint(iteration, self._debugger_engine)
            # check the watchpoint for current iteration
            # add the hit watchpoints to hit list
            hit_list = debugger_backend.check_watchpoints(
                iteration=iteration, error_on_no_value=error_on_no_value)
            for hit in hit_list:
                # the list of slots for the hit node to report
                # (for the current watchpoint and iteration)
                wp_handle = wp_handles.get(hit.watchpoint_id)
                graph_name, node_name = hit.name.split('/', 1)
                node = self._get_node(node_name, hit.rank_id, graph_name)
                tensor = DebuggerTensorImpl(node=node, slot=hit.slot, iteration=iteration)
                if wp_handle.need_check(tensor):
                    hit_params = hit.parameters
                    hit_detail = HitDetail(hit_params, wp_handle.condition)
                    wp_hit = WatchpointHitImpl(tensor=tensor,
                                               condition=wp_handle.condition,
                                               hit_detail=hit_detail,
                                               error_code=hit.error_code)
                    wp_hit_list.append(wp_hit)
            if error_on_no_value:
                no_value_hit_list = []
                for wp_handle in wp_handles.values():
                    no_value_hit_list += wp_handle.watchpoint_hit_on_no_value(iteration)
                wp_hit_list += no_value_hit_list
            # remove all the watchpoints for the previous iterations
            for watchpoint_id in wp_handles:
                debugger_backend.remove_watchpoint(watchpoint_id=watchpoint_id)

        return wp_hit_list

    def _get_node(self, node_name, rank_id, graph_name):
        """Get NodeImpl object."""
        unique_id = NodeUniqueId(name=node_name, rank=rank_id, graph_name=graph_name)
        node = self._nodes.get(rank_id, {}).get(unique_id)
        return node

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

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensor_list = list(my_run.select_tensors(query_string="Conv2D-op13"))
                >>> affected_nodes = my_run.list_affected_nodes(tensor_list[0])
        """
        self._validate_node(tensor.node)
        affected_nodes = [affected_node.copy() for affected_node in tensor.node.downstream]
        return affected_nodes

    def get_input_nodes(self, node):
        """
        Get the input nodes of the given node.

        Args:
            node (Node): The node of which input nodes will be returned.

        Returns:
            Iterable[Node], the input nodes of the given node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node_list = list(my_run.select_nodes(query_string="Conv2D-op13"))
                >>> input_nodes = my_run.get_input_nodes(node_list[0])
        """
        self._validate_node(node)
        input_nodes = node.input_nodes.copy()
        return input_nodes

    def get_output_nodes(self, node):
        """
        Get the nodes that use the output tensors of the given node.

        Args:
            node (Node): The node of which output nodes will be returned.

        Returns:
            Iterable[Node], the output nodes of this node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node_list = list(my_run.select_nodes(query_string="Conv2D-op13"))
                >>> out_nodes = my_run.get_output_nodes(node_list[0])
        """
        self._validate_node(node)
        output_nodes = node.downstream.copy()
        return output_nodes

    def _validate_node(self, node):
        """Check if node is in current directory."""
        validate_type(node, 'node', NodeImpl, 'Node')
        node = self._get_node(node.name, node.rank, node.graph_name)
        if node is None:
            raise DebuggerParamValueError(f"Failed to find node {node.name} with rank {node.rank} "
                                          "in dump directory.")

    def _get_iterable_ranks(self, ranks):
        """
        Validate input ranks and return iterable rands.

        Args:
           ranks (Union[int, list[int], None], optional): The range of ranks.

        Returns:
            list[int], list of rank id.
        """
        total_ranks = self.get_ranks()
        return parse_param_to_iterable_obj(ranks, 'ranks', total_ranks)
