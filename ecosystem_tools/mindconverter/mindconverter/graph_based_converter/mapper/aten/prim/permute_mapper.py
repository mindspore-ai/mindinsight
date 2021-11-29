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
"""Mapper module."""
from mindconverter.graph_based_converter.common.utils import reset_template_and_exchange_msg
from mindconverter.graph_based_converter.constant import WeightType
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class PermuteMapper(AtenToMindSporeMapper):
    """Permute mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "transpose"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = ["input", "dims"]
        args_name_list = PermuteMapper.get_args_name_list(**kwargs, args_name=args_name)
        trainable_params = dict()
        for weight in weights:
            trainable_params[args_name_list[weight.location]] = {"data": weight.value, "location": weight.location,
                                                                 "type": WeightType.PARAMETER.value,
                                                                 "onnx_name": weight.name}
        return trainable_params

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = AtenToMindSporeMapper._generate_snippet_template(
            **kwargs)
        raw_params = kwargs.get("raw_params")
        if not raw_params:
            return template, exchange_msg, outputs_list, outputs_mapping

        op = kwargs.get("operation")
        trainable_params = kwargs.get("trainable_params", dict())

        variable_slot = "var_0"
        args_name = ["input", "dims"]
        inputs, args, group_inputs = PermuteMapper._params_parser(raw_params=raw_params, args_name=args_name,
                                                                  trainable_params=trainable_params)

        init_template_list = [f"self.{{{variable_slot}}}_{arg_name} = {{{arg_name}}}" for arg_name in args]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            if PermuteMapper.is_tensor(value):
                variable_slot_param_name = f"{variable_slot}/{name}"
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)
        construct_template = PermuteMapper._get_construct_template(variable_slot=variable_slot, op=op, inputs=inputs)

        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, [construct_template], args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_construct_template(**kwargs):
        """Get construct_template from params_parser."""
        variable_slot = kwargs.get("variable_slot")
        op = kwargs.get("op")
        inputs = kwargs.get("inputs", list())
        shape_template = f"({', '.join(inputs[1:])})" if len(inputs[1:]) > 1 else f"{inputs[1]}"
        construct_template = f"opt_{{{variable_slot}}} = {inputs[0]}.{op}(*{shape_template})"
        return construct_template
