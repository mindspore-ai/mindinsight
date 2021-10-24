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
import numpy as np

from mindconverter.graph_based_converter.common.utils import reset_init_or_construct
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class DenseMapper(ONNXToMindSporeMapper):
    """Dense mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Dense"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        trans_b = params.get('transB', 0)
        weights = kwargs['weights']
        weight_index = 0
        bias_index = 1
        bias = DenseMapper._find_val_by_index(bias_index, weights)
        has_bias = isinstance(bias, np.ndarray)
        weight = DenseMapper._find_val_by_index(weight_index, weights)
        if trans_b:
            weight = weight.transpose()
        in_channels, out_channels = weight.shape
        return {
            'in_channels': in_channels,
            'out_channels': out_channels,
            'has_bias': has_bias
        }

    @staticmethod
    def _convert_trained_weights(**kwargs):
        params = kwargs['params']
        trans_b = params.get('transB', 0)
        alpha = params.get('alpha', 1.0)
        beta = params.get('beta', 1.0)
        weights = kwargs['weights']
        weight = DenseMapper._find_val_by_index(0, weights).transpose()
        if trans_b:
            weight = weight.transpose()
        bias = DenseMapper._find_val_by_index(1, weights)
        return {
            'weight': {'data': alpha * weight},
            'bias': {'data': beta * bias}
        }

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        raw_params = kwargs.get('raw_params', dict())
        trans_a = raw_params.get('transA', 0)
        if not trans_a:
            return template, exchange_msg, outputs_list, outputs_mapping

        op = kwargs.get("operation")
        args = kwargs.get("converted_params")
        weights = kwargs.get("weights")
        trainable_params = kwargs.get('trainable_params', dict())

        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        input_rank = len(raw_params['input_shape'])
        input_perm = [i for i in range(input_rank)]
        input_perm[-2], input_perm[-1] = input_perm[-1], input_perm[-2]

        variable_slot = "var_0"
        init_input_perm = f"self.{{{variable_slot}}}_input_perm = {{input_perm}}"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"
        inputs_in_construct = [f"{{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}",
                               f"self.{{{variable_slot}}}_input_perm"]

        args['input_perm'] = tuple(input_perm)
        construct_transpose = f"opt_{{{variable_slot}}}_transpose = P.Transpose()({', '.join(inputs_in_construct)})"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}(opt_{{{variable_slot}}}_transpose)"
        template = reset_init_or_construct(template, variable_slot, [init_input_perm, init_template],
                                           TemplateKeywords.INIT.value)
        template = reset_init_or_construct(template, variable_slot, [construct_transpose, construct_template],
                                           TemplateKeywords.CONSTRUCT.value)
        exchange_msg = {
            variable_slot: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: op,
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: args,
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: weights,
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: trainable_params
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
