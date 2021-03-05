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
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class SplitMapper(ONNXToMindSporeMapper):
    """Split mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Split"

    @staticmethod
    def _convert_params(**kwargs):
        axis = kwargs["params"]["axis"]
        output_shape_list = kwargs["params"]["output_shape"]
        output_num = len(output_shape_list)
        return {"axis": axis,
                "output_num": output_num}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        if not op:
            raise ValueError("Can not get MindSpore operation name.")
        converted_params = kwargs["converted_params"]
        output_num = converted_params["output_num"]

        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"
        slot_list = [f"opt_{{{variable_slot}}}"]
        for i in range(1, output_num): # Here `1` means the second output of the operator
            slot_list.append(f"opt_{{{variable_slot}}}_{i}")
        slot_final = ", ".join(slot_list)
        construct_template = f"{slot_final} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template],
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = {
            variable_slot: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: op,
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: args,
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: weights,
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: {}
            }
        }
        outputs_list = slot_list
        outputs_mapping = []
        for i in range(output_num):
            outputs_mapping.append((i, i))
        outputs_mapping = tuple(outputs_mapping)
        return template, exchange_msg, outputs_list, outputs_mapping
