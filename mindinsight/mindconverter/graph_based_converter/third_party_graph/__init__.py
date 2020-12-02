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
"""Graph associated definition module."""

__all__ = ["GraphFactory"]
from importlib import import_module

from .base import Graph


class GraphFactory:
    """Graph factory."""

    @classmethod
    def init(cls, graph_path: str,
             sample_shape: tuple,
             input_nodes: str = None, output_nodes: str = None):
        """
        Init an instance of graph.

        Args:
            graph_path (str): Graph or model file path.
            sample_shape (tuple): Input shape of the model.
            input_nodes(str): Input nodes.
            output_nodes(str): Output nodes.

        Returns:
            Graph, graph instance.
        """
        if all([input_nodes, output_nodes]):
            onnx_graph_module = import_module(
                'mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_graph')
            onnx_graph = getattr(onnx_graph_module, 'OnnxGraph')
            return onnx_graph.load(model_path=graph_path, input_nodes=input_nodes,
                                   output_nodes=output_nodes, sample_shape=sample_shape)

        pytorch_graph_module = import_module(
            'mindinsight.mindconverter.graph_based_converter.third_party_graph.pytorch_graph')
        pytorch_graph = getattr(pytorch_graph_module, 'PyTorchGraph')
        return pytorch_graph.load(model_path=graph_path, sample_shape=sample_shape)
