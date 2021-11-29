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


class LayerNormMapper(AtenToMindSporeMapper):
    """LayerNorm mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.LayerNorm"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = {
            5: ["input", "normalized_shape", "weight", "eps", "cudnn_enable"],
            6: ["input", "normalized_shape", "weight", "bias", "eps", "cudnn_enable"]
        }
        args_name_list = LayerNormMapper.get_args_name_list(**kwargs, args_name=args_name)
        trainable_params = dict()
        for weight in weights:
            if weight.location == 2:
                ms_weight_name = "gamma"
                weight_type = WeightType.COMMON.value
            elif weight.location == 3 and "bias" in args_name_list:
                ms_weight_name = "beta"
                weight_type = WeightType.COMMON.value
            else:
                ms_weight_name = args_name_list[weight.location]
                weight_type = WeightType.PARAMETER.value
            trainable_params[ms_weight_name] = {
                "data": weight.value, "location": weight.location, "type": weight_type, "onnx_name": weight.name
            }
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
        args_name = {
            5: ["input", "normalized_shape", "weight", "eps", "cudnn_enable"],
            6: ["input", "normalized_shape", "weight", "bias", "eps", "cudnn_enable"]
        }
        inputs, args, group_inputs = LayerNormMapper._params_parser(raw_params=raw_params, args_name=args_name,
                                                                    trainable_params=trainable_params)
        args = LayerNormMapper._get_args(args=args)

        init_template_list = [f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            weight_type = trainable_param["type"]
            if LayerNormMapper.is_tensor(value):
                if weight_type == WeightType.PARAMETER.value:
                    variable_slot_param_name = f"{variable_slot}/{name}"
                    init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                    parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)
        construct_template_list = [f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}({inputs[0]})"]
        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, construct_template_list, args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_args(**kwargs):
        """Get args from params_parser."""
        args = kwargs.get("args", dict())
        normalized_shape = args["normalized_shape"]
        return {
            "normalized_shape": (normalized_shape,) if isinstance(normalized_shape, int) else normalized_shape,
            "epsilon": args["eps"]
        }
