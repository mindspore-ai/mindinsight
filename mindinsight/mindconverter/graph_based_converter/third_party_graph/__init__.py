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
from .base import Graph
from .pytorch_graph import PyTorchGraph
from .pytorch_graph_node import PyTorchGraphNode


class GraphFactory:
    """Graph factory."""

    @classmethod
    def init(cls, graph_path: str, sample_shape: tuple, checkpoint: str = None):
        """
        Init an instance of graph.

        Args:
            graph_path (str): Graph or model file path.
            sample_shape (tuple): Input shape of the model.
            checkpoint (str): Checkpoint file path.

        Returns:
            Graph, graph instance.
        """
        if checkpoint:
            pass

        return PyTorchGraph.load(model_path=graph_path, sample_shape=sample_shape)


__all__ = [
    "GraphFactory",
    "PyTorchGraphNode",
]
