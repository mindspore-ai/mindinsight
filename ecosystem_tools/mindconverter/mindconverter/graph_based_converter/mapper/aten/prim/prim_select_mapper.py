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


class PrimSelectMapper(AtenToMindSporeMapper):
    """Prim Select mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "PrimOp"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        raw_params = kwargs.get("raw_params")
        if not raw_params:
            return AtenToMindSporeMapper._generate_snippet_template(**kwargs)

        dim = raw_params.get("constant_1", 0)
        index = raw_params.get("constant_2", 0)

        input_shape = raw_params.get("input_shape")
        construct_selected = [":"] * len(input_shape)
        construct_selected[dim] = f"{index}"
        construct_selected_str = ", ".join(construct_selected)

        variable_slot = "var_0"
        construct_template = f"opt_{{{variable_slot}}} = " \
                             f"{{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}[{construct_selected_str}]"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: list(),
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = PrimSelectMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
