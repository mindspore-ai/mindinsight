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
from mindconverter.graph_based_converter.constant import PYTORCH_MS_MAP, WeightType
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class CastMapper(AtenToMindSporeMapper):
    """Cast mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Cast"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = {
            2: ["input_0", "input_1"],
            5: ["input", "var", "unused", "unused", "unused"],
            6: ["input", "unused", "dtype", "unused", "unused", "unused"],
            8: ["input", "dtype", "unused", "unused", "unused", "unused", "unused", "unused"]
        }
        args_name_list = CastMapper.get_args_name_list(**kwargs, args_name=args_name)
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
        args_name = {
            2: ["input_0", "input_1"],
            5: ["input", "var", "unused", "unused", "unused"],
            6: ["input", "unused", "dtype", "unused", "unused", "unused"],
            8: ["input", "dtype", "unused", "unused", "unused", "unused", "unused", "unused"]
        }
        inputs, args, group_inputs = CastMapper._params_parser(raw_params=raw_params, args_name=args_name,
                                                               trainable_params=trainable_params)
        args = CastMapper._get_args(args=args)

        init_template_list = [f"self.{{{variable_slot}}}_{arg_name} = {{{arg_name}}}" for arg_name in args]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            if CastMapper.is_tensor(value):
                variable_slot_param_name = f"{variable_slot}/{name}"
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)
        args, construct_template = CastMapper._get_construct_template(inputs=inputs, variable_slot=variable_slot, op=op,
                                                                      args=args)
        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, [construct_template], args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_args(**kwargs):
        """Get args from params_parser."""
        args = kwargs.get("args", dict())
        return {arg_name: arg_value for arg_name, arg_value in args.items() if arg_name != "unused"}

    @staticmethod
    def _get_construct_template(**kwargs):
        """Get construct_template according to num_inputs."""
        inputs = kwargs.get("inputs", list())
        variable_slot = kwargs.get("variable_slot")
        op = kwargs.get("op")
        args = kwargs.get("args")

        num_inputs = len(inputs)
        if num_inputs == 2:
            construct_template = f"opt_{{{variable_slot}}} = {op}()({inputs[0]}, {inputs[1]}.dtype)"
        elif num_inputs == 5:
            var = args.get("var")
            if isinstance(var, int):
                args["var"] = PYTORCH_MS_MAP[var] if var != -1 else None
                construct_template = f"opt_{{{variable_slot}}} = {op}()({', '.join(inputs[:2])})"
            else:
                construct_template = f"opt_{{{variable_slot}}} ={op}()({inputs[0]}, {inputs[1]}.dtype)"
        elif num_inputs in [6, 8]:
            dtype = args.get("dtype")
            args["dtype"] = PYTORCH_MS_MAP[dtype] if dtype != -1 else None
            input_dtype = inputs[2] if num_inputs == 6 else inputs[1]
            construct_template = f"opt_{{{variable_slot}}} = {op}()({inputs[0]}, {input_dtype})"
        else:
            raise ValueError(f"Number of inputs should be one of [2, 5, 6, 8], but {num_inputs} is gotten.")
        return args, construct_template
