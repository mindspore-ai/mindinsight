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
"""The parallel strategy graph classes."""
import copy
import sys
import time
from enum import Enum
from typing import List

from mindinsight.profiler.common.log import logger
from mindinsight.datavisual.common.enums import PluginNameEnum


class NodeType(Enum):
    """Define the types of nodes that require special processing."""
    PARAMETER = 'Parameter'
    CONST = 'Const'


class NodeInstanceType(Enum):
    """Define the actual role of the node."""
    # Means that the operator is used to do gradient aggregation
    GRADIENT_AGGREGATION = 'GradientAggregation'

    # Means that the operator is a redistribution insertion operator
    REDISTRIBUTION = 'Redistribution'


class DataType(Enum):
    """Define the data type, more detail refer the anf ir proto file."""
    DT_STRING = 'DT_STRING'
    DT_BOOL = 'DT_BOOL'
    DT_INT8 = 'DT_INT8'
    DT_INT16 = 'DT_INT16'
    DT_INT32 = 'DT_INT32'
    DT_INT64 = 'DT_INT64'
    DT_UINT8 = 'DT_UINT8'
    DT_UINT16 = 'DT_UINT16'
    DT_UINT32 = 'DT_UINT32'
    DT_UINT64 = 'DT_UINT64'
    DT_FLOAT16 = 'DT_FLOAT16'
    DT_FLOAT32 = 'DT_FLOAT32'
    DT_FLOAT64 = 'DT_FLOAT64'
    DT_TENSOR = 'DT_TENSOR'
    DT_LIST = 'DT_LIST'
    DT_TUPLE = 'DT_TUPLE'
    DT_NONE = 'DT_NONE'
    DT_TYPE = 'DT_TYPE'


class Node:
    """Define the attributes of a node."""

    def __init__(self, name, node_id, topo_index=-1):
        self._node_id = node_id
        self.name = name
        self.type = ""
        self.instance_type = ''
        self._attr = dict()
        self._input = []
        self._output = {}
        self.scope = ""
        self.output_shape = []
        self.output_data_type = ""

        # This value will be used as the priority field.
        self.topo_index = topo_index
        self.parallel_group = []
        self.parallel_strategy = []  # gen_strategy
        self.parallel_group_ranks = ''

    @property
    def node_id(self):
        """The id of this node, and id is unique in graph."""
        return self._node_id

    @property
    def attr(self):
        """Get node attr."""
        return self._attr

    def add_attr(self, attr_dict):
        """
        Update node attr.

        Args:
            attr_dict (dict[str, str]): The attr of node.
        """
        self._attr.update(attr_dict)

    @property
    def input(self):
        """
        Get all input of current node.

        Returns:
            list[str], refer to the input attr.
        """
        return self._input

    def add_input(self, name):
        """
        Update input.

        Args:
            name (str): The source node name.
        """
        self._input.append(name)

    def replace_input(self, inputs):
        """Replace input"""
        self._input = inputs

    def remove_input(self, name):
        """Remove the input from node."""
        self._input.remove(name)

    def to_dict(self):
        return dict(
            node_id=str(self.topo_index) if self.type != NodeType.CONST.value else self._node_id,
            name=self.name,
            scope=self.scope,
            type=self.type,
            instance_type=self.instance_type,
            attr=self._attr,
            input=self._input,
            output_shape=self.output_shape,
            output_data_type=self.output_data_type,
            parallel_group=self.parallel_group,
            parallel_shard=self.parallel_strategy,
            parallel_group_rank=self.parallel_group_ranks
        )


class Graph:
    """This class holds graph data parsed from files"""

    # Limit the size of a single attribute value per node to avoid storing too much data
    MAX_NODE_ATTRIBUTE_VALUE_BYTES = 1024

    def __init__(self):
        self.rank_id = 0
        self.op_nodes = {}
        self.const_nodes = {}
        self.parameter_nodes = {}

    def build_graph(self, graph_proto: dict, rank_id: str):
        start = time.time()
        self.rank_id = rank_id
        self._parse_graph_proto(graph_proto)
        logger.info("Parse graph proto success, op node count: %d, parameters count: %d, "
                    "const count: %d, use time: %s.",
                    len(self.op_nodes), len(self.parameter_nodes), len(self.const_nodes), (time.time() - start))

    def list_op_node_id(self):
        for node_id in self.op_nodes:
            yield node_id

    def get_op_node(self, node_id):
        return self.op_nodes[node_id]

    def _parse_graph_proto(self, graph_proto: dict):
        self._parse_const_nodes(graph_proto['constVals'])
        self._parse_parameter_nodes(graph_proto['parameters'])
        self._parse_op_nodes(graph_proto['node'])
        self._update_input()

    def _update_input(self):
        """Update op node input"""
        for op_node in self.op_nodes.values():
            inputs = list(op_node.input)
            new_inputs = []
            for input_name in inputs:
                if input_name in self.const_nodes:
                    new_inputs.append(input_name)
                    continue

                if input_name not in self.op_nodes:
                    op_node.remove_input(input_name)
                    continue
                src_node = self.get_op_node(input_name)
                new_inputs.append(str(src_node.topo_index))
            op_node.replace_input(new_inputs)

    def _parse_op_nodes(self, node_protos):
        """Transform the node proto into Node class."""
        index = 1
        for node_proto in node_protos:
            name = node_proto.get('name')
            full_name = node_proto.get('fullName')
            if not name or not full_name:
                logger.warning("Finding a node with an empty name or empty full_name will not save it.")
                continue
            scope = node_proto.get('scope', '')
            op_type = node_proto.get('opType', '')
            node_name = self._process_node_name(scope, op_type, name, full_name)
            node = Node(name=node_name, node_id=name, topo_index=index)
            index += 1
            node.scope = scope
            node.type = op_type

            attribute = node_proto.get('attribute', [])
            input_ = node_proto.get('input', [])
            self._parse_attr_proto(attribute, node)
            self._parse_input_proto(input_, node)
            if 'shapes' in node.attr:
                node.output_shape = node.attr['shapes']
            else:
                node.output_shape = self._get_shape_by_parse_type_proto(node_proto.get('outputType', dict()))
            node.output_data_type = self._get_data_type_by_parse_type_proto(node_proto.get('outputType', dict()))

            node.parallel_group = [node.attr['group']] if 'group' in node.attr else []
            node.parallel_strategy = node.attr.get('in_strategy', [])
            node.parallel_group_ranks = node.attr.get('group_ranks', '')

            instance_name = node_proto.get('instanceName', '')
            if 'grad_mirror' in instance_name:
                node.instance_type = NodeInstanceType.GRADIENT_AGGREGATION.value
            elif 'redistribution' in instance_name:
                node.instance_type = NodeInstanceType.REDISTRIBUTION.value
            else:
                node.instance_type = ''

            self._append_node(node)

    def _parse_const_nodes(self, consts):
        """
        Parse `anf_ir_pb2.NameValueProto` object, and create a const node.

        Args:
            consts (list[anf_ir_pb2.NameValueProto]): Refer to `anf_ir_pb2.NameValueProto` object.
        """
        for const in consts:
            key = const.get('key')
            if not key:
                logger.warning("Finding a const with an empty key will not save it.")
                continue

            node = Node(name=key, node_id=key)
            node.type = NodeType.CONST.value

            self._append_node(node)

    def _parse_parameter_nodes(self, parameter_protos: list):
        """
        Parse `anf_ir_pb2.ParameterProto` object, and create a const node.

        Args:
            parameter_protos (list[dict]): The dict object refers to anf_ir_pb2.ParameterProto.
        """
        for parameter in parameter_protos:
            name = parameter.get('name')
            if not name:
                logger.warning("Finding a parameter with an empty name will not be saved.")
                continue
            node = Node(name=name, node_id=name)
            # Note: Display parameter as Const
            node.type = NodeType.CONST.value
            self._append_node(node)

    def _append_node(self, node: Node):
        if node.type == NodeType.PARAMETER.value:
            self.parameter_nodes[node.node_id] = node
        elif node.type == NodeType.CONST.value:
            self.const_nodes[node.node_id] = node
        else:
            self.op_nodes[node.node_id] = node

    @staticmethod
    def _process_node_name(scope, node_type: str, node_id: str, full_name=None):
        """Handle the special node name."""
        if node_type == "Load":
            # The Load operator needs to be renamed as it has the same name with parameter
            node_name = f'{scope}/{node_type}-op{node_id}'
        elif not full_name or \
                any(full_name.lower().endswith(f'[:{plugin.value.lower()}]') for plugin in PluginNameEnum):
            # process summary node
            node_name = f'{scope}/{node_type}-op{node_id}'
        else:
            node_name = full_name

        return node_name

    def _parse_attr_proto(self, attributes, node):
        """
        Parse `anf_ir_pb2.AttributeProto` object., and Filters large attribute values.

        Args:
            attributes (list[anf_ir_pb2.AttributeProto]): Refer to `anf_ir_pb2.AttributeProto` object.
            node (Node): Refer to `Node` object, it is used to log message and update attr.
        """
        for attr in attributes:
            if sys.getsizeof(attr['value']) > self.MAX_NODE_ATTRIBUTE_VALUE_BYTES:
                message = f"The attribute value of node({node.name}) " \
                          f"is over {self.MAX_NODE_ATTRIBUTE_VALUE_BYTES} Bytes, will ignore."
                logger.warning(message)
                continue

            if attr['name'] == 'gen_strategy':
                # The gen_strategy value is equal in_strategy value, so we only need to show one strategy value in attr
                continue

            value = self._parse_value_proto(attr['value'])
            node.add_attr({attr['name']: str(value)})

    def _parse_value_proto(self, value_proto: dict):
        """Format the value proto into python base type."""
        actual_value = value_proto

        if value_proto['dtype'] == DataType.DT_STRING.value:
            actual_value = value_proto['strVal']
        elif value_proto['dtype'] in (DataType.DT_INT8.value, DataType.DT_INT16.value,
                                      DataType.DT_INT32.value, DataType.DT_INT64.value):
            actual_value = int(value_proto['intVal'])
        elif value_proto['dtype'] == DataType.DT_BOOL.value:
            actual_value = bool(int(value_proto['boolVal']))
        elif value_proto['dtype'] in (DataType.DT_UINT8.value, DataType.DT_UINT16.value,
                                      DataType.DT_UINT32.value, DataType.DT_UINT64.value):
            actual_value = int(value_proto['uintVal'])
        elif value_proto['dtype'] in (DataType.DT_FLOAT16.value, DataType.DT_FLOAT32.value, DataType.DT_FLOAT64.value):
            actual_value = float(value_proto['floatVal']) if value_proto['floatVal'] \
                else value_proto.get('doubleVal', 0)
        elif value_proto['dtype'] in (DataType.DT_TUPLE.value, DataType.DT_LIST.value):
            actual_value = []
            for value in value_proto.get('values', []):
                actual_value.append(self._parse_value_proto(value))
        elif value_proto['dtype'] == DataType.DT_NONE.value:
            actual_value = value_proto['strVal']
        elif value_proto['dtype'] == DataType.DT_TYPE.value:
            actual_value = value_proto.get('typeVal', {}).get('dataType', '')

        return actual_value

    @staticmethod
    def _parse_input_proto(input_protos: list, node: Node):
        """
        Parse `anf_ir_pb2.InputProto` object.

        Args:
            input_protos (list[dict]): The key of this param refer to `anf_ir_pb2.InputProto` object.
            node (Node): Refer to `Node` object, it is used to log message and update input.
        """
        for input_proto in input_protos:
            if not input_proto['name']:
                logger.warning("The name in input proto of node(%s) is empty, will ignore.", node.name)
                continue

            node.add_input(name=input_proto['name'])

    def _get_shape_by_parse_type_proto(self, type_proto: dict):
        """
        Parse proto's `message TypeProto` to get shape information.

        Args:
            type_proto (dict): The keys of this param refer to anf_ir_pb2.TypeProto.

        Returns:
            list, a list of shape.
        """
        shapes = []
        if not type_proto:
            return shapes

        if 'dataType' in type_proto:
            if type_proto['dataType'] != DataType.DT_TENSOR.value and \
                    type_proto['dataType'] != DataType.DT_TUPLE.value:
                return []
        if 'tensorType' in type_proto and 'shape' in type_proto['tensorType']:
            tensor_type = type_proto['tensorType']
            tensor_shape_proto = tensor_type['shape']
            shapes = [dim['size'] for dim in tensor_shape_proto['dim']]
        if 'sequenceType' in type_proto and 'elemTypes' in type_proto['sequenceType']:
            for elem_type in type_proto['sequenceType']['elemTypes']:
                shape = self._get_shape_by_parse_type_proto(elem_type)
                if shape:
                    shapes.append(shape)
        return shapes

    def _get_data_type_by_parse_type_proto(self, type_proto: dict):
        """
        Get data type by parse type proto object.

        The name of the DataType, refer to `anf_ir_pb2.DataType` object.
        If data type is tensor or tuple, the data name we return is `data_type[element_type, element_type]`.

        Args:
            type_proto (dict): The keys of this param refer to anf_ir_pb2.TypeProto.

        Returns:
            str, the data type.
        """
        if not type_proto:
            return ''

        data_type_name = type_proto['dataType']
        if type_proto['dataType'] == DataType.DT_TENSOR.value:
            tensor_type_proto = type_proto['tensorType']
            elem_type_name = tensor_type_proto['elemType']
            return f'{data_type_name}[{elem_type_name}]'

        if type_proto['dataType'] == DataType.DT_TUPLE.value:
            data_types = []
            for elem_type in type_proto['sequenceType']['elemTypes']:
                data_types.append(self._get_data_type_by_parse_type_proto(elem_type))
            return f'{data_type_name}{str(data_types)}'

        return data_type_name


class MergedGraph:
    """We will merge `Graph`s from the same stage into a graph, and call the new graph MergedGraph."""

    def __init__(self):
        self._rank_ids = []
        self._op_nodes = {}
        self._const_nodes = {}
        self._parameter_nodes = {}

    def merge_graphs(self, graphs: List[Graph]):
        """This function merge the same stage graphs into a graph."""
        if not graphs:
            logger.warning("Can not find any graph when merge graphs.")
            return

        for graph in graphs:
            self._rank_ids.append(graph.rank_id)

        # Graph has the same operator on the same stage, so we can use the node ids with any graphs.
        node_ids = graphs[0].list_op_node_id()
        for node_id in node_ids:
            node = graphs[0].get_op_node(node_id)
            new_node = copy.deepcopy(node)
            for graph in graphs[1:]:
                new_node.parallel_group.extend(graph.get_op_node(node_id).parallel_group)
                new_node.parallel_group = list(sorted(set(new_node.parallel_group)))

            self._op_nodes[new_node.node_id] = new_node

        self._const_nodes = graphs[0].const_nodes
        self._parameter_nodes = graphs[0].parameter_nodes

    def to_dict(self):
        result = dict(
            rank_ids=sorted(map(int, self._rank_ids)),
            op_nodes=[node.to_dict() for node in self._op_nodes.values()],
            const_nodes=[node.to_dict() for node in self._const_nodes.values()],
            parameter_nodes=[node.to_dict() for node in self._parameter_nodes.values()]
        )
        return result


class SupportedParallelType(Enum):
    DATA_PARALLEL = 'data_parallel'
    SEMI_AUTO_PARALLEL = 'semi_auto_parallel'
    AUTO_PARALLEL = 'auto_parallel'

    @classmethod
    def list_members(cls):
        """List all members."""
        return [member.value for member in cls]


class GraphManager:
    """
    This class is used to add original graphs and manage the merged graphs.

    We use this class to build the original computation graph and then merge the same stage graphs into MergedGraph.
    And we can query any merged graph by this class.

    Args:
        parallel_type (str): The parallel type, refer to `SupportedParallelType`.
        stage_devices (list): refer to MindSpore ccsrc/utils/profiling_parallel.proto
            ProfilingParallel.Config.stage_devices.

    Examples:
        >>> manager = GraphManager('AUTO_PARALLEL', parallel.config.stage_devices)
        >>> for file in sorted(path.rglob("parallel_strategy*.pb")):
        ...     with file.open(mode='rb') as fp:
        ...         manager.add_graph(parallel.graph, parallel.config.rank_id)
        >>> manager.merge_graph()
    """

    def __init__(self, parallel_type: str, stage_id: str, stage_devices: list):
        self._parallel_type = parallel_type
        self._stage_id = stage_id
        self._stage_devices = stage_devices
        self._merged_graph = MergedGraph()
        self._rank_graphs = {}

    def add_graph(self, graph: Graph, rank_id: str):
        """Add an original graph object which is parsed from pb files."""
        self._rank_graphs[rank_id] = graph

    def merge_graph(self):
        """Merge the same stage graphs into a merged graph."""
        graphs = []
        for rank_id in self._stage_devices:
            if rank_id not in self._rank_graphs:
                logger.warning("This rank id(%s) is not found in all the parsed files.", rank_id)
                continue
            graphs.append(self._rank_graphs[rank_id])

        if not graphs:
            logger.warning("There can not find any graph in stage %s.", self._stage_id)
            return

        self._merged_graph.merge_graphs(graphs)

    def to_dict(self):
        """Get all merged graphs and the training attributes."""
        if self._merged_graph:
            return self._merged_graph.to_dict()
        return None
