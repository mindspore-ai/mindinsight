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
from enum import Enum
from typing import List

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.exceptions.exceptions import UnsupportedParallelTypeException
from mindinsight.profiler.common.exceptions.exceptions import WrongParallelStrategyDataException
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.proto_files.mindinsight_anf_ir_pb2 import DataType


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
            dict[str, dict], refer to the input attr.
        """
        return self._input

    def add_input(self, name):
        """
        Update input.

        Args:
            name (str): The source node name.
        """
        self._input.append(name)

    def to_dict(self):
        return dict(
            node_id=self._node_id,
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

    def build_graph(self, graph_proto, rank_id):
        self.rank_id = rank_id
        self._parse_graph_proto(graph_proto)

    def list_op_node_id(self):
        for node_id in self.op_nodes:
            yield node_id

    def get_op_node(self, node_id):
        return self.op_nodes[node_id]

    def _parse_graph_proto(self, graph_proto):
        self._parse_const_nodes(graph_proto.const_vals)
        self._parse_parameter_nodes(graph_proto.parameters)
        self._parse_op_nodes(graph_proto.node)

    def _parse_op_nodes(self, node_protos):
        """Transform the node proto into Node class."""
        for topo_index, node_proto in enumerate(node_protos):
            if not node_proto.name or not node_proto.full_name:
                logger.warning("Finding a node with an empty name or empty full_name will not save it.")
                continue

            node_name = self._process_node_name(node_proto.scope, node_proto.op_type,
                                                node_proto.name, node_proto.full_name)
            node = Node(name=node_name, node_id=node_proto.name, topo_index=topo_index)
            node.scope = node_proto.scope
            node.type = node_proto.op_type

            self._parse_attr_proto(node_proto.attribute, node)
            self._parse_input_proto(node_proto.input, node)
            if 'shapes' in node.attr:
                node.output_shape = node.attr['shapes']
            else:
                node.output_shape = self._get_shape_by_parse_type_proto(node_proto.output_type)
            node.output_data_type = self._get_data_type_by_parse_type_proto(node_proto.output_type)

            node.parallel_group = [node.attr['group']] if 'group' in node.attr else []
            node.parallel_strategy = node.attr['strategy'] if 'strategy' in node.attr else []
            node.parallel_strategy = node.attr['gen_strategy'] if 'gen_strategy' in node.attr else []
            node.parallel_group_ranks = node.attr['group_ranks'] if 'group_ranks' in node.attr else ''

            if 'grad_mirror' in node_proto.instance_name:
                node.instance_type = NodeInstanceType.GRADIENT_AGGREGATION.value
            elif 'redistribution' in node_proto.instance_name:
                node.instance_type = NodeInstanceType.REDISTRIBUTION.value
            else:
                node.instance_type = ''

            self._append_node(node)

    def _parse_parameter_nodes(self, parameter_protos):
        """
        Parse `anf_ir_pb2.ParameterProto` object, and create a parameter node.

        Args:
            parameter_protos (list[anf_ir_pb2.ParameterProto]): Refer to anf_ir_pb2.ParameterProto.
        """
        for parameter in parameter_protos:
            if not parameter.name:
                logger.warning("Finding a parameter with an empty name will not save it.")
                continue
            node = Node(name=parameter.name, node_id=parameter.name)
            node.type = NodeType.PARAMETER.value
            node.output_shape = self._get_shape_by_parse_type_proto(parameter.type)
            node.output_data_type = self._get_data_type_by_parse_type_proto(parameter.type)
            attr = dict(
                type=self._get_data_type_by_parse_type_proto(parameter.type),
                shape=str(self._get_shape_by_parse_type_proto(parameter.type))
            )
            node.add_attr(attr)

            self._append_node(node)
            logger.debug("Foreach graph proto parameters, node id: %s, node name: %s, "
                         "node def name: %s", node.node_id, node.name, parameter.name)

    def _parse_const_nodes(self, consts):
        """
        Parse `anf_ir_pb2.NameValueProto` object, and create a const node.

        Args:
            consts (list[anf_ir_pb2.NameValueProto]): Refer to `anf_ir_pb2.NameValueProto` object.
        """
        for const in consts:
            if not const.key:
                logger.warning("Finding a const with an empty key will not save it.")
                continue
            node = Node(name=const.key, node_id=const.key)
            node.type = NodeType.CONST.value
            if const.value.ByteSize() > self.MAX_NODE_ATTRIBUTE_VALUE_BYTES:
                node.add_attr({const.key: 'dtype: ' + DataType.Name(const.value.dtype)})
            else:
                node.add_attr({const.key: str(const.value)})

            if const.value.dtype == DataType.DT_TENSOR:
                shape = list(const.value.tensor_val.dims)
                node.output_shape.append(shape)
            else:
                # dim is zero
                node.output_shape.append([])

            node.output_nums = len(node.output_shape)

            self._append_node(node)

    def _append_node(self, node):
        if node.type == NodeType.PARAMETER.value:
            self.parameter_nodes[node.node_id] = node
        elif node.type == NodeType.CONST.value:
            self.const_nodes[node.node_id] = node
        else:
            self.op_nodes[node.node_id] = node

    @staticmethod
    def _process_node_name(scope, node_type, node_id, full_name=None):
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
            if attr.value.ByteSize() > self.MAX_NODE_ATTRIBUTE_VALUE_BYTES:
                message = f"The attribute value of node({node.name}) " \
                          f"is over {self.MAX_NODE_ATTRIBUTE_VALUE_BYTES} Bytes, will ignore."
                logger.warning(message)
                continue

            value = self._parse_value_proto(attr.value)
            # TODO parse attr.value and format it
            node.add_attr({attr.name: str(value)})

    def _parse_value_proto(self, value_proto):
        """Format the value proto into python base type."""
        actual_value = value_proto

        if value_proto.dtype == DataType.DT_STRING:
            actual_value = value_proto.str_val
        elif value_proto.dtype in (DataType.DT_INT8, DataType.DT_INT16, DataType.DT_INT32, DataType.DT_INT64):
            actual_value = value_proto.int_val
        elif value_proto.dtype == DataType.DT_BOOL:
            actual_value = value_proto.bool_val
        elif value_proto.dtype in (DataType.DT_UINT8, DataType.DT_UINT16, DataType.DT_UINT32, DataType.DT_UINT64):
            actual_value = value_proto.uint_val
        elif value_proto.dtype in (DataType.DT_FLOAT16, DataType.DT_FLOAT32, DataType.DT_FLOAT64):
            actual_value = value_proto.float_val if value_proto.float_val else value_proto.double_val
        elif value_proto.dtype in (DataType.DT_TUPLE, DataType.DT_LIST):
            actual_value = []
            for value in value_proto.values:
                actual_value.append(self._parse_value_proto(value))

        return actual_value

    @staticmethod
    def _parse_input_proto(input_protos, node):
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

            node.add_input(name=input_proto.name)

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
                return []
        if type_proto.HasField('tensor_type'):
            tensor_type = type_proto.tensor_type
            tensor_shape_proto = tensor_type.shape
            shapes = [dim.size for dim in tensor_shape_proto.dim]
        if type_proto.HasField('sequence_type'):
            for elem_type in type_proto.sequence_type.elem_types:
                shapes.append(self._get_shape_by_parse_type_proto(elem_type))
        return shapes

    def _get_data_type_by_parse_type_proto(self, type_proto):
        """
        Get data type by parse type proto object.

        The name of the DataType, refer to `anf_ir_pb2.DataType` object.
        If data type is tensor or tuple, the data name we return is `data_type[element_type, element_type]`.

        Args:
            type_proto (anf_ir_pb2.TypeProto): Refer to anf_ir_pb2.TypeProto.

        Returns:
            str, the data type.
        """

        def get_data_type_name_by_value(data_type, data_value, field_name):
            return data_type.DESCRIPTOR.fields_by_name[field_name].enum_type.values_by_number[data_value].name

        data_type_name = get_data_type_name_by_value(type_proto, type_proto.data_type, field_name='data_type')
        if type_proto.data_type == DataType.DT_TENSOR:
            tensor_type_proto = type_proto.tensor_type
            value = type_proto.tensor_type.elem_type
            elem_type_name = get_data_type_name_by_value(tensor_type_proto, value, field_name='elem_type')
            return f'{data_type_name}[{elem_type_name}]'

        if type_proto.data_type == DataType.DT_TUPLE:
            data_types = []
            for elem_type in type_proto.sequence_type.elem_types:
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
                new_node.parallel_group = list(set(new_node.parallel_group))

            self._op_nodes[new_node.node_id] = new_node

        self._const_nodes = graphs[0].const_nodes
        self._parameter_nodes = graphs[0].parameter_nodes

    def to_dict(self):
        result = dict(
            rank_ids=self._rank_ids,
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
        stage_device (TensorShapeProto): refer to profiling_parallel_pb2.Config.stage_devices.

    Examples:
        >>> manager = GraphManager('AUTO_PARALLEL', parallel.config.stage_devices)
        >>> for file in sorted(path.rglob("parallel_strategy*.pb")):
        ...     with file.open(mode='rb') as fp:
        ...         manager.add_graph(parallel.graph, parallel.config.rank_id)
        >>> manager.merge_graph()
    """

    def __init__(self, parallel_type: str, stage_devices):
        if parallel_type not in SupportedParallelType.list_members():
            raise UnsupportedParallelTypeException(f"Only support {SupportedParallelType.list_members()} parallel type,"
                                                   f" but current parallel type is {parallel_type}.")
        self._parallel_type = parallel_type
        self._stage_devices = self._get_stage_devices(stage_devices)
        self._stage_merged_graphs = {}
        self._rank_graphs = {}

    def add_graph(self, graph_proto, rank_id: str):
        """Add an original graph proto which is parsed from pb files."""
        if rank_id in self._rank_graphs:
            msg = f"The file with the same rank id({rank_id}) was found. " \
                  f"There should be no file names with the same rank id."
            logger.error(msg)
            raise WrongParallelStrategyDataException(msg)
        graph = Graph()
        graph.build_graph(graph_proto=graph_proto, rank_id=rank_id)
        self._rank_graphs[rank_id] = graph

        # If parallel type is data parallel, we can not get stage_devices from proto file.
        if self._parallel_type == SupportedParallelType.DATA_PARALLEL.value:
            if not self._stage_devices:
                self._stage_devices[0] = list()
            self._stage_devices[0].append(rank_id)

    def merge_graph(self):
        """Merge the same stage graphs into a merged graph."""
        for stage, rank_ids in self._stage_devices.items():
            graphs = []
            for rank_id in rank_ids:
                if rank_id not in self._rank_graphs:
                    logger.warning("This rank id(%s) is not found in all the parsed files.", rank_id)
                    continue
                graphs.append(self._rank_graphs[rank_id])

            if not graphs:
                logger.warning("There can not find any graph in stage %s.", stage)
                continue

            merged_graph = MergedGraph()
            merged_graph.merge_graphs(graphs)
            self._stage_merged_graphs[stage] = merged_graph

    @staticmethod
    def _get_stage_devices(tensor_proto):
        stage_devices = {}
        for stage, devices in enumerate(tensor_proto):
            devices = [dim.size for dim in devices.dim]
            stage_devices[stage] = devices
        return stage_devices

    def to_dict(self):
        """Get all merged graphs and the training attributes."""
        graphs = {}
        metadata = dict(
            parallel_type=self._parallel_type
        )
        for stage, merged_graph in self._stage_merged_graphs.items():
            graphs[stage] = merged_graph.to_dict()

        return dict(
            metadata=metadata,
            graphs=graphs
        )
