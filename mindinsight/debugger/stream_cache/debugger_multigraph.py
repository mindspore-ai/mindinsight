# Copyright 2020 Huawei Technologies Co., Ltd
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
"""This file is used to define the basic graph."""
import copy
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.datavisual.data_transform.graph.node import Node, NodeTypeEnum
from .debugger_graph import DebuggerGraph


class DebuggerMultiGraph(DebuggerGraph):
    """The `DebuggerMultiGraph` object provides interfaces to describe a debugger multigraph."""

    def add_graph(self, graph_dict):
        """
        Add graphs to DebuggerMultiGraph.

        Args:
            graph_dict (dict): The <graph_name, graph_object> dict.
        """
        if len(graph_dict) == 1:
            graph = list(graph_dict.values())[0]
            self._normal_node_map = graph.normal_node_map
            self._node_id_map_name = graph.node_id_map_name
            self._const_node_temp_cache = graph.const_node_temp_cache
            self._parameter_node_temp_cache = graph.parameter_node_temp_cache
            self._leaf_nodes = graph.leaf_nodes
            self._full_name_map_name = graph.full_name_map_name
        else:
            for graph_name, graph in graph_dict.items():
                log.debug("add graph %s into whole graph.", graph_name)

                # add nodes
                normal_nodes = copy.deepcopy(graph.normal_node_map)
                for _, node_obj in normal_nodes.items():
                    self._add_graph_scope(node_obj, graph_name)
                    self._cache_node(node_obj)

                # add graph_node
                node = Node(name=graph_name, node_id=graph_name)
                node.type = NodeTypeEnum.NAME_SCOPE.value
                node.subnode_count = len(graph.list_node_by_scope())
                self._cache_node(node)

            self._leaf_nodes = self._get_leaf_nodes()
            self._full_name_map_name = self._get_leaf_node_full_name_map()

            log.info(
                "Build multi_graph end, all node count: %s, const count: %s, parameter count: %s.",
                self.normal_node_count, len(self._const_node_temp_cache),
                len(self._parameter_node_temp_cache))

    def _add_graph_scope(self, node, graph_name):
        """Add graph scope to the inputs and outputs in node"""

        # add graph scope to node name
        pre_scope = graph_name + "/"
        node.name = pre_scope + node.name
        if node.scope:
            node.scope = pre_scope + node.scope
        else:
            node.scope = graph_name

        # update inputs
        old_inputs = copy.deepcopy(node.inputs)
        for src_name, input_attr in old_inputs.items():
            new_src_name = graph_name + "/" + src_name
            node.add_inputs(new_src_name, input_attr)
            node.delete_inputs(src_name)

        # update outputs
        old_outputs = copy.deepcopy(node.outputs)
        for dst_name, output_attr in old_outputs.items():
            new_dst_name = graph_name + "/" + dst_name
            node.add_outputs(new_dst_name, output_attr)
            node.delete_outputs(dst_name)

        # update proxy_inputs
        old_proxy_inputs = copy.deepcopy(node.proxy_inputs)
        for src_name, input_attr in old_proxy_inputs.items():
            new_src_name = graph_name + "/" + src_name
            node.add_proxy_inputs(new_src_name, input_attr)
            node.delete_proxy_inputs(src_name)

        # update proxy_outputs
        old_proxy_outputs = copy.deepcopy(node.proxy_outputs)
        for dst_name, output_attr in old_proxy_outputs.items():
            new_dst_name = graph_name + "/" + dst_name
            node.add_proxy_outputs(new_dst_name, output_attr)
            node.delete_proxy_outputs(dst_name)
