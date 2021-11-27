# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define Pytorch graph."""
from typing import Dict, NoReturn, Mapping

from mindconverter.common.log import MindConverterLogger
from mindconverter.graph_based_converter.constant import UNKNOWN_SHAPE_WITHOUT_PRECURSOR_NODES
from mindconverter.graph_based_converter.sub_graph_searcher.scope_name_rebuilder import \
    rebuild_name_scope_according_to_user_selections
from mindconverter.graph_based_converter.third_party_graph.base import Graph, NodeWeight, NodeOutputShape
from mindconverter.graph_based_converter.third_party_graph.input_node import InputNode
from mindconverter.graph_based_converter.third_party_graph.pytorch_graph_node import PytorchGraphNode
from mindconverter.graph_based_converter.third_party_graph.torch_utils import TENSORTYPE, Pattern
from mindconverter.graph_based_converter.third_party_graph.torch_utils import model_to_graph, \
    PytorchDataLoader
from mindconverter.graph_based_converter.sub_graph_searcher import generate_scope_name


class PytorchGraph(Graph):
    """
    Define Pytorch graph.

    Args:
        model (torch.nn.Module): Pytorch defined model proto.
        input_tensors (tuple<torch.Tensor>): List of input tensor for tracing.
    """

    def __init__(self, model, input_tensors):
        MindConverterLogger.info("Pytorch model loading begins.")
        self._traced_model, self._param_dict = model_to_graph(model, args=input_tensors)
        self._graph = self._traced_model.inlined_graph
        input_names = [ipt.debugName() for ipt in self._graph.inputs() if isinstance(ipt.type(), TENSORTYPE)]
        input_nodes = {name: tuple(tensor.shape) for name, tensor in zip(input_names, input_tensors)}
        MindConverterLogger.info("Pytorch model loading is finished.")

        super(PytorchGraph, self).__init__(model=model, model_path='', input_nodes=input_nodes)
        self.dataloader = PytorchDataLoader(self._traced_model, self._param_dict)
        self._scope_name = None
        self.patterns = Pattern(self.dataloader.nodes_dict).patterns

    def _build_connection(self, src, tgt) -> NoReturn:
        """
        Build connection between source node and target node.

        Args:
            src (str): Source node name.
            tgt (str): Target node name.
        """
        # If src and tgt are the same node, src not in node_collection or
        # tgt not in node_collection, then skip this edge.
        if src == tgt or src not in self._nodes_collection or tgt not in self._nodes_collection:
            if src not in self._nodes_collection:
                MindConverterLogger.warning(f"Graph construct a self-loop node {src}. Ignored.")
                return
        if tgt not in self._nodes_collection[src].successor_nodes:
            self._nodes_collection[src].successor_nodes.append(tgt)
        if src not in self._nodes_collection[tgt].precursor_nodes:
            self._nodes_collection[tgt].precursor_nodes.append(src)

    def generate_scope_name(self, user_operations: Mapping[str, Dict] = None):
        """
        Generate scope names according to user operations or auto-merging.

        Args:
            user_operations (dict): User selections on ui.
        """
        if user_operations:
            self._scope_names = rebuild_name_scope_according_to_user_selections(self.dataloader, user_operations)
        else:
            self._scope_names = generate_scope_name(self.dataloader)

    def build(self):
        """Build graph tree."""
        if self._scope_names is None:
            self.generate_scope_name()

        self._shape_dict = self.dataloader.node_output_shape_dict
        for ind, (node_name, node) in enumerate(self.dataloader.nodes_dict.items()):
            node_weights = list()
            if isinstance(self._scope_names, dict):
                node.scope_name = self._scope_names[node_name]
            else:
                node.scope_name = self._scope_names[ind]
            inputs = node.input_name_list
            fake_inputs = node.fake_input_name_list
            # check each input from node or tensors
            for loc, i in enumerate(inputs):
                if i in self.dataloader.tensors_dict:
                    tensor = self.dataloader.tensors_dict[i]
                    t_name = tensor.name
                    t_value = tensor.to_array()
                    location = fake_inputs.index(t_name) if t_name in fake_inputs else loc
                    node_weights.append(NodeWeight(t_name, t_value, location))
            self._nodes_collection[node_name] = PytorchGraphNode(node, node_weights)
            self._nodes_record[node_name] = node_name

            for nd_ipt_name in node.precursor_onnx_node_dict:
                self._build_connection(nd_ipt_name, node_name)

        super(PytorchGraph, self).build()
        self._collect_input_shape_of_each_node()
        for node_name in self._shape_dict:
            if len(self._shape_dict[node_name]) == 1:
                self._shape_dict[node_name] = self._shape_dict[node_name][0].node_output_shape

    def _collect_input_shape_for_input_nodes(self, node, node_name, input_nodes):
        """Collect input shape for graph input nodes."""
        for ipt in node.ir_node_inputs:
            if ipt not in input_nodes:
                continue
            input_nodes[ipt].set_scope_name(node.scope_name)
            node.precursor_nodes.insert(0, ipt)
            input_nodes[ipt].set_successor_nodes(node_name)
            output_shape_single = NodeOutputShape(ipt, None, input_nodes[ipt].output_shape)
            if ipt not in self._shape_dict:
                self._shape_dict.setdefault(ipt, []).append(output_shape_single)

    def _collect_input_shape_from_precursor_nodes(self, precursor_nodes, ipt_nd_name):
        """Collect input shape from precursor nodes."""
        ipt_shape = list()
        for p_nd in precursor_nodes:
            shp_list = self._shape_dict.get(p_nd)
            for shp in shp_list:
                if ipt_nd_name == shp.node_opt_name:
                    shp_single = shp.node_output_shape
                    ipt_shape.append(tuple(shp_single) if isinstance(shp_single, list) else shp_single)
        return ipt_shape

    def _collect_input_shape_of_each_node(self):
        """Collect input tensor shape of each node."""
        input_nodes = dict()
        for ipt_nd_name, shape in self._raw_input_nodes.items():
            input_nodes[ipt_nd_name] = InputNode(ipt_nd_name, shape)

        for node_name, node in self._nodes_collection.items():
            if node_name in self._input_nodes:
                self._collect_input_shape_for_input_nodes(node, node_name, input_nodes)

            ipt_shape = []
            for ipt_nd_name in node.ir_node_inputs:
                if ipt_nd_name in input_nodes:
                    ipt_shape.append(input_nodes[ipt_nd_name].output_shape)
                    continue

                if node.precursor_nodes:
                    ipt_shape.extend(self._collect_input_shape_from_precursor_nodes(node.precursor_nodes, ipt_nd_name))
                else:
                    ipt_shape.append(UNKNOWN_SHAPE_WITHOUT_PRECURSOR_NODES)

            self._input_shape[node_name] = ipt_shape[0] if len(ipt_shape) == 1 else ipt_shape

    def sub_graph_merging(self):
        raise NotImplementedError

    @staticmethod
    def load_checkpoint(ckpt_path: str) -> dict:
        raise NotImplementedError

    @staticmethod
    def load_metadata(**kwargs):
        raise NotImplementedError

    @staticmethod
    def load_graph(graph_path: str, **kwargs):
        raise NotImplementedError
