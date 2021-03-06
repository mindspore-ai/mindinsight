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
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
    WeightType
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class MulMapper(ONNXToMindSporeMapper):
    """Mul mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Mul"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs['weights']
        if weights:
            tensor = MulMapper._find_val_by_index(0, weights)
            return {'w': {'data': tensor, 'type': WeightType.PARAMETER.value}}
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        op = kwargs.get("operation")
        args = kwargs.get("converted_params")
        weights = kwargs.get("weights")
        if not weights:
            return template, exchange_msg, outputs_list, outputs_mapping

        tensor = MulMapper._find_val_by_index(0, weights)

        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}()"
        args["w_shape"] = tensor.shape
        args["w_dtype"] = tensor.dtype
        init_tensor = f"self.{{{variable_slot}}}_w = " \
                      f"Parameter(Tensor(np.random.uniform(0, 1, {{w_shape}}).astype(np.{{w_dtype}})), " \
                      f"name=None)"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}," \
                             f"self.{{{variable_slot}}}_w)"
        template = reset_init_or_construct(template, variable_slot, [init_template, init_tensor],
                                           TemplateKeywords.INIT.value)
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)
        return template, exchange_msg, outputs_list, outputs_mapping
