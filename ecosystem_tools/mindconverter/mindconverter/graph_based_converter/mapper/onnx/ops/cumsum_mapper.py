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
"""CumSum mapper module."""
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class CumSumMapper(ONNXToMindSporeMapper):
    """CumSum mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.CumSum"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        exclusive = params.get("exclusive", 0)
        reverse = params.get("reverse", 0)
        exclusive = exclusive == 1
        reverse = reverse == 1
        return {"exclusive": exclusive, "reverse": reverse}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        raw_weights = kwargs.get("weights", list())
        if not op or not raw_weights:
            raise ValueError("Can not get MindSpore operation name.")

        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"

        axis = CumSumMapper._find_val_by_index(0, raw_weights)
        args["axis"] = int(axis)
        init_axis = f"self.{{{variable_slot}}}_axis = {{axis}}"

        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                             f"self.{{{variable_slot}}}_axis)"

        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template, init_axis],
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
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: dict(),
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: dict()
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
