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
"""Module rocessing for shared weights."""
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.generator.node_struct import NodeStruct
from mindinsight.mindconverter.graph_based_converter.generator.module_struct import ModuleStruct

class SharedWeightHelper:
    """Helper function to process shared weights."""

    @staticmethod
    def check_node_has_shared_weight(node: NodeStruct):
        """
        Check the node has shared weight and return all of them.

        Args:
            node (NodeStruct): NodeStruct instance.

        Returns:
            list, a list of shared weight onnx names
        """
        shared_weight_names = []
        for shared_weight_name, repeated_node_list in GlobalContext().repeated_weights.items():
            if node.onnx_name in repeated_node_list:
                shared_weight_names.append(shared_weight_name)

        return shared_weight_names

    @staticmethod
    def add_shared_weight_to_parent_module(shared_weight_name: str, module_to_be_registered: ModuleStruct):
        """Register the shared weight name to module and assign a local var name for it."""
        default_weight_name = f"passthrough_w_{module_to_be_registered.shared_weights_counter}"
        if shared_weight_name not in module_to_be_registered.shared_weights_collection:
            module_to_be_registered.shared_weights_collection[shared_weight_name] = default_weight_name
        module_to_be_registered.shared_weights_counter += 1

    @staticmethod
    def register_shared_weight_to_public_parent(node: NodeStruct, shared_weight_name: str, pub_module_identifier):
        """
        Register shared weight from bottom to top until its public module.

        Note:
            Now we always consider the public module is main model, since looking for public module among multiple
            nodes consume long time.

        Args:where the shared weight to be used.
            node (NodeStruct): The NodeStruct instance which has the shared weight.
            share_weight_name (str): The onnx name of the shared weights.
            pub_module_identifier (list): The identifier of the public module the shared weight in.
        """
        if not node.fragment.default_var.get(ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value):
            # No weight shared operator, skip
            return
        parent_module = node.parent_module_struct
        exit_flag = False
        while True:
            if parent_module.identifier == pub_module_identifier:
                exit_flag = True
            SharedWeightHelper.add_shared_weight_to_parent_module(shared_weight_name, parent_module)
            parent_module = parent_module.parent_module_struct
            if exit_flag:
                break
            if parent_module is None:
                break

    @staticmethod
    def add_shared_weights_in_init_statement(md_struct: ModuleStruct, module_def_args: list):
        """add shared weights to module init statement."""
        if md_struct.shared_weights_collection:
            return module_def_args + list(md_struct.shared_weights_collection.values())
        return module_def_args

    @staticmethod
    def public_module_shared_weight_statement_generation(public_module: ModuleStruct):
        """Return the statement of declaration of shared weights in its public module."""
        statements = []
        for passthrough_w_onnx_name, passthrough_w_var_name in public_module.shared_weights_collection.items():
            parameter_statement = GlobalContext().repeated_weights_declaration.get(passthrough_w_onnx_name)
            declare_statement = f"self.{passthrough_w_var_name} = {parameter_statement}"
            statements.append(declare_statement)
        return statements
