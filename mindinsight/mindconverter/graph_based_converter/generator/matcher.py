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
"""Processing the node's and modules' inputs and outputs matching."""
from mindinsight.mindconverter.graph_based_converter.generator.node_struct import NodeStruct
from mindinsight.mindconverter.graph_based_converter.generator.module_struct import ModuleStruct
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext

class MatcherHelper:
    """
    Helper function for matching processing.
    """
    @staticmethod
    def main_model_special_process_inputs(main_model: ModuleStruct):
        """Call in preprocess"""
        # allocate main model construct x
        prec_edges = main_model.external_precursor_nodes_names
        graph_inputs = GlobalContext().onnx_graph_info.get('graph_inputs')
        inputs = dict()
        for edge in graph_inputs:
            if not edge in inputs and edge in prec_edges:
                regular_edge = MatcherHelper.regular_edge_name(edge)
                inputs[edge] = regular_edge
        main_model.inputs_register = inputs

    @staticmethod
    def regular_edge_name(name: str) -> str:
        """Regular the edge name to adapt the python grammar."""
        regular = ""
        for char in name:
            if char.isalpha() or char.isdigit():
                regular = f"{regular}{char}"
            else:
                regular = f"{regular}_"
        if not regular[0].isalpha():
            regular = f"auto_legalized__{regular}"
        return regular

    @staticmethod
    def get_public_parent_module(node_a: NodeStruct, node_b: NodeStruct):
        """Return the public parent module of both Node A and Node B."""
        find = False
        b_onnx_name = node_b.onnx_name
        tmp = node_a
        while not find:
            parent_struct = tmp.parent_module_struct
            if b_onnx_name in parent_struct.onnx_names:
                find = True
            tmp = parent_struct
        return tmp

    @staticmethod
    def get_submodule_has_out_user_under_public_parent(public_module: ModuleStruct, node_out_user: NodeStruct):
        """Return the ModuleStruct which under the public module and contains the NodeStruct which provided."""
        for module_struct in public_module.module_structs:
            if node_out_user.onnx_name in module_struct.onnx_names:
                return module_struct
        return None

    @staticmethod
    def register_outputs_to_main_model(output_edge_name: str, output_edge_provider: NodeStruct):
        """
        Register the output edge to the main model and through all modules.

        Args:
            output_edge_name (str): The name of this output edge.
            output_edge_provider (NodeStruct): The node which produces this output.
        """
        base_out = output_edge_provider.outputs_manager.get_base_out(output_edge_name)
        nd_parent = output_edge_provider.parent_module_struct
        while nd_parent:
            nd_parent.add_outputs_edge(base_out.onnx_edge_name)
            nd_parent = nd_parent.parent_module_struct

    @staticmethod
    def register_inputs_to_main_model(input_edge_name: str, input_edge_user: NodeStruct):
        """
        Register the input edge to the main model and through all modules.

        Args:
            input_edge_name (str): The name of this input edge.
            input_edge_user (NodeStruct): The node uses this input.
        """
        nd_parent = input_edge_user.parent_module_struct
        while nd_parent:
            nd_parent.add_inputs_edge(input_edge_name)
            nd_parent = nd_parent.parent_module_struct


class MatcherLauncher:
    """Process Node-to-Node inputs outputs matching."""
    def __init__(self, main_model: ModuleStruct):
        super(MatcherLauncher).__init__()
        self.main_model = main_model
        self._global_context = GlobalContext()
        self._graph_inputs = self._global_context.onnx_graph_info.get("graph_inputs")
        self._graph_outputs = self._global_context.onnx_graph_info.get("graph_outputs")

    def matching_process(self):
        """The matching process."""
        # 0. Pre-process
        MatcherHelper.main_model_special_process_inputs(self.main_model)

        # 1. Set all module's return dict
        self._register_module_inputs_x_header()

        # 2. Set module returns
        self._register_module_returns()


    def _register_module_inputs_x_header(self):
        """Recursively register the inputs to module init header."""
        # Use nearest parent module algorithm
        for nd_struct in self._global_context.node_struct_collections.values():
            if not nd_struct.precursor_nodes_names_external:
                # has no precursor nodes but need check if inputs are graph level inputs
                has_graph_input = False
                for edge in nd_struct.inputs_edges_names:
                    if edge in self._global_context.onnx_graph_info.get('graph_inputs'):
                        has_graph_input = True
                        break
                if not has_graph_input:
                    continue # avoid unnecessary checking

            for inp in nd_struct.inputs_edges_names:
                if inp in self._global_context.onnx_graph_info.get('graph_inputs'):
                    # when the input edge is from graph level.
                    MatcherHelper.register_inputs_to_main_model(inp, nd_struct)
                    continue
                out_provider_onnx_name = self._global_context.outputs_storage.onnx_name(inp)
                out_provider_struct = \
                    self._global_context.onnx_node_name_to_node_struct_map.get(out_provider_onnx_name)
                if out_provider_struct is None:
                    raise ValueError(f"The Matcher detected an output has unknown provider for the edge {inp}")
                public_parent = MatcherHelper.get_public_parent_module(nd_struct, out_provider_struct)
                nd_parent = nd_struct.parent_module_struct
                # Recursively register x in all parents until the public module
                while public_parent.identifier != nd_parent.identifier:
                    nd_parent.add_inputs_edge(inp)
                    nd_parent = nd_parent.parent_module_struct


    def _register_module_returns(self):
        """Recursively register the node outputs to parent modules."""
        # Use nearest parent module algorithm
        for nd_struct in self._global_context.node_struct_collections.values():
            if not nd_struct.successor_nodes_names_external:
                # check if any edge to graph output
                has_graph_output = False
                for edge in nd_struct.fragment.metadata.get('outputs'):
                    if edge in self._global_context.onnx_graph_info.get('graph_outputs'):
                        has_graph_output = True
                        break
                if not has_graph_output:
                    continue # avoid unnecessary checking
            for base_out in nd_struct.outputs_manager.outputs:
                if base_out.onnx_edge_name in self._global_context.onnx_graph_info.get('graph_outputs'):
                    MatcherHelper.register_outputs_to_main_model(base_out.onnx_edge_name, nd_struct)
                    continue
                out_user_onnx_names = base_out.onnx_user
                for out_user_onnx_name in out_user_onnx_names:
                    out_user_struct = \
                        self._global_context.onnx_node_name_to_node_struct_map.get(out_user_onnx_name)
                    if out_user_struct is None:
                        raise ValueError(f"The Matcher detected an output has unknown provider for the edge "\
                                         f"{base_out.onnx_edge_name}")
                    public_parent = MatcherHelper.get_public_parent_module(nd_struct, out_user_struct)
                    nd_parent = nd_struct.parent_module_struct
                    # Recursively register outputs to parents until the public module
                    while public_parent.identifier != nd_parent.identifier:
                        nd_parent.add_outputs_edge(base_out.onnx_edge_name)
                        nd_parent = nd_parent.parent_module_struct
    