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


class EmbeddingMapper(AtenToMindSporeMapper):
    """Embedding mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Embedding"

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get("weights", list())
        args_name = ["weight", "input", "padding_idx", "scale_grad_by_freq", "sparse"]
        args_name_list = EmbeddingMapper.get_args_name_list(**kwargs, args_name=args_name)
        trainable_params = dict()
        for weight in weights:
            trainable_params["embedding_table" if weight.location == 0 else args_name_list[weight.location]] = {
                "data": weight.value, "location": weight.location,
                "type": WeightType.COMMON.value if weight.location == 0 else WeightType.PARAMETER.value,
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
        args_name = ["weight", "input", "padding_idx", "scale_grad_by_freq", "sparse"]
        inputs, args, group_inputs = EmbeddingMapper._params_parser(raw_params=raw_params, args_name=args_name,
                                                                    trainable_params=trainable_params)
        args = EmbeddingMapper._get_args(trainable_params=trainable_params, args=args)

        init_template_list = [f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"]
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            weight_type = trainable_param["type"]
            if EmbeddingMapper.is_tensor(value):
                if weight_type == WeightType.PARAMETER.value:
                    variable_slot_param_name = f"{variable_slot}/{name}"
                    init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                    parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)
        construct_template_list = [f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}({inputs[1]})"]
        template, exchange_msg = reset_template_and_exchange_msg(template, exchange_msg, variable_slot,
                                                                 init_template_list, construct_template_list, args,
                                                                 trainable_params, parameters_declared, group_inputs)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_args(**kwargs):
        """Get args from params_parser."""
        trainable_params = kwargs.get("trainable_params", dict())
        args = kwargs.get("args", dict())
        vocab_size, embedding_size = trainable_params.get("embedding_table", dict())["data"].shape
        return {
            "vocab_size": vocab_size,
            "embedding_size": embedding_size,
            "padding_idx": args["padding_idx"] if args["padding_idx"] != -1 else None
        }
