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
"""Self-defined Pattern module."""
import re

from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords
from mindconverter.graph_based_converter.third_party_graph.base import BasePass


class Pattern2(BasePass):
    """
    Pattern mapper.
    Pattern:
        ..., x_i,... = x.shape
        y = A[:,...]
        z = y[:,start:x_i + B:stride,...]

        A is constant tensor and B is constant int.
    """

    SELF_DEFINED_PATTERN = {
        "op1": {
            "op_type": "size",
            "input": None,
            "output": ["op1"]
        },
        "op2": {
            "op_type": "add",
            "input": ["op1"],
            "output": ["op2"]
        },
        "op3": {
            "op_type": "slice",
            "input": None,
            "output": ["op3"]
        },
        "op4": {
            "op_type": "slice",
            "input": ["op3", "op2"],
            "output": ["op4"]
        }
    }

    node_output_to_code_output_name = dict()

    input_symbol = ExchangeMessageKeywords.VariableScope.value.INPUTS.value
    output_name_in_pattern = "opt_pattern2"

    @staticmethod
    def generate_init_template_list(**kwargs):
        variable_slot = kwargs["variable_slot"]
        variable_slot_param_name = f"{variable_slot}/pattern_weight_0"
        return [f"self.{{{variable_slot}}}_pattern_weight_0 = {{{variable_slot_param_name}}}"]

    @staticmethod
    def generate_construct_template_list(**kwargs):
        variable_slot = kwargs["variable_slot"]
        raw_params = kwargs["raw_params"]
        weights = kwargs["weights"]

        size_params = dict()
        add_params = dict()
        slice_params = dict()

        for param_name, param_value in raw_params.items():
            find_pattern = re.compile(r"(.*)_.*")
            ret = re.findall(find_pattern, param_name)
            if ret:
                op_type = ret[0]
                if op_type == "size":
                    size_params[param_name] = param_value["inputs"][1]
                elif op_type == "add":
                    add_params = {param_name: param_value["inputs"][:2]}
                elif op_type == "slice":
                    slice_params[param_name] = param_value["inputs"]

        shape_code = Pattern2._gen_size_code(size_params, raw_params)
        add_code = Pattern2._gen_add_code(add_params, raw_params, weights)
        slice_code_list = Pattern2._gen_slice_code_list(slice_params, raw_params, weights, variable_slot)

        template_list = [
            shape_code, add_code, *slice_code_list
        ]
        return template_list

    @classmethod
    def _gen_size_code(cls, size_params, raw_params):
        """Generate code for size."""
        template_shape_output = ["_"] * len(raw_params["input_shape"])
        for param_name, dim in size_params.items():
            code_output_name = cls.output_name_in_pattern
            template_shape_output[dim] = code_output_name
            cls.node_output_to_code_output_name.update({raw_params[param_name]["outputs"][0]: code_output_name})
        shape_code = f"{', '.join(template_shape_output)} = {{{cls.input_symbol}}}.shape"
        return shape_code

    @classmethod
    def _gen_add_code(cls, add_params, raw_params, weights):
        """Generate code for add."""
        add_inputs = list()
        for name, value in add_params.items():
            add_inputs = [cls.node_output_to_code_output_name.get(param, f"{param}") for param in value]

            for idx, ipt in enumerate(add_inputs):
                for weight in weights:
                    if ipt == weight.name:
                        weight_value = weight.value.tolist() if not weight.value.shape else weight.name
                        add_inputs[idx] = f"{weight_value}"

            cls.node_output_to_code_output_name[raw_params[name]["outputs"][0]] = cls.output_name_in_pattern
        add_code = f"{cls.output_name_in_pattern} = {' + '.join(add_inputs)}"
        return add_code

    @classmethod
    def _gen_slice_code_list(cls, slice_params, raw_params, weights, variable_slot):
        """Generate code list for slice."""
        slice_code_list = list()
        for idx, (name, param) in enumerate(slice_params.items()):
            input_code = cls.node_output_to_code_output_name.get(param[0], param[0])
            slice_axis = param[1]

            dim_max = raw_params["input_shape"][slice_axis]
            for weight in weights:
                if input_code == weight.name:
                    dim_max = weight.value.shape[slice_axis]
                    input_code = f"self.{{{variable_slot}}}_pattern_weight_0"

            slice_index = [cls.node_output_to_code_output_name.get(dim, f"{dim}") for dim in param[2:]]
            slice_index[1] = f"{min(int(slice_index[1]), dim_max)}" if slice_index[1].isdigit() else slice_index[1]
            slice_index = ":".join(slice_index)
            slice_index_code = [":"] * (slice_axis + 1)
            slice_index_code[slice_axis] = f"{slice_index}"
            slice_code = f"opt_{{{variable_slot}}} = {input_code}[{', '.join(slice_index_code)}]"\
                if idx == len(slice_params) - 1 else \
                f"{cls.output_name_in_pattern}_slice_{idx} = {input_code}[{', '.join(slice_index_code)}]"
            slice_code_list.append(slice_code)
            cls.node_output_to_code_output_name[raw_params[name]["outputs"][0]] = \
                f"{cls.output_name_in_pattern}_slice_{idx}"
        return slice_code_list
