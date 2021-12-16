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
from mindconverter.graph_based_converter.constant import WeightType, PYTORCH_MS_MAP
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class SumMapper(AtenToMindSporeMapper):
    """Sum mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "sum"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = {
            2: ["input", "dtype"],
            4: ["input", "axis", "keepdim", "dtype"]
        }
        args_name_list = SumMapper.get_args_name_list(**kwargs, args_name=args_name)
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

        trainable_params = kwargs.get("trainable_params", dict())

        variable_slot = "var_0"
        args_name = {
            2: ["input", "dtype"],
            4: ["input", "axis", "keepdim", "dtype"]
        }
        inputs, args, group_inputs = SumMapper._params_parser(raw_params=raw_params,
                                                              args_name=args_name,
                                                              trainable_params=trainable_params)

        dtype = args.get("dtype")
        args["dtype"] = dtype if dtype is None else PYTORCH_MS_MAP[dtype]
        init_template_list = [f"self.{{{variable_slot}}}_{arg_name} = {{{arg_name}}}" for arg_name in args]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            if SumMapper.is_tensor(value):
                variable_slot_param_name = f"{variable_slot}/{name}"
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)

        if len(inputs) == 2:
            construct_template = f"opt_{{{variable_slot}}} = ms_np.sum({inputs[0]}, " \
                                 f"dtype=self.{{{variable_slot}}}_dtype)"
        elif len(inputs) == 4:
            construct_template = f"opt_{{{variable_slot}}} = ms_np.sum({' ,'.join(inputs[:2])}, " \
                                 f"dtype=self.{{{variable_slot}}}_dtype, " \
                                 f"keepdims=self.{{{variable_slot}}}_keepdim)"
        else:
            raise ValueError(
                f"For SumMapper, number of params is required in [2,4], but {len(inputs)} is gotten."
            )

        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, [construct_template], args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping
