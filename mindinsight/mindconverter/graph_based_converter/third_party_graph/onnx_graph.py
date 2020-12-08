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
"""Define ONNX graph."""
from typing import Dict, NoReturn

from mindinsight.mindconverter.common.log import logger as log
from .base import Graph
from .input_node import InputNode
from .onnx_graph_node import OnnxGraphNode
from .tf_graph_parser import TFGraphParser
from .onnx_utils import OnnxDataLoader

NONE_SCOPE_OP = {
    "onnx::Add": "Add",
    "onnx::Flatten": "Flatten",
    "onnx::Concat": "Concat",
    "onnx::Squeeze": "Squeeze",
    "onnx::Unsqueeze": "Unsqueeze",
}


def normalize_node_name(node):
    """
    Rename the node name by removing :0

    Args:
        node (Node, str): ONNX node instance or node name string.

    Returns:
        str, normalized node name.
    """
    if isinstance(node, str):
        return node.split(':')[0]
    return node.name.split(':')[0]


class OnnxGraph(Graph):
    """
    Define ONNX graph.

    Args:
        model (onnx.ModelProto): Onnx defined model proto.
        sample_shape (tuple): Input shape of the model.
    """

    def __init__(self, model, sample_shape: tuple = None, **kwargs):
        super(OnnxGraph, self).__init__(model=model, **kwargs)

        self.build(sample_shape)

    @staticmethod
    def _extract_shape(shape):
        """
        Extract shape from string-type shape.

        Args:
            shape (str): Shape value in string-type.

        Returns:
            list, shape.
        """
        if "," not in shape:
            return []

        shape_arr = []
        for s in shape.split(","):
            s = s.strip()
            if not s:
                return []
            if ":" in s:
                s = s.split(":")[0]
            s = s.replace("!", "")
            if not s.isdigit():
                return []
            shape_arr.append(int(s))
        return shape_arr

    def _build_connection(self, src, tgt) -> NoReturn:
        """
        Build connection between source node and target node.

        Args:
            src (str): Source node name.
            tgt (str): Target node name.
        """
        # If src and tgt are the same node, src not in node_collection or
        # tgt not in node_collection, then skip this edge.
        src = normalize_node_name(src)
        tgt = normalize_node_name(tgt)
        if src == tgt or src not in self._nodes_collection or tgt not in self._nodes_collection:
            if src.split(':')[0] not in self._nodes_collection:
                log.warning(
                    "Graph construct a self-loop node %s. Ignored.", src)
                return
        if tgt not in self._nodes_collection[src.split(':')[0]].successor_nodes:
            self._nodes_collection[src.split(':')[0]].successor_nodes.append(tgt)
        if src not in self._nodes_collection[tgt].precursor_nodes:
            self._nodes_collection[tgt.split(':')[0]].precursor_nodes.append(src)

    def build(self, input_shape=None):
        """
        Build graph tree.

        Args:
            input_shape (tuple): Input shape of model. Default: None
        """
        model_data = OnnxDataLoader(self.model, graph_input_shape=input_shape,
                                    input_nodes=self._raw_input_nodes,
                                    output_nodes=self._raw_output_nodes)
        from ..sub_graph_searcher import generate_scope_name
        scope_name_list = generate_scope_name(model_data)

        self._shape_dict = model_data.node_output_shape_dict
        for ind, (node_name, node) in enumerate(model_data.nodes_dict.items()):
            node_weight = {}
            node.scope_name = scope_name_list[ind]
            inputs = node.input_name_list
            # check each input from node or tensors
            for i in inputs:
                if i in model_data.tensors_dict:
                    tensor = model_data.tensors_dict[i]
                    t_name = tensor.name
                    t_value = tensor.to_array()
                    node_weight[t_name] = t_value
            self._nodes_collection[node_name] = OnnxGraphNode(node, node_weight)
            self._nodes_record[node_name] = node_name

            for nd_ipt_name in node.precursor_onnx_node_dict:
                self._build_connection(nd_ipt_name, node_name)

        super(OnnxGraph, self).build(input_shape=input_shape)
        self._collect_input_shape_of_each_node(input_shape)

    def _collect_input_shape_of_each_node(self, input_shape):
        """
        Collect input tensor shape of each node.

        Args:
            input_shape (tuple): Input shape.
        """
        input_node = InputNode(input_shape)
        input_node_name = self._raw_input_nodes.replace(":0", "")
        for node_name, node in self._nodes_collection.items():
            if node_name in self._input_nodes:
                ipt_nd_name = input_node_name.format(input_node.scope_name)
                input_node.set_scope_name(node.scope_name)
                node.precursor_nodes.insert(0, ipt_nd_name)
                input_node.set_successor_nodes(node_name)
                self._shape_dict[ipt_nd_name] = input_node.output_shape

            ipt_shape = []
            for p_nd in node.precursor_nodes:
                shp = self._shape_dict.get(p_nd)
                ipt_shape.append(tuple(shp) if isinstance(shp, list) else shp)

            self._input_shape[node_name] = ipt_shape[0] if len(
                ipt_shape) == 1 else ipt_shape

    def sub_graph_merging(self):
        raise NotImplementedError()

    @staticmethod
    def load_checkpoint(ckpt_path: str) -> Dict:
        raise NotImplementedError()

    @staticmethod
    def load_metadata(**kwargs):
        raise NotImplementedError()

    @staticmethod
    def load_graph(graph_path: str, **kwargs):
        """
        Load graph.

        Note:
            The input/output nodes are optional for
            tf saved model format. But required for .pb & .ckpt

        Args:
            graph_path (str): Graph path.

        Returns:
            object, ONNX model.
        """
        tf_input_nodes = kwargs.get('input_nodes')
        tf_output_nodes = kwargs.get('output_nodes')
        onnx_model = TFGraphParser.parse(graph_path,
                                         input_nodes=tf_input_nodes,
                                         output_nodes=tf_output_nodes)
        return onnx_model
