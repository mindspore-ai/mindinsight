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
from mindconverter.graph_based_converter.constant import FIRST_LEVEL_INDENT, SECOND_LEVEL_INDENT, NEW_LINE, WeightType
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class Im2ColMapper(AtenToMindSporeMapper):
    """Im2Col mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        Im2ColMapper.global_context.hard_template["Im2Col"] = [
            f"class Unfold(nn.Cell):",
            f"{FIRST_LEVEL_INDENT}def __init__(self, paddings, ksizes, strides, rates):",
            f"{SECOND_LEVEL_INDENT}super().__init__()",
            f"{SECOND_LEVEL_INDENT}self.expand_dims = P.ExpandDims()",
            f"{SECOND_LEVEL_INDENT}self.pad = nn.Pad(paddings=paddings)",
            f"{SECOND_LEVEL_INDENT}self.unfold = nn.Unfold(ksizes=ksizes, strides=strides, rates=rates)",
            f"{SECOND_LEVEL_INDENT}self.concat = P.Concat(axis=1)",
            f"{NEW_LINE}",
            f"{FIRST_LEVEL_INDENT}def construct(self, x):",
            f"{SECOND_LEVEL_INDENT}output_list = list()",
            f"{SECOND_LEVEL_INDENT}for c in range(x.shape[1]):",
            f"{SECOND_LEVEL_INDENT}{FIRST_LEVEL_INDENT}output_ = self.expand_dims(x[:, c, :, :], 1)",
            f"{SECOND_LEVEL_INDENT}{FIRST_LEVEL_INDENT}output_ = self.pad(output_)",
            f"{SECOND_LEVEL_INDENT}{FIRST_LEVEL_INDENT}output_ = self.unfold(output_)",
            f"{SECOND_LEVEL_INDENT}{FIRST_LEVEL_INDENT}output_list.append(output_)",
            f"{SECOND_LEVEL_INDENT}output = self.concat(output_list)",
            f"{SECOND_LEVEL_INDENT}return output.reshape(output.shape[0], output.shape[1], -1)",
            f"{NEW_LINE}"
        ]
        return "Unfold"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = ["input", "kernel_size", "dilation", "padding", "stride"]
        args_name_list = Im2ColMapper.get_args_name_list(**kwargs, args_name=args_name)
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
        variable_slot = "var_0"
        trainable_params = kwargs.get("trainable_params", dict())
        args_name = ["input", "kernel_size", "dilation", "padding", "stride"]
        inputs, args, group_inputs = Im2ColMapper._params_parser(raw_params, args_name, trainable_params)

        args = Im2ColMapper._get_args(args=args)
        init_template_list = [f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"]
        parameters_declared = Im2ColMapper.generate_parameters_declared(variable_slot, init_template_list,
                                                                        args, trainable_params)
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}({inputs[0]})"

        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, [construct_template], args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_args(**kwargs):
        """Get args from params_parser"""
        args = kwargs.get("args")
        converted_args = dict()
        converted_args["ksizes"] = tuple([1, *args.get("kernel_size"), 1])
        converted_args["strides"] = tuple([1, *args.get("stride"), 1])
        converted_args["rates"] = tuple([1, *args.get("dilation"), 1])
        padding = args.get("padding")
        converted_args["paddings"] = ((0, 0), (0, 0), (padding[0], padding[0]), (padding[1], padding[1]))
        return converted_args
