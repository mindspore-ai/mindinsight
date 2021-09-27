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
import re

import numpy as np

from mindinsight.mindconverter.graph_based_converter.common.utils import convert_bytes_string_to_string
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
    WeightType, BLANK_SYM
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class EinSumMapper(ONNXToMindSporeMapper):
    """EinSum mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        equation = kwargs['params']['equation']
        if not EinSumMapper.equation_check(equation):
            return None
        return "P.MatMul"

    @staticmethod
    def equation_check(equation):
        """
        Check equation validation.
        Only support equation `bfxxx, xxxh -> bfh`.

        Args:
            equation (Union[str, bytes]): Equation of EinSum.

        Returns:
            bool, True if equation is format of `bfxxx, xxxh -> bfh`, otherwise False.
        """

        equation = convert_bytes_string_to_string(equation)

        equation = equation.replace(BLANK_SYM, '').split('->')
        if len(equation) != 2:
            return False

        equation_left_list = equation[0].split(',')
        if len(equation_left_list) != 2:
            return False

        equation_right = equation[1]
        pattern = ''.join([s for s in equation_left_list[0] if s in equation_left_list[1]])
        output_first = re.sub(pattern, '', equation_left_list[0])
        output_second = re.sub(pattern, '', equation_left_list[1])
        output = ''.join((output_first, output_second)).replace(BLANK_SYM, '')
        return output == equation_right

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get('weights', list())
        tensor = EinSumMapper._find_val_by_index(0, weights)
        if isinstance(tensor, np.ndarray) and tensor.shape:
            return {'weight': {'data': tensor, 'type': WeightType.PARAMETER.value}}
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params")
        weights = kwargs.get("weights")
        input_shape = kwargs["raw_params"]["input_shape"]
        trainable_params = kwargs.get("trainable_params", dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        variable_slot = "var_0"
        init_template_list = [f"self.{{{variable_slot}}} = {op}()"]

        default_shape = input_shape[:2]
        inputs_in_construct = [
            f"{{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}"
            f".view({default_shape[0]} * {default_shape[1]}, -1)"]

        if weights:
            tensor = EinSumMapper._find_val_by_index(0, weights)
            args["weight_shape"] = tensor.shape
            args["weight_dtype"] = tensor.dtype

            weight_location = EinSumMapper._find_location_by_index(0, weights)

            init_template_list.append(
                f"self.{{{variable_slot}}}_weight = "
                f"Parameter(Tensor(np.random.uniform(0, 1, {{weight_shape}}).astype(np.{{weight_dtype}})), name=None)")

            default_shape += (tensor.shape[-1],)
            inputs_in_construct.insert(weight_location, f"self.{{{variable_slot}}}_weight.view(-1, {tensor.shape[-1]})")

        construct_template = f"opt_{{{variable_slot}}} = " \
                             f"self.{{{variable_slot}}}({', '.join(inputs_in_construct)}).view{default_shape}"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: init_template_list,
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
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: trainable_params
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping
