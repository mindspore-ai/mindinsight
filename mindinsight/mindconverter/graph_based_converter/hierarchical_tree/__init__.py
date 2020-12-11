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
"""Hierarchical tree module."""
__all__ = ["HierarchicalTreeFactory"]

import re

from mindinsight.mindconverter.common.log import logger as log
from .hierarchical_tree import HierarchicalTree
from ..third_party_graph.onnx_graph_node import OnnxGraphNode

from ...common.exceptions import NodeInputMissingError, TreeNodeInsertError


def _tf_model_node_name_reformat(node: OnnxGraphNode, node_name):
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
    if new_name:
        return new_name
    return node_name


class HierarchicalTreeFactory:
    """Hierarchical tree factory."""

    @classmethod
    @TreeNodeInsertError.check_except("Tree node inserts failed.")
    def create(cls, graph):
        """
        Factory method of hierarchical tree.

        Args:
            graph: Graph obj.

        Returns:
            HierarchicalTree, tree.
        """
        tree = HierarchicalTree()
        node_scope_name = dict()
        for _, node_name in enumerate(graph.nodes_in_topological_order):
            node_inst = graph.get_node(node_name)
            node_input = graph.get_input_shape(node_name)
            node_output = graph.get_output_shape(node_name)
            if node_input != 0 and not node_input:
                err_msg = f"This model is not supported now. " \
                          f"Cannot find {node_name}'s input shape."
                error = NodeInputMissingError(err_msg)
                log.error(str(error))
                raise error
            if isinstance(node_inst, OnnxGraphNode):
                node_name_with_scope = _tf_model_node_name_reformat(node_inst, node_name)
                node_scope_name[node_name] = node_name_with_scope
                node_name = node_name_with_scope

            node_inst.add_input_and_output_shape(node_input, node_output)
            tree.insert(node_inst, node_name)

        if node_scope_name:
            return tree, node_scope_name
        return tree
