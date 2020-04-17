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
"""This file is used to define the MindSpore graph."""
import re
import copy

from mindinsight.datavisual.common.log import logger
from .node import Node
from .node import NodeTypeEnum
from .graph import Graph
from .graph import EdgeTypeEnum
from .graph import DataTypeEnum


class MSGraph(Graph):
    """The object describes the MindSpore graph, and it is defined in the anf_if proto file."""

    def build_graph(self, graph_proto):
        """
        Build graph by graph proto which refer to `anf_ir_pb2.GraphProto`, and set status to loading.

        Args:
            graph_proto (anf_ir_pb2.GraphProto): Refer to `anf_ir_pb2.GraphProto`.
        """
        logger.info("Start to build graph.")

        self._build_leaf_nodes(graph_proto)
        self._build_polymeric_nodes()
        self._build_name_scope_nodes()
        self._update_polymeric_input_output()
        logger.info("Build graph end, normal node count: %s, polymeric node "
                    "count: %s.", len(self._normal_nodes), len(self._polymeric_nodes))

    def _build_leaf_nodes(self, graph_proto):
        """
        Build leaf node from graph proto.

        Left node will contain operation node, parameter node, const node.

        Args:
            graph_proto (anf_ir_pb2.model_proto.graph): Refer to anf_ir_pb2.model_proto.graph.
        """
        logger.info("Start to build leaf nodes.")
        leaf_node_id_map_name = {}
        const_nodes_map = {}

        for node_def in graph_proto.node:
            if not node_def.name:
                logger.warning("Finding a node with an empty name will not save it.")
                continue
            node = self._parse_graph_proto_node(node_def)
            leaf_node_id_map_name.update({node.node_id: node.name})

        for parameter in graph_proto.parameters:
            if not parameter.name:
                logger.warning("Finding a parameter with an empty name will not save it.")
                continue
            node = self._parse_graph_proto_parameter(parameter)
            const_nodes_map.update({node.name: node})

        for i, const in enumerate(graph_proto.const_vals):
            if not const.key:
                logger.warning("Finding a const with an empty key will not save it.")
                continue
            node_id = 'const_{}'.format(i)
            node = self._parse_graph_proto_const(const, node_id)
            const_nodes_map.update({const.key: node})

        self._calc_input(leaf_node_id_map_name, graph_proto, const_nodes_map)
        self._calc_output()

        logger.info("Build leaf nodes end, normal nodes count: %s, group count: %s, "
                    "left node count: %s.", len(self._normal_nodes), len(self._node_groups),
                    len(self._leaf_nodes))

    def _calc_input(self, leaf_node_id_map_name, graph_proto, const_nodes_map):
        """
        Calc input for every leaf node.

        Args:
            leaf_node_id_map_name (dict[str, str]): Format is {'node_id': 'node_name'}.
            graph_proto (anf_ir_pb2.model_proto.graph): See anf_ir_pb2.model_proto.graph.
            const_nodes_map (dict[str, Node]): Format is {'node name': <Const node>}.
        """
        logger.debug("Start to calc input.")
        for node_def in graph_proto.node:
            node_name = leaf_node_id_map_name[node_def.name]
            node = self._leaf_nodes[node_name]
            for input_def in node_def.input:
                edge_type = EdgeTypeEnum.DATA.value
                if input_def.type == "CONTROL_EDGE":
                    edge_type = EdgeTypeEnum.CONTROL.value

                if const_nodes_map.get(input_def.name):
                    const_node = copy.deepcopy(const_nodes_map[input_def.name])
                    src_name = '{}/{}'.format(node.name_scope, input_def.name)
                    if not self._normal_nodes.get(src_name):
                        const_node.name = src_name
                        const_node.name_scope = node.name_scope
                        self._normal_nodes.update({src_name: const_node})
                        self._leaf_nodes.update({src_name: const_node})
                    src_node = self._leaf_nodes.get(src_name)
                else:
                    src_name = leaf_node_id_map_name.get(input_def.name)
                    if not src_name:
                        logger.warning("The input_def name '%s' in node '%s' is invalid, "
                                       "will be ignore.", input_def.name, node_name)
                        continue

                    src_node = self._leaf_nodes.get(src_name)
                    if src_node is None:
                        logger.warning("The input '%s' in node '%s' is not in "
                                       "leaf nodes.", src_name, node_name)
                        continue

                input_item = {
                    src_name: {
                        "shape": src_node.shape,
                        "edge_type": edge_type,
                        "scope": NodeTypeEnum.NAME_SCOPE.value
                    }
                }
                node.update_input(input_item)

            if self._normal_nodes.get(node_name):
                self._normal_nodes[node_name] = node
            else:
                group_name = self._create_group_name(node.name_scope, node.node_type, node.name)
                self._node_groups[group_name][node.name] = node

    def _calc_output(self):
        """Calc output of every node."""
        logger.debug("Start to calc output.")

        for name, node in self._leaf_nodes.items():
            if node.node_type == NodeTypeEnum.CONST.value:
                continue
            for src_name, input_attr in node.inputs.items():
                src_node = self._leaf_nodes[src_name]
                if src_node.node_type == NodeTypeEnum.CONST.value:
                    continue

                if self._normal_nodes.get(src_name):
                    self._normal_nodes[src_name].update_output({name: input_attr})
                else:
                    group_name = self._create_group_name(src_node.name_scope,
                                                         src_node.node_type, src_node.name)
                    self._node_groups[group_name][src_name].update_output({name: input_attr})

    def _parse_graph_proto_node(self, node_def):
        """
        Parse `anf_ir_pb2.model_proto.graph.node_def`, and create a a node.

        Args:
            node_def (anf_ir_pb2.model_proto.graph.node_def): Refer to anf_ir_pb2.model_proto.graph.node_def.

        Returns:
            Node, a `Node` object.
        """
        node_name = '/'.join([node_def.scope, node_def.op_type]) + node_def.name \
            if node_def.scope else node_def.op_type + node_def.name
        node = Node(name=node_name, node_id=node_def.name)
        node.node_type = node_def.op_type
        logger.debug("Foreach graph proto nodes, node id: %s, node name: %s, node def name: %s, "
                     "input count: %s", node.node_id, node.name, node_def.name, len(node_def.input))

        for attr in node_def.attribute:
            node.update_attr({attr.name: str(attr.value)})

        node.output_i = node_def.output_i
        node.name_scope = node_def.scope

        output_type = node_def.output_type
        shape = self._parse_type_proto(output_type)
        node.shape = shape

        self._leaf_nodes.update({node.name: node})
        group_name = self._create_group_name(node.name_scope, node.node_type, node.name)
        if group_name is not None:
            node_dict = self._node_groups.get(group_name, {})
            node_dict.update({node.name: node})
            self._node_groups.update({group_name: node_dict})
        else:
            self._normal_nodes.update({node.name: node})

        return node

    def _parse_graph_proto_parameter(self, parameter):
        """
        Parse anf_ir_pb2.model_proto.graph.parameter, and create a parameter node.

        Args:
            parameter (anf_ir_pb2.model_proto.graph.parameter): Refer to anf_ir_pb2.model_proto.graph.parameter.

        Returns:
            Node, a `Node` object.
        """
        node = Node(name=parameter.name, node_id=parameter.name)
        node.node_type = NodeTypeEnum.PARAMETER.value
        node.shape = self._parse_type_proto(parameter.type)
        logger.debug("Foreach graph proto parameters, node id: %s, node name: %s, "
                     "node def name: %s", node.node_id, node.name, parameter.name)
        return node

    def _parse_graph_proto_const(self, const, const_node_id):
        """
        Parse anf_ir_pb2.model_proto.graph.const, and create a const node.

        Args:
            const (anf_ir_pb2.model_proto.graph.const): Refer to anf_ir_pb2.model_proto.graph.const
            const_node_id (str): The id of the new const node, it should be unique in graph.

        Returns:
            Node, a `Node` object.
        """
        node = Node(name=const.key, node_id=const_node_id)
        node.node_type = NodeTypeEnum.CONST.value
        node.update_attr({const.key: str(const.value)})
        if const.value.dtype == DataTypeEnum.DT_TENSOR.value:
            shape = []
            for dim in const.value.tensor_val.dims:
                shape.append(dim)
            node.shape = shape
        return node

    def _parse_type_proto(self, type_proto):
        """
        Parse proto's `message TypeProto` to get shape information.

        Args:
            type_proto (anf_ir_pb2.TypeProto): Refer to anf_ir_pb2.TypeProto.

        Returns:
            list, a list of shape.
        """
        shapes = []
        if type_proto.HasField('tensor_type'):
            tensor_type = type_proto.tensor_type
            tensor_shape_proto = tensor_type.shape
            for dim in tensor_shape_proto.dim:
                shapes.append(dim.size)
        if type_proto.HasField('sequence_type'):
            for elem_type in type_proto.sequence_type.elem_types:
                shapes.append(self._parse_type_proto(elem_type))
        return shapes

    def _create_group_name(self, name_scope, node_type, node_name):
        """
        Create group name by node name, name scope, node type.

        Only nodes that conform to the rules are aggregated.

        Args:
            name_scope (str): The node name scope.
            node_type (str): The node type.
            node_name (str): The node name.

        Returns:
            Optional[str], if match the rules will return a group name, else return None.
        """
        group_types = ['Reshape', 'Variable']
        pattern_names = r'.*?/Cast-op\d+'

        if node_type in group_types:
            group_name = name_scope + '/' + node_type if name_scope else node_type
            return group_name

        if node_type == 'FrameworkOp' and re.search(pattern_names, node_name):
            group_name = name_scope + '/' + 'Cast-op' if name_scope else 'Cast-op'
            return group_name

        return None
