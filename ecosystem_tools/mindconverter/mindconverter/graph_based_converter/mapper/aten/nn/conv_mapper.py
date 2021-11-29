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


class ConvMapper(AtenToMindSporeMapper):
    """Conv2d mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Conv2d"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = {
            11: ["input", "weight", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled"],
            12: ["input", "weight", "bias", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled"],
            13: ["input", "weight", "bias", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled", "allow_tf32"]
        }
        args_name_list = ConvMapper.get_args_name_list(**kwargs, args_name=args_name)
        trainable_params = dict()
        for weight in weights:
            trainable_params[args_name_list[weight.location]] = {
                "data": weight.value, "location": weight.location,
                "type": WeightType.PARAMETER.value if weight.location == 0 else WeightType.COMMON.value,
                "onnx_name": weight.name
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
            11: ["input", "weight", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled"],
            12: ["input", "weight", "bias", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled"],
            13: ["input", "weight", "bias", "stride", "padding", "dilation", "transposed", "output_padding", "groups",
                 "benchmark", "deterministic", "cudnn_enabled", "allow_tf32"]
        }
        inputs, args, group_inputs = AtenToMindSporeMapper._params_parser(raw_params=raw_params, args_name=args_name,
                                                                          trainable_params=trainable_params)
        args = ConvMapper._get_args(inputs=inputs, args=args, trainable_params=trainable_params)

        init_template_list = [f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            weight_type = trainable_param["type"]
            if ConvMapper.is_tensor(value):
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
        num_inputs = len(kwargs["inputs"])
        args = kwargs.get("args", dict())
        trainable_params = kwargs.get("trainable_params", dict())
        if num_inputs == 12:
            if args.get("bias") and isinstance(args["bias"], (tuple, list)):
                args["groups"] = args.pop("output_padding")
                args["dilation"] = args.pop("padding")
                args["padding"] = args.pop("stride")
                args["stride"] = args.pop("bias")

        weight = trainable_params["weight"]["data"]
        kernel_size = tuple(weight.shape[2:])
        out_channels = weight.shape[0]
        in_channels = weight.shape[1] * args["groups"]
        pad_mode, padding = ConvMapper._convert_padding(args.get("padding"))
        has_bias = "bias" in trainable_params
        return {
            "kernel_size": kernel_size,
            "in_channels": in_channels,
            "out_channels": out_channels,
            "stride": args["stride"],
            "dilation": args["dilation"],
            "padding": padding,
            "pad_mode": pad_mode,
            "group": args["groups"],
            "has_bias": has_bias
        }

    @staticmethod
    def _convert_padding(val):
        """Convert padding from aten to mindspore."""
        if isinstance(val, (tuple, list)):
            if sum(val) == 0:
                return "\'valid\'", 0
            padding = list()
            for num in val:
                padding += [num, num]
            return "\'pad\'", tuple(padding)
        raise ValueError("Conv. mapper get unexpected padding from aten.")
