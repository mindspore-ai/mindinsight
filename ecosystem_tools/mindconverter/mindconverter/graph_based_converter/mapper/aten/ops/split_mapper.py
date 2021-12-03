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
from mindconverter.graph_based_converter.common.utils import reset_init_or_construct
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class SplitMapper(AtenToMindSporeMapper):
    """Split mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Split"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs.get("params", dict())
        axis = params.get("constant_2", 0)

        input_shape = params.get("input_shape")
        if not isinstance(input_shape, tuple):
            raise ValueError("Can not get input shape from Operator Split.")

        output_dim = params.get("constant_1", input_shape[axis])
        if input_shape[axis] % output_dim != 0:
            raise ValueError("Operator Split only supports splitting tensor equally.")
        output_num = input_shape[axis] // output_dim
        return {"axis": axis, "output_num": output_num}

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

        variable_slot = "var_0"
        output_num = kwargs.get("converted_params").get("output_num")
        outputs_list = [f"opt_{{{variable_slot}}}_{i}" for i in range(output_num)]
        construct_template = f"{', '.join(outputs_list)} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)
        outputs_mapping = tuple([(i, i) for i in range(output_num)])
        return template, exchange_msg, outputs_list, outputs_mapping
