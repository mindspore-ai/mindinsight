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
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class FlattenMapper(AtenToMindSporeMapper):
    """Flatten mapper."""

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
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = AtenToMindSporeMapper._generate_snippet_template(
            **kwargs)
        raw_params = kwargs.get("raw_params")
        if not raw_params:
            return template, exchange_msg, outputs_list, outputs_mapping

        op = kwargs["operation"]
        weights = kwargs["weights"]
        output_shape = raw_params.get("output_shape")
        args = {"shape": output_shape}

        variable_slot = "var_0"
        target_shape = f"self.{{{variable_slot}}}_shape = tuple({{shape}})"
        init_template = f"self.{{{variable_slot}}} = {op}()"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                             f"self.{{{variable_slot}}}_shape)"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template, target_shape],
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = AtenToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args,
                                                                    weights=weights)
        return template, exchange_msg, outputs_list, outputs_mapping
