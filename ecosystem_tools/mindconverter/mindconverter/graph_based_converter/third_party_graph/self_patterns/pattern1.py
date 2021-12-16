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


class Pattern1(BasePass):
    """
    Pattern mapper.
    Pattern: x.view(x.size, x.size).
    """

    SELF_DEFINED_PATTERN = {
        "op1": {
            "op_type": "size",
            "input": None,
            "output": ["op1"]
        },
        "op2": {
            "op_type": "size",
            "input": None,
            "output": ["op2"]
        },
        "op3": {
            "op_type": "view",
            "input": ["op1", "op2"],
            "output": ["op3"]
        }
    }

    @staticmethod
    def generate_init_template_list(**kwargs):
        return list()

    @staticmethod
    def generate_construct_template_list(**kwargs):
        variable_slot = kwargs["variable_slot"]
        raw_params = kwargs["raw_params"]

        size_params = list()
        view_params = list()

        for param_name, param_value in raw_params.items():
            find_pattern = re.compile(r"(.*)_.*")
            ret = re.findall(find_pattern, param_name)
            if ret:
                op_type = ret[0]
                if op_type == "size":
                    size_params.append({param_name: param_value["inputs"][1]})
                elif op_type == "view":
                    view_params = param_value["inputs"][1]
                else:
                    continue

        input_symbol = ExchangeMessageKeywords.VariableScope.value.INPUTS.value
        input_shape = raw_params.get("input_shape")
        if not isinstance(input_shape, tuple):
            raise ValueError("Can not get input shape from pattern1.")
        template_shape_output = ["_"] * len(input_shape)

        node_output_to_code_output_name = dict()
        for idx, param in enumerate(size_params):
            for param_name, dim in param.items():
                code_output_name = f"x_{idx}"
                template_shape_output[dim] = code_output_name
                node_output_to_code_output_name[raw_params[param_name]["outputs"][0]] = code_output_name
        shape_code = f"{', '.join(template_shape_output)} = {{{input_symbol}}}.shape"

        view_input = [node_output_to_code_output_name.get(param, f"{param}") for param in view_params]
        view_code = f"view({', '.join(view_input)})"

        template_list = [
            shape_code,
            f"{{{input_symbol}}}_ = {{{input_symbol}}}.{view_code}",
            f"opt_{{{variable_slot}}} = {{{input_symbol}}}_"
        ]
        return template_list
