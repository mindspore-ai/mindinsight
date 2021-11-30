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
from mindconverter.graph_based_converter.common.utils import add_init_or_construct, reset_init_or_construct, \
    reset_exchange_msg
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class ReduceMeanMapper(AtenToMindSporeMapper):
    """Reduce Mean mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.ReduceMean"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs.get("params")
        keep_dims = params.get("constant_2")
        return {"keep_dims": bool(keep_dims)}

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

        args = kwargs.get("converted_params")
        axis = raw_params.get("constant_1")
        args["axis"] = axis

        variable_slot = "var_0"
        init_axis = f"self.{{{variable_slot}}}_axis = {{axis}}"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                             f"self.{{{variable_slot}}}_axis)"
        template = add_init_or_construct(template, variable_slot, init_axis, TemplateKeywords.INIT.value)
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)
        exchange_msg = reset_exchange_msg(exchange_msg, variable_slot, args,
                                          ExchangeMessageKeywords.VariableScope.value.ARGS.value)
        return template, exchange_msg, outputs_list, outputs_mapping