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
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class ReduceMeanMapper(ONNXToMindSporeMapper):
    """ReduceMean mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.ReduceMean"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        keep_dims = not params['keepdims'] == 0
        return {'keep_dims': keep_dims}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        raw_params = kwargs.get("raw_params")
        if raw_params.get('axes'):
            axis = raw_params['axes'][0] if len(raw_params['axes']) == 1 else tuple(raw_params['axes'])
        else:
            axis = tuple()
        variable_slot = "var_0"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, {axis})"
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)

        return template, exchange_msg, outputs_list, outputs_mapping
