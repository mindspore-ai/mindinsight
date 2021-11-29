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


class ShapeMapper(AtenToMindSporeMapper):
    """Shape mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Shape"

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

        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        trainable_params = kwargs.get("trainable_params", dict())
        dim = raw_params["constant_1"]

        variable_slot = "var_0"
        construct_template = f"opt_{{{variable_slot}}} = {op}()" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})[{dim}]"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: list(),
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = AtenToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args,
                                                                    weights=weights, trainable_params=trainable_params)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
