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
"""Define PyTorch graph."""
import warnings
import re
from typing import Dict, NoReturn

import torch
from torch.nn import Module
from torch.onnx import OperatorExportTypes

from .base import Graph
from .input_node import InputNode
from .pytorch_graph_node import PyTorchGraphNode
from .graph_parser import PyTorchGraphParser
from .torch_utils import OverloadTorchModuleTemporarily, unique_state_dict
from .torch_utils import create_autograd_variable
from .torch_utils import onnx_tracer
from ..hierarchical_tree import HierarchicalTree
from ..constant import SEPARATOR_IN_SCOPE, LINK_IN_SCOPE
from ..constant import LEFT_BUCKET, RIGHT_BUCKET

NONE_SCOPE_OP = {
    'onnx::Add': 'Add',
    'onnx::Flatten': 'Flatten',
}


def normalize_scope_name(node):
    """
    Rename scope name into uniform.

    Args:
        node (Node): PyTorch node.

    Returns:
        str, normalized scope name.
    """
    global NONE_SCOPE_OP

    name = node.scopeName().split(SEPARATOR_IN_SCOPE)
    scopes = []
    for segment in name:
        segment = segment.split(LINK_IN_SCOPE)[0]
        left = segment.find(LEFT_BUCKET)
        right = segment.find(RIGHT_BUCKET)
        if left != -1:
            if segment[left + 1: right].isdigit():
                scopes.append(f"{segment[:left]}_{segment[left + 1: right]}")
            else:
                scopes.append(segment[left + 1: right])
        else:
            scopes.append(segment)
    if node.kind() in NONE_SCOPE_OP.keys():
        scopes.append(NONE_SCOPE_OP[node.kind()])
    return f"{SEPARATOR_IN_SCOPE.join(scopes)}_{PyTorchGraph.get_node_id(node)}"


class PyTorchGraph(Graph):
    """
    Define PyTorch graph.

    Args:
        model (Module): PyTorch model.
        sample_shape (tuple): Input shape of the model.

    """

    def __init__(self, model: Module, sample_shape: tuple):
        super(PyTorchGraph, self).__init__(model=model)
        self._params_dict = unique_state_dict(model)
        self.build(sample_shape)

    @staticmethod
    def _check_input_shape(input_shape):
        """
        Check input shape.

        Args:
            input_shape (tuple): Input tensor shape.

        """
        if not input_shape:
            raise ValueError("`input_shape` can not be None.")

        for item in input_shape:
            if not isinstance(item, int):
                raise ValueError(f"Only support model with one input now, "
                                 f"and each shape value in `input_shape` should be int.")

    def build(self, input_shape):
        """
        Build graph tree.

        Args:
            input_shape (tuple): Input shape of model.

        """
        self._check_input_shape(input_shape)

        def _extract_shape(shape):
            return [int(x.split(":")[0].replace("!", "")) for x in shape.split(',')]

        feed_forward_ipt_shape = (1, *input_shape)
        batched_sample = create_autograd_variable(torch.rand(*feed_forward_ipt_shape))

        # Assign execution mode to eval.
        self.model.eval()

        with OverloadTorchModuleTemporarily() as _:
            # In pytorch higher version, trace function has a known.
            graph = onnx_tracer(self.model, batched_sample,
                                OperatorExportTypes.ONNX)

        nodes = list(graph.nodes())

        for node in nodes:
            node_name = normalize_scope_name(node)
            output_shape_str_list = re.findall(r'[^()!]+', str(node))
            output_shape_str = output_shape_str_list[1]
            output_shape = _extract_shape(output_shape_str)
            weight_scope = '.'.join(
                re.findall(r'\[([\w\d.]+)\]', node.scopeName())
            )
            node_weight = {}
            for scope, weight in self._params_dict.items():
                split_scope = scope.split('.')
                if '.'.join(split_scope[:-1]) == weight_scope:
                    node_weight[split_scope[-1]] = weight
            self._shape_dict[node_name] = output_shape
            self._nodes_collection[node_name] = PyTorchGraphNode(node, node_weight)
            self._nodes_record[node_name] = node_name

            for node_input in list(node.inputs()):
                # Connect input node and src node.
                if PyTorchGraph.get_node_id(node_input.node()) and node_input.node().scopeName():
                    node_input_name = normalize_scope_name(
                        node_input.node()
                    )
                    self.build_connection(node_input_name, node_name)

        super(PyTorchGraph, self).build(input_shape=input_shape)

        # Add Input Node
        input_node = InputNode(input_shape)
        for node_name, node in self._nodes_collection.items():
            if node_name in self._input_nodes:
                input_node.set_scope_name(node.scope_name)
                node.precursor_nodes.append(input_node.scope_name)
                input_node.set_successor_nodes(node_name)
                self._nodes_collection[input_node.scope_name] = input_node
                self._input_shape[node_name] = feed_forward_ipt_shape
                break

    def sub_graph_merging(self):
        """
        Merge split operation into one.
        """
        raise NotImplementedError()

    def to_ir(self, mapper):
        """
        Convert graph to IR graph.
        """
        raise NotImplementedError()

    def to_hierarchical_tree(self):
        """
        Generate hierarchical tree based on graph.
        """
        tree = HierarchicalTree()
        node_input = None
        for _, node_name in enumerate(self.nodes_in_topological_order):
            node_inst = self.get_node(node_name)
            node_output = self._shape_dict.get(node_name)
            if node_inst.in_degree == 0:
                # If in-degree equals to zero, then it's a input node.
                continue

            # If the node is on the top, then fetch its input
            # from input table.
            if not node_input:
                node_input = self._input_shape.get(node_name)

            if not node_input:
                raise ValueError(f"Cannot find {node_name}'s input shape.")

            tree.insert(node_inst, node_name, node_input, node_output)
            node_input = node_output
        return tree

    def build_connection(self, src, tgt) -> NoReturn:
        """
        Build connection between source node and target node.

        Args:
            src (str): Source node name.
            tgt (str): Target node name.

        """
        # If src and tgt are the same node, src not in node_collection or
        # tgt not in node_collection,
        # then skip this edge.
        if src == tgt or src not in self._nodes_collection or tgt not in self._nodes_collection:
            if src.split(':')[0] not in self._nodes_collection:
                warnings.warn(f"Graph construct a self-loop node {src}. Ignored.")
                return

        if tgt not in self._nodes_collection[src.split(':')[0]].successor_nodes:
            self._nodes_collection[src.split(':')[0]].successor_nodes.append(tgt)
        if src not in self._nodes_collection[tgt].precursor_nodes:
            self._nodes_collection[tgt.split(':')[0]].precursor_nodes.append(src)

    @staticmethod
    def load_checkpoint(ckpt_path: str) -> Dict:
        """
        Load checkpoint.

        Args:
            ckpt_path (str):  Checkpoint file path.

        Returns:
            dict, weights in model.
        """

    @staticmethod
    def load_metadata(**kwargs):
        """
        Load graph metadata.
        """
        raise NotImplementedError("class `PyTorchGraph` has not implemented "
                                  "`load_metadata()`.")

    @staticmethod
    def load_graph(graph_path: str):
        """
        Load graph.

        Args:
            graph_path (str): Graph path.

        Returns:
            object, pytorch model.
        """
        torch_model = PyTorchGraphParser.parse(graph_path)
        return torch_model

    @staticmethod
    def get_node_id(node):
        """
        Get node id using regular expr.

        Args:
            node (Node): PyTorch node.

        Returns:
            str, node id.
        """
        node_id = re.search(r"[\d]+", str(node))
        return node_id.group()
