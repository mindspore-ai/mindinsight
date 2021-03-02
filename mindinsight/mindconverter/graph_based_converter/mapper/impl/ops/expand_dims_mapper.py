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
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class ExpandDimsMapper(ONNXToMindSporeMapper):
    """Expand_dims mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.ExpandDims"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get('operation')
        args = kwargs.get('converted_params', dict())
        params = kwargs['raw_params']  # opset 11, axes is in attributes, and is a list.
        weights = kwargs.get('weights')  # opset 12, axes is in inputs and is a tensor.

        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        if weights:
            axes = ExpandDimsMapper._find_val_by_index(0, weights).tolist()
        else:
            axes = params['axes']

        variable_slot = 'var_0'
        init_template_list = [f"self.{{{variable_slot}}} = {op}()"]

        construct_template_list = list()
        # Type of `axes` in torch operator `Unsqueeze` is list,
        # while type of `axis` in MindSpore operator `ExpandDims` is int.
        # As a result, if length of `axes` is 1, one operator in MindSpore is required to replace that in torch,
        # otherwise, a set of operators in MindSpore are required to replace this operator in torch.
        if len(axes) == 1:
            args["axis"] = axes[0]
            init_template_list.append(f"self.{{{variable_slot}}}_axis = {{axis}}")
            construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                                 f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                                 f"self.{{{variable_slot}}}_axis)"
            construct_template_list.append(construct_template)
        else:
            for idx, axis in enumerate(axes):
                if not construct_template_list:
                    args[f"axis_{idx}"] = axis
                    init_template = f"self.{{{variable_slot}}}_{idx}_axis = {{axis_{idx}}}"
                    construct_template = f"opt_{{{variable_slot}}}_{idx} = self.{{{variable_slot}}}" \
                                         f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                                         f"self.{{{variable_slot}}}_{idx}_axis)"
                elif idx == len(axes) - 1:
                    args["axis"] = axis
                    init_template = f"self.{{{variable_slot}}}_axis = {{axis}}"
                    construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                                         f"({{{variable_slot}}}_{idx - 1}, self.{{{variable_slot}}}_axis)"
                else:
                    args[f"axis_{idx}"] = axis
                    init_template = f"self.{{{variable_slot}}}_{idx}_axis = {{axis_{idx}}}"
                    construct_template = f"opt_{{{variable_slot}}}_{idx} = self.{{{variable_slot}}}" \
                                         f"({{{variable_slot}}}_{idx - 1}, self.{{{variable_slot}}}_{idx}_axis)"

                init_template_list.append(init_template)
                construct_template_list.append(construct_template)

        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: init_template_list,
                TemplateKeywords.CONSTRUCT.value: construct_template_list
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
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: dict()
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
