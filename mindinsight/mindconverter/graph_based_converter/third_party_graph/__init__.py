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
"""Graph associated definition module."""

__all__ = ["GraphFactory"]

from typing import List

from mindinsight.mindconverter.graph_based_converter.third_party_graph.base import Graph
from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_graph import OnnxGraph


class GraphFactory:
    """Graph factory."""

    @classmethod
    def init(cls, graph_path: str,
             input_nodes: dict = None, output_nodes: List[str] = None):
        """
        Init an instance of graph.

        Args:
            graph_path (str): Graph or model file path.
            input_nodes (dict): Input nodes.
            output_nodes (list[str]): Output nodes.

        Returns:
            Graph, graph instance.
        """
        if not isinstance(input_nodes, dict):
            raise TypeError("`input_nodes` must be type of dict.")
        if not isinstance(output_nodes, list):
            raise TypeError("`output_nodes` must be type of list.")
        return OnnxGraph.load(model_path=graph_path, input_nodes=input_nodes,
                              output_nodes=output_nodes)
