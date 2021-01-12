# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
from mindinsight.mindconverter.graph_based_converter.common.utils import reset_init_or_construct
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.mapper.gen_setting import Setting


class ReshapeMapper(ONNXToMindSporeMapper):
    """Reshape mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Reshape"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        if kwargs.get("weights", None):
            return ReshapeMapper._convert_settings_tf(**kwargs)
        return ReshapeMapper._convert_settings_pytorch(**kwargs)

    @staticmethod
    def _convert_settings_pytorch(**kwargs):
        params = kwargs.get("params")
        shape = params.get("output_shape")
        return Setting(op_extra_input={"input_shape": tuple(shape)})

    @staticmethod
    def _convert_settings_tf(**kwargs):
        weights = kwargs.get("weights")
        if len(weights) > 1:
            raise ValueError("For reshape, `weights` length should equal to 1.")
        shape = [-1]
        shape += list(weights.values())[0][1:].tolist()
        return Setting(op_extra_input={"shape": tuple(shape)})

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        weights = kwargs.get("weights")
        if len(weights) > 1:
            raise ValueError("For reshape, `weights` length should equal to 1.")
        shape = [-1]
        shape += list(weights.values())[0][1:].tolist()
        variable_slot = "var_0"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, {tuple(shape)})"
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)

        return template, exchange_msg, outputs_list, outputs_mapping
