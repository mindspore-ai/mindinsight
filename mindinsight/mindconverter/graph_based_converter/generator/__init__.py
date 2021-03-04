# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Generator module."""
__all__ = ["batch_add_nodes"]

import re
import copy

from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords
from mindinsight.mindconverter.graph_based_converter.common.code_fragment import NewFragment
from mindinsight.mindconverter.graph_based_converter.common.outputs import NodeOutputManager
from mindinsight.mindconverter.graph_based_converter.generator.generator import Generator


def _tf_model_node_name_reformat(node, node_name):
    """
    Rename the node name by combining scope name and its original name.

    Args:
        node (OnnxGraphNode): OnnxGraphNode instance.
        node_name (str): node name saved in Graph.

    Returns:
        str, re-formatted node name.
    """
    scope_name = node.scope_name
    regex = r"(?P<parent>.+/)(?P<op>\w+)"
    match = re.match(regex, scope_name)
    parent = match.group("parent")
    node_name = '$' + node_name.replace('/', '::') + '$'

    if scope_name:
        new_name = parent + node_name
        return new_name
    return node_name


def batch_add_nodes(graph_obj, mapper) -> Generator:
    """
    Add nodes to Generator in batch mode.

    Args:
        graph_obj (Graph): Graph obj.
        mapper (Mapper): Mapper of third party framework and MindSpore.

    """
    generator_inst = Generator()
    external_inputs = graph_obj.user_provided_input_nodes
    for node_name in graph_obj.nodes_in_topological_order:
        node_inst = graph_obj.get_node(node_name)
        node_input = graph_obj.get_input_shape(node_name)
        node_output = graph_obj.get_output_shape(node_name)
        if not node_input:
            raise ValueError("Unable to get the node's inputs from Graph object.")
        node_name_with_scope = _tf_model_node_name_reformat(node_inst, node_name)
        node_name = node_name_with_scope

        node_inst.add_input_and_output_shape(node_input, node_output)
        code_template, exchange_msg, outputs_lst, outputs_mapping = _convert_params(node_inst, mapper, external_inputs)
        outputs_mapping = NodeOutputManager(node_name, output_mappings=outputs_mapping)
        fragment = NewFragment(data_entity=exchange_msg, code_template=code_template,
                               outputs=outputs_lst, outputs_mapping=outputs_mapping)
        generator_inst.add_node(node_name, node_instance=node_inst, node_fragment=fragment)
    return generator_inst


def _supply_graph_info(node, external_inputs):
    """
    Supply IR graph node info into metadata.

    Args:
        node (GraphNode): Graph node instance.
        external_inputs (list[str]): External inputs in ONNX ir.

    Returns:
        dict, metadata.
    """
    precursors = _combine_external_inputs_with_precursor_nodes(node, external_inputs)
    return {
        ExchangeMessageKeywords.MetadataScope.value.SOURCE.value: node.ir_node_name,
        ExchangeMessageKeywords.MetadataScope.value.OPERATION.value: node.ir_node_operation,
        ExchangeMessageKeywords.MetadataScope.value.SCOPE.value: node.scope_name,
        ExchangeMessageKeywords.MetadataScope.value.INPUTS.value: node.ir_node_inputs,
        ExchangeMessageKeywords.MetadataScope.value.INPUTS_SHAPE.value: node.input_shape,
        ExchangeMessageKeywords.MetadataScope.value.OUTPUTS.value: node.ir_node_outputs,
        ExchangeMessageKeywords.MetadataScope.value.OUTPUTS_SHAPE.value: node.output_shape,
        ExchangeMessageKeywords.MetadataScope.value.PRECURSOR.value: precursors,
        ExchangeMessageKeywords.MetadataScope.value.SUCCESSOR.value: node.ir_node_successor,
        ExchangeMessageKeywords.MetadataScope.value.ATTRS.value: node.node_params,
    }


def _convert_params(node, mapper, external_inputs):
    """
    Call mapper to convert node's params from ONNX to MindSpore.

    Args:
        node (GraphNode): Our defined GraphNode instance.
        mapper (Mapper): The mapper instance which indicating conversion method.
        external_inputs (list[str]): External inputs provided by users.

    Returns:
        tuple[str, dict, dict, dict], op name in MindSpore, MindSpore parameters,
        MindSpore settings and weights of the node.
    """
    params = copy.deepcopy(node.node_params)
    params.update({"input_shape": node.input_shape,
                   "output_shape": node.output_shape})

    code_template, exchange_msg, outputs_lst, outputs_order_mapping = mapper.convert(op_name=node.op_name,
                                                                                     params=params,
                                                                                     weights=node.weight)
    exchange_msg[ExchangeMessageKeywords.METADATA.value] = _supply_graph_info(node, external_inputs)
    outputs_order_mapping = _bind_outputs_edges(exchange_msg=exchange_msg, outputs_order_mapping=outputs_order_mapping)
    return code_template, exchange_msg, outputs_lst, outputs_order_mapping


def _combine_external_inputs_with_precursor_nodes(node, external_inputs):
    """
    User_provided_input_nodes.

    Args:
        node (OnnxGraphNode): Node instance.
        external_inputs (list[str]): Inputs in onnx ir.

    Returns:
        list[str], precursor nodes list.
    """
    inputs = set(node.ir_node_inputs)
    to_be_added = list(inputs & set(external_inputs))
    precursor = node.ir_node_precursor
    # Add external inputs to precursor as the order of its inputs.
    for item in to_be_added:
        node_idx = node.ir_node_inputs.index(item)
        precursor.insert(node_idx, item)
    return precursor

def _bind_outputs_edges(exchange_msg, outputs_order_mapping):
    """
    Bind the outputs edges names with the outputs order mapping.

    Args:
        exchange_msg (dict): The dict of exchange messages of this node.
        outputs_order_mapping (tuple): The outputs mapping of this node.

    returns,
        zip, the zip object of both edges and mapping
    """
    outputs_edges = exchange_msg.get('metadata').get('outputs')
    if not outputs_edges:
        raise ValueError(f"ONNX Node {exchange_msg.get('metadata').get('source')} has no outputs info.")
    if len(outputs_edges) != len(outputs_order_mapping):
        raise ValueError(f"ONNX Node {exchange_msg.get('metadata').get('source')} has inconsistent " \
                         f"outputs edge number and mapping number")
    return zip(outputs_edges, outputs_order_mapping)
