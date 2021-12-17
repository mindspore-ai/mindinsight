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
import numpy as np
from mindconverter.graph_based_converter.common.utils import reset_template_and_exchange_msg
from mindconverter.graph_based_converter.constant import WeightType
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class NLLLossMapper(AtenToMindSporeMapper):
    """NLLLoss mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.NLLLoss"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        trainable_params = dict()
        args_name = ["input", "labels", "weight", "reduction", "unused"]
        args_name_list = NLLLossMapper.get_args_name_list(**kwargs, args_name=args_name)
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

        weight_shape = raw_params.get("input_shape")[0][-1]
        op = kwargs.get("operation")
        variable_slot = "var_0"
        trainable_params = kwargs.get("trainable_params")
        args_name = ["input", "labels", "weight", "reduction", "unused"]
        inputs, args, group_inputs = NLLLossMapper._params_parser(raw_params, args_name, trainable_params)

        init_template_list = [f"self.{{{variable_slot}}}_{arg_name} = {{{arg_name}}}" for arg_name in args
                              if arg_name not in ["unused", "reduction"]]
        if args.get("weight", 1) is None:
            trainable_params["weight"] = {"data": np.ones(weight_shape, dtype=np.float32),
                                          "location": 2, "type": WeightType.PARAMETER.value}
        if args.get("reduction"):
            args["reduction"] = "mean"
        else:
            args["reduction"] = "sum"
        init_template_list.append(f"self.{{{variable_slot}}} = {op}('{{reduction}}')")
        parameters_declared = NLLLossMapper.generate_parameters_declared(variable_slot, init_template_list,
                                                                         args, trainable_params)
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({inputs[0]}, {inputs[1]}, {inputs[2]})[0]"

        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, [construct_template], args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping
