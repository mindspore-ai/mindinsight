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
from collections import deque
from copy import deepcopy

from mindinsight.datavisual.data_transform.graph.msgraph import MSGraph
from mindinsight.debugger.common.exceptions.exceptions import \
    DebuggerNodeNotInGraphError, DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from .node_type_identifier import NodeTypeIdentifier


def _is_match(identifier, node, condition):
    """Check if the node is matched to the identifier.
    Args:
        identifier (NodeTypeIdentifier): The debug name of the node.
        node (Node obj): The number of layers the user wants to trace. Default is 0.

    Returns:
        list, a list of the traced tensors' name and node type,
            arranged in order from leaf node to root node.
        int, the number of output tensors.
    """
    if condition:
        matched = identifier.is_match(node, condition)
    else:
        matched = identifier.is_match(node)
    return matched


class DebuggerGraph(MSGraph):
    """The `DebuggerGraph` object provides interfaces to describe a debugger graph."""

    @property
    def leaf_nodes(self):
        """Return the leaf nodes."""
        return self._leaf_nodes

    @property
    def normal_node_map(self):
        """Return the normal_node_map"""
        return self._normal_node_map

    @property
    def node_id_map_name(self):
        """Return the node_id_map_name"""
        return self._node_id_map_name

    @property
    def const_node_temp_cache(self):
        """Return const_node_temp_cache"""
        return self._const_node_temp_cache

    @property
    def parameter_node_temp_cache(self):
        """Return parameter_node_temp_cache"""
        return self._parameter_node_temp_cache

    @property
    def full_name_map_name(self):
        """Return full_name_map_name"""
        return self._full_name_map_name

    def get_node_name_by_full_name(self, full_name):
        """Get node name by full names."""
        inner_name = self._full_name_map_name.get(full_name, '')
        if not inner_name:
            log.warning("Node %s does not find the relative inner node name.", full_name)

        return inner_name

    def get_full_name_by_node_name(self, node_name):
        """Get full name by node name."""
        if not node_name:
            return ''
        node = self._normal_node_map.get(node_name)
        if not node:
            log.error("Node <%s> is not in graph.", node_name)
            raise DebuggerNodeNotInGraphError(node_name=node_name)

        return node.full_name

    def get_node_type(self, node_name):
        """
        Get the type of the node.

        Args:
            node_name (str): The full name of the node with its scope.

        Returns:
            str, node type or name_scope.
        """
        if not node_name:
            return 'name_scope'
        node = self._normal_node_map.get(node_name)
        if not node:
            log.error("Node <%s> is not in graph.", node_name)
            raise DebuggerNodeNotInGraphError(node_name=node_name)

        return node.type

    def search_nodes_by_category(self, node_category, condition=None):
        """
        Search nodes by type.

        Args:
            node_category (TargetTypeEnum): The node type supported in
                mindinsight.conditionmgr.condition.TargetTypeEnum.
            condition (dict): Search condition. Default: None.

                - activation_func (Union[str, list[str]): The target functions. Used when node_type
                    is TargetTypeEnum.ACTIVATION.
                - search_range (list[Node]): The list of nodes to be searched from.

        Returns:
            list[Node], list of nodes.
        """
        identifier = NodeTypeIdentifier(node_category.value)
        # get search range
        condition = {} if condition is None else condition
        search_range = condition.pop('search_range', None)
        if not search_range:
            search_range = self._leaf_nodes.values()
        # search match nodes
        matched_nodes = []
        for node in search_range:
            matched = _is_match(identifier, node, condition)
            if matched:
                matched_nodes.append(node)
        return matched_nodes

    def get_tensor_history(self, node_name, depth=0):
        """
        Get the tensor history of a specified node.

        Args:
            node_name (str): The debug name of the node.
            depth (int): The number of layers the user wants to trace. Default is 0.

        Returns:
            list, a list of the traced tensors' name and node type,
                arranged in order from leaf node to root node.
            int, the number of output tensors.
        """
        node = self._leaf_nodes.get(node_name)
        tensor_history = self._get_tensor_infos_of_node(node)
        cur_outputs_nums = len(tensor_history)
        cur_depth = 0
        trace_list = deque([(node, cur_depth)])
        while trace_list:
            cur_node, cur_depth = trace_list.popleft()
            tensors_info = self._get_input_tensors_of_node(cur_node)
            if tensors_info:
                tensor_history.extend(tensors_info)
            if cur_depth < depth:
                for name in cur_node.inputs.keys():
                    trace_list.append((self._leaf_nodes[name], cur_depth + 1))

        return tensor_history, cur_outputs_nums

    @staticmethod
    def _get_tensor_infos_of_node(cur_node, slot=None):
        """Get tensors info of specified node."""
        tensors_info = []
        if slot is None:
            slots = range(cur_node.output_nums)
        elif slot >= 0:
            slots = [slot]
        else:
            log.info("Skip get tensor info for %s:%s.", cur_node.name, slot)
            return tensors_info
        for num in slots:
            tensor_info = {
                'name': cur_node.name + ':' + str(num),
                'full_name': cur_node.full_name + ':' + str(num),
                'node_type': cur_node.type
            }
            tensors_info.append(tensor_info)

        return tensors_info

    def _get_input_tensors_of_node(self, cur_node):
        """Get input tensors of node."""
        tensors_info = []
        for name in cur_node.inputs.keys():
            node = self._leaf_nodes.get(name)
            tensor_info = self._get_tensor_infos_of_node(node)
            tensors_info.extend(tensor_info)

        return tensors_info

    def get_bfs_order(self):
        """
        Traverse the graph in order of breath-first search.

        Returns:
            list, including the leaf nodes arranged in BFS order.
        """
        root = self.get_default_root()
        log.info('Randomly choose node %s as root to do BFS.', root.name)

        bfs_order = []
        self.get_bfs_graph(root.name, bfs_order)
        length = len(self._leaf_nodes.keys())
        # Find rest un-traversed nodes
        for node_name, _ in self._leaf_nodes.items():
            if node_name not in bfs_order:
                self.get_bfs_graph(node_name, bfs_order)

        if len(bfs_order) != length:
            log.error("The length of bfs and leaf nodes are not equal.")
            msg = "Not all nodes are traversed!"
            raise DebuggerParamValueError(msg)

        return bfs_order

    def get_bfs_graph(self, node_name, bfs_order):
        """
        Traverse the graph in order of breath-first search.

        Returns:
            list, including the leaf nodes arranged in BFS order.
        """
        temp_list = deque()
        temp_list.append(node_name)
        while temp_list:
            node_name = temp_list.popleft()
            node = self._leaf_nodes.get(node_name)

            if not node:
                log.warning('Cannot find node %s in graph. Ignored.', node_name)
                continue

            bfs_order.append(node_name)
            if node.inputs:
                for name in node.inputs.keys():
                    if name not in temp_list and name not in bfs_order:
                        temp_list.append(name)
            if node.outputs:
                for name in node.outputs.keys():
                    if name not in temp_list and name not in bfs_order:
                        temp_list.append(name)

    def get_default_root(self):
        """
        Get a node as default root for BFS in graph. Using the
        leaf node with the smallest node id as the default root.

        Returns:
            str, the name of the default root.
        """
        default_root = None
        for _, item in self._leaf_nodes.items():
            if item.node_id == '1':
                default_root = item
                break

        if default_root is None:
            log.error("Abnormal graph. Invalid node for BFS.")
            msg = 'Abnormal graph. Invalid node for BFS.'
            raise DebuggerParamValueError(msg)

        return default_root

    def get_tensor_graph(self, node_name):
        """
        Get graph relative to a node.

        Args:
            node_name (str): Node name.

        Returns:
            dict, tensor graph, format is:
                {'nodes': [
                    {'name': <node name>,
                    'full_name': <node full name>,
                    'type': <node type>
                    'input': <input objects>,
                    'output': <output objects>,
                    'slot': {'id': <slot id>}
                    }
                ]}
        """
        graph_nodes = []
        cur_node = self._leaf_nodes.get(node_name)
        node_detail_info = cur_node.to_dict()
        cur_node_info = self._get_node_info_for_tensor_graph(cur_node)
        cur_node_info['input'] = deepcopy(node_detail_info.get('input'))
        cur_node_info['output'] = deepcopy(node_detail_info.get('output'))
        self._add_input_node_info(cur_node_info=cur_node_info, graph_nodes=graph_nodes)
        self._add_output_node_info(cur_node=cur_node, cur_node_info=cur_node_info, graph_nodes=graph_nodes)
        graph_nodes.append(cur_node_info)
        return {'nodes': graph_nodes}

    @staticmethod
    def _get_node_info_for_tensor_graph(node):
        """Get node infos for tensor graph."""
        node_info = {
            'name': node.name,
            'full_name': node.full_name,
            'type': node.type,
            'input': {},
            'output': {},
            'slots': [{'slot': str(slot)} for slot in range(node.output_nums)]
        }
        return node_info

    def _add_output_node_info(self, cur_node, cur_node_info, graph_nodes):
        """
        Add output node info into cur_node_info and node list.

        Args:
            cur_node (Node): The current node object.
            cur_node_info (dict): Current node info.
            graph_nodes (list[<Node info>]): The nodes in tensor graph.
        """
        output_slot_mapping = self._get_slot_mapping(cur_node)
        for node_name, edge_info in cur_node_info.get('output').items():
            edge_info['slot_mapping'] = output_slot_mapping
            # add output node info into graph
            output_node = self._leaf_nodes.get(node_name)
            output_node_info = self._get_node_info_for_tensor_graph(output_node)
            output_node_info['input'][cur_node.name] = edge_info
            graph_nodes.append(output_node_info)

    def _add_input_node_info(self, cur_node_info, graph_nodes):
        """
        Add input node info into cur_node_info and node list.

        Args:
            cur_node_info (dict): Current node info.
            graph_nodes (list[<Node info>]): The nodes in tensor graph.
        """
        cur_node_name = cur_node_info.get('name')
        for node_name, edge_info in cur_node_info.get('input').items():
            input_node = self._leaf_nodes.get(node_name)
            edge_info['slot_mapping'] = self._get_slot_mapping(input_node)
            # add input node info into graph
            input_node_info = self._get_node_info_for_tensor_graph(input_node)
            input_node_info['output'][cur_node_name] = edge_info
            graph_nodes.append(input_node_info)

    @staticmethod
    def _get_slot_mapping(input_node):
        """Get slot mapping between nodes."""
        return [[str(slot), ''] for slot in range(input_node.output_nums)]
