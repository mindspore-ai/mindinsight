# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.proto_files.mindinsight_anf_ir_pb2 import DataType
from mindinsight.datavisual.common.enums import PluginNameEnum
from .node_tree import NodeTree
from .node import Node
from .node import NodeTypeEnum
from .graph import Graph
from .graph import EdgeTypeEnum
from .graph import check_invalid_character


class MSGraph(Graph):
    """The object describes the MindSpore graph, and it is defined in the anf_ir proto file."""

    def _parse_data(self, proto_data):
        """
        The proto data is parsed and all nodes are stored in the specified structure.

        Args:
            proto_data (anf_ir_pb2.GraphProto): Refer to anf_ir_pb2.GraphProto object.
        """
        logger.info("Start to parse graph proto data.")

        self._parse_op_nodes(proto_data.node)
        self._parse_parameters(proto_data.parameters)
        self._parse_consts(proto_data.const_vals)

        self._update_input_after_create_node()
        self._update_output_after_create_node()

        logger.info("Parse proto data end, normal node count(only contain op node, "
                    "parameter, const): %s.", self.normal_node_count)

    def _parse_op_nodes(self, node_protos):
        """
        Parse `anf_ir_pb2.NodeProto` object, and create a normal node.

        Args:
            node_protos (list[anf_ir_pb2.NodeProto]): Refer to anf_ir_pb2.NodeProto.
        """
        logger.debug("Start to parse op nodes from proto.")
        for topological_index, node_proto in enumerate(node_protos):
            if not node_proto.name:
                logger.warning("Finding a node with an empty name will not save it.")
                continue

            if node_proto.op_type == "Load":
                # The Load operator needs to be renamed as it has the same name with parameter
                node_name = Node.create_node_name(scope=node_proto.scope,
                                                  base_name=f'{node_proto.op_type}-op{node_proto.name}')
                node_proto.full_name = node_name
            elif not node_proto.full_name or any(
                    node_proto.full_name.lower().endswith(f'[:{plugin.value.lower()}]') for plugin in PluginNameEnum):
                node_name = Node.create_node_name(scope=node_proto.scope,
                                                  base_name=f'{node_proto.op_type}{node_proto.name}')
            else:
                node_name = node_proto.full_name

            # The Graphviz plug-in that the UI USES can't handle these special characters.
            check_invalid_character(node_name)

            node = Node(name=node_name, node_id=node_proto.name, topological_index=topological_index)
            node.full_name = node_proto.full_name
            node.type = node_proto.op_type

            self._parse_attributes(node_proto.attribute, node)
            self._parse_inputs(node_proto.input, node)

            node.output_i = node_proto.output_i
            node.scope = node_proto.scope
            node.output_shape = self._get_shape_by_parse_type_proto(node_proto.output_type)
            node.output_nums = len(node.output_shape)
            node.output_data_type = self._get_data_type_by_parse_type_proto(node_proto.output_type, node)

            self._cache_node(node)

    def _parse_parameters(self, parameter_protos):
        """
        Parse `anf_ir_pb2.ParameterProto` object, and create a parameter node.

        Args:
            parameter_protos (list[anf_ir_pb2.ParameterProto]): Refer to anf_ir_pb2.ParameterProto.
        """
        logger.debug("Start to parse parameters from proto.")
        for parameter in parameter_protos:
            if not parameter.name:
                logger.warning("Finding a parameter with an empty name will not save it.")
                continue
            check_invalid_character(parameter.name)
            node = Node(name=parameter.name, node_id=parameter.name)
            node.type = NodeTypeEnum.PARAMETER.value
            node.output_shape = self._get_shape_by_parse_type_proto(parameter.type)
            node.output_nums = len(node.output_shape)
            node.output_data_type = self._get_data_type_by_parse_type_proto(parameter.type, node)
            attr = dict(
                type=self._get_data_type_by_parse_type_proto(parameter.type, node),
                shape=str(self._get_shape_by_parse_type_proto(parameter.type))
            )
            node.add_attr(attr)

            self._cache_node(node)
            logger.debug("Foreach graph proto parameters, node id: %s, node name: %s, "
                         "node def name: %s", node.node_id, node.name, parameter.name)

    def _parse_consts(self, consts):
        """
        Parse `anf_ir_pb2.NameValueProto` object, and create a const node.

        Args:
            consts (list[anf_ir_pb2.NameValueProto]): Refer to `anf_ir_pb2.NameValueProto` object.
        """
        logger.debug("Start to parse consts from proto.")
        for const in consts:
            if not const.key:
                logger.warning("Finding a const with an empty key will not save it.")
                continue
            check_invalid_character(const.key)
            node = Node(name=const.key, node_id=const.key)
            node.type = NodeTypeEnum.CONST.value
            if const.value.ByteSize() > self.MAX_NODE_ATTRIBUTE_VALUE_BYTES:
                node.add_attr({const.key: 'dtype: ' + DataType.Name(const.value.dtype)})
            else:
                node.add_attr({const.key: str(const.value)})

            if const.value.dtype == DataType.DT_TENSOR:
                shape = list(const.value.tensor_val.dims)
                node.output_shape.append(shape)
                if const.value.tensor_val.HasField('data_type'):
                    node.elem_types.append(DataType.Name(const.value.tensor_val.data_type))
            else:
                node.elem_types.append(DataType.Name(const.value.dtype))
                # dim is zero
                node.output_shape.append([])

            node.output_nums = len(node.output_shape)

            self._cache_node(node)

    def _get_shape_by_parse_type_proto(self, type_proto):
        """
        Parse proto's `message TypeProto` to get shape information.

        Args:
            type_proto (anf_ir_pb2.TypeProto): Refer to anf_ir_pb2.TypeProto.

        Returns:
            list, a list of shape.
        """
        shapes = []
        if type_proto.HasField('data_type'):
            if type_proto.data_type != DataType.DT_TENSOR and \
                    type_proto.data_type != DataType.DT_TUPLE:
                # Append an empty list as a placeholder
                # for the convenience of output number calculation.
                shapes.append([])
                return shapes
        if type_proto.HasField('tensor_type'):
            tensor_type = type_proto.tensor_type
            tensor_shape_proto = tensor_type.shape
            shape = [dim.size for dim in tensor_shape_proto.dim]
            shapes.append(shape)
        if type_proto.HasField('sequence_type'):
            for elem_type in type_proto.sequence_type.elem_types:
                shapes.extend(self._get_shape_by_parse_type_proto(elem_type))
        return shapes

    def _get_data_type_by_parse_type_proto(self, type_proto, node):
        """
        Get data type by parse type proto object.

        The name of the DataType, refer to `anf_ir_pb2.DataType` object.
        If data type is tensor or tuple, the data name we return is `data_type[element_type, element_type]`.

        Args:
            type_proto (anf_ir_pb2.TypeProto): Refer to anf_ir_pb2.TypeProto.

        Returns:
            str, the data type.

        """
        data_type_name = self._get_data_type_name_by_value(type_proto, type_proto.data_type, field_name='data_type')
        if type_proto.data_type == DataType.DT_TENSOR:
            tensor_type_proto = type_proto.tensor_type
            value = type_proto.tensor_type.elem_type
            elem_type_name = self._get_data_type_name_by_value(tensor_type_proto, value, field_name='elem_type')
            node.elem_types.append(elem_type_name)
            return f'{data_type_name}[{elem_type_name}]'

        if type_proto.data_type == DataType.DT_TUPLE:
            data_types = []
            for elem_type in type_proto.sequence_type.elem_types:
                data_types.append(self._get_data_type_by_parse_type_proto(elem_type, node))
            return f'{data_type_name}{str(data_types)}'

        node.elem_types.append(data_type_name)

        return data_type_name

    def get_nodes(self, searched_node_list):
        """
        Get node tree by a searched_node_list.

        Args:
            searched_node_list (list[Node]): A list of nodes that
                matches the given search pattern.

        Returns:
            A list of dict including the searched nodes.
            [{
                "name": "Default",
                "type": "name_scope",
                "nodes": [{
                    "name": "Default/Conv2D1",
                    "type": "name_scope",
                    "nodes": [{
                        ...
                    }]
                }]
            },
            {
                "name": "Gradients",
                "type": "name_scope",
                "nodes": [{
                    "name": "Gradients/Default",
                    "type": "name_scope",
                    "nodes": [{
                        ...
                }]
            }]
        """
        # save the node in the NodeTree
        root = NodeTree()
        for node in searched_node_list:
            self._build_node_tree(root, node.name, node.type)

        # get the searched nodes in the NodeTree and reorganize them
        searched_list = []
        self._traverse_node_tree(root, searched_list)

        return searched_list

    def search_leaf_nodes_by_pattern(self, pattern):
        """
        Search leaf node by a given pattern.

        Args:
            pattern (Union[str, None]): The pattern of the node to search,
                if None, return all node names.

        Returns:
            list[Node], a list of nodes.
        """
        if pattern is not None:
            pattern = pattern.lower()
            searched_nodes = [
                node for name, node in self._leaf_nodes.items()
                if pattern in name.lower()
            ]
        else:
            searched_nodes = [node for node in self._leaf_nodes.values()]
        return searched_nodes

    def search_nodes_by_pattern(self, pattern):
        """
        Search node by a given pattern.

        Search node which pattern is the part of the last node. Example: pattern=ops, node1=default/ops,
        node2=default/ops/weight, so node2 will be ignore and only node1 will be return.

        Args:
            pattern (Union[str, None]): The pattern of the node to search.

        Returns:
            list[Node], a list of nodes.
        """
        searched_nodes = []
        if pattern and pattern != '/':
            pattern = pattern.lower()
            for name, node in self._normal_node_map.items():
                name = name.lower()
                pattern_index = name.rfind(pattern)
                if pattern_index >= 0 and name.find('/', pattern_index + len(pattern)) == -1:
                    searched_nodes.append(node)
        return searched_nodes

    def _build_node_tree(self, root, node_name, node_type):
        """
        Build node tree.

        Args:
            root (NodeTree): Root node of node tree.
            node_name (str): Node name.
            node_type (str): Node type.
        """
        scope_names = node_name.split('/')
        cur_node = root
        full_name = ""
        for scope_name in scope_names[:-1]:
            full_name = '/'.join([full_name, scope_name]) if full_name else scope_name
            scope_node = self._get_normal_node(node_name=full_name)
            sub_node = cur_node.get(scope_name)
            if not sub_node:
                sub_node = cur_node.add(scope_name, scope_node.type)
            cur_node = sub_node
        cur_node.add(scope_names[-1], node_type)

    def _traverse_node_tree(self, cur_node, search_node_list):
        """Traverse the node tree and construct the searched nodes list."""
        for _, sub_node in cur_node.get_children():
            sub_nodes = []
            self._traverse_node_tree(sub_node, sub_nodes)
            sub_node_dict = {
                'name': sub_node.node_name,
                'type': sub_node.node_type,
                'nodes': sub_nodes
            }
            search_node_list.append(sub_node_dict)

    def _parse_inputs(self, input_protos, node):
        """
        Parse `anf_ir_pb2.InputProto` object.

        Args:
            input_protos (list[anf_ir_pb2.InputProto]): Refer to `anf_ir_pb2.InputProto` object.
            node (Node): Refer to `Node` object, it is used to log message and update input.
        """
        for input_proto in input_protos:
            if not input_proto.name:
                logger.warning("The name in input proto of node(%s) is empty, will ignore.", node.name)
                continue

            edge_type = EdgeTypeEnum.DATA.value if not input_proto.type else EdgeTypeEnum.CONTROL.value

            # Notice:
            # 1. The name in the input proto is the node id of the Node object.
            # 2. In the current step, the shape of source node cannot be obtained,
            #    so it is set to empty list by default, and the next step will update it.
            # 3. Same with scope, set the default value first.
            input_attr = {
                "shape": [],
                "edge_type": edge_type,
                "independent_layout": False,
                'data_type': ''
            }

            node.add_inputs(src_name=input_proto.name, input_attr=input_attr)

    def _parse_attributes(self, attributes, node):
        """
        Parse `anf_ir_pb2.AttributeProto` object., and Filters large attribute values.

        Args:
            attributes (list[anf_ir_pb2.AttributeProto]): Refer to `anf_ir_pb2.AttributeProto` object.
            node (Node): Refer to `Node` object, it is used to log message and update attr.
        """
        for attr in attributes:
            if attr.value.ByteSize() > self.MAX_NODE_ATTRIBUTE_VALUE_BYTES:
                message = f"The attribute value of node({node.name}) " \
                          f"is over {self.MAX_NODE_ATTRIBUTE_VALUE_BYTES} Bytes, will ignore."
                logger.warning(message)
                continue
            node.add_attr({attr.name: str(attr.value)})

    def _update_input_after_create_node(self):
        """Update the input of node after create node."""
        for node in self._normal_node_map.values():
            for src_node_id, input_attr in dict(node.inputs).items():
                node.delete_inputs(src_node_id)
                if not self._is_node_exist(node_id=src_node_id):
                    message = f"The input node could not be found by node id({src_node_id}) " \
                              f"while updating the input of the node({node})"
                    logger.warning(message)

                    continue

                src_node = self._get_normal_node(node_id=src_node_id)
                input_attr['shape'] = src_node.output_shape
                input_attr['data_type'] = src_node.output_data_type
                node.add_inputs(src_name=src_node.name, input_attr=input_attr)

    def _update_output_after_create_node(self):
        """Update the output of node after create node."""
        # Constants and parameter should not exist for input and output.
        filtered_node = {NodeTypeEnum.CONST.value, NodeTypeEnum.PARAMETER.value}
        for node in self._normal_node_map.values():
            for src_name, input_attr in node.inputs.items():
                src_node = self._get_normal_node(node_name=src_name)
                if src_node.type in filtered_node:
                    continue

                src_node.add_outputs(node.name, input_attr)

    @staticmethod
    def _get_data_type_name_by_value(data_type, value, field_name='data_type'):
        """Get the data type name by the enum value, data_type refer to `DataType` object."""
        return data_type.DESCRIPTOR.fields_by_name[field_name].enum_type.values_by_number[value].name
