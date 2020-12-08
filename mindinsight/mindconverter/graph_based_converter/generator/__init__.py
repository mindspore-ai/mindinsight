# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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

from .generator import Generator, CodeStruct
from ..common.code_fragment import CodeFragment


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
    new_name = None
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
    for node_name in graph_obj.nodes_in_topological_order:
        node_inst = graph_obj.get_node(node_name)
        node_input = graph_obj.get_input_shape(node_name)
        node_output = graph_obj.get_output_shape(node_name)
        if not node_input:
            raise ValueError("Unable to get the node's inputs from Graph object.")
        node_name_with_scope = _tf_model_node_name_reformat(node_inst, node_name)
        node_name = node_name_with_scope

        node_inst.add_input_and_output_shape(node_input, node_output)
        op_name, params, settings, weights = _convert_params(node_inst, mapper)
        generator_inst.add_node(
            node_name,
            node_instance=node_inst,
            node_fragment=CodeFragment(op_name, params,
                                       settings,
                                       node_inst.input_shape,
                                       node_inst.output_shape,
                                       weights)
        )
    return generator_inst


def _convert_params(node, mapper):
    """
    Call mapper to convert node's params from ONNX to MindSpore.

    Args:
        node (GraphNode): Our defined GraphNode instance.
        mapper (Mapper): The mapper instance which indicating conversion method.

    Returns:
        str, op name in MindSpore
        dict, MindSpore parameters
        dict, MindSpore settings
        dict, weights of the node
    """
    params = copy.deepcopy(node.node_params)
    params.update({"input_shape": node.input_shape,
                   "output_shape": node.output_shape})

    op_in_ms, ms_params, ms_settings, weights = mapper.convert(op_name=node.op_name,
                                                               params=params,
                                                               weights=node.weight)
    if "input_shape" in ms_params:
        ms_params.pop("input_shape")
    if "output_shape" in ms_params:
        ms_params.pop("output_shape")

    if op_in_ms:
        return op_in_ms, ms_params, ms_settings, weights

    return node.op_name, node.node_params, dict(), dict()
