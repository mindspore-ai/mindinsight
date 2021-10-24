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
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, \
    TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class ClipMapper(ONNXToMindSporeMapper):
    """Clip mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.clip_by_value"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation").replace("onnx::", "onnx.")
        weights = kwargs.get("weights")
        if not op:
            raise ValueError("Can not get MindSpore operation name.")
        min_val = ClipMapper._find_val_by_index(0, weights).tolist()
        max_val = ClipMapper._find_val_by_index(1, weights).tolist()

        variable_slot = "var_0"
        args = {"min": min_val, "max": max_val}

        min_val_decl_stmt = f"self.{{{variable_slot}}}_min = {{min}}"
        max_val_decl_stmt = f"self.{{{variable_slot}}}_max = {{max}}"

        construct_template = f"opt_{{{variable_slot}}} = {op}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                             f"self.{{{variable_slot}}}_min, self.{{{variable_slot}}}_max)"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [min_val_decl_stmt, max_val_decl_stmt],
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
