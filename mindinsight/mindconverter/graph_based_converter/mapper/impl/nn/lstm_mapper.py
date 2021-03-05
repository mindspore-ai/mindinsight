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
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords



class LSTMMapper(ONNXToMindSporeMapper):
    """LSTM mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.LSTM"

    @staticmethod
    def _convert_params(**kwargs):
        """convert params"""
        weights = kwargs["weights"]
        input_weights = LSTMMapper._find_val_by_index(0, weights)
        embed_dim = input_weights.shape[2]
        params = kwargs['params']
        output_shape_list = kwargs.get("params").get("output_shape")
        output_shape = output_shape_list[0].node_output_shape
        # Here the first element determine if the lstm is bidirectional
        # `1` means unidirectional. `2` means bidirectional
        if output_shape[1] == 2:
            return {
                "input_size": embed_dim,
                "hidden_size": params["hidden_size"],
                "bidirectional": True
            }

        return {
            "input_size": embed_dim,
            "hidden_size": params["hidden_size"]
        }

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        """generate snippet template"""
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        output_shape_list = kwargs.get("raw_params").get("output_shape")
        output_shape = output_shape_list[0].node_output_shape
        output_reshape = (output_shape[0], output_shape[2], output_shape[1], output_shape[3])
        trainable_params = kwargs.get("trainable_params", dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")
        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"
        init_reshape = f"self.{{{variable_slot}}}_reshape = P.Reshape()"
        init_transpose = f"self.{{{variable_slot}}}_transpose = P.Transpose()"
        init_cast = f"self.{{{variable_slot}}}_cast = P.Cast()"
        construct_template = f"opt_{{{variable_slot}}}, (opt_{{{variable_slot}}}_h, " \
                             f"opt_{{{variable_slot}}}_c) = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
        construct_template_cast = f"opt_{{{variable_slot}}} = " \
                                     f"self.{{{variable_slot}}}_cast(" \
                                     f"opt_{{{variable_slot}}}, mindspore.float32)"
        construct_template_reshape = f"opt_{{{variable_slot}}} = " \
                                     f"self.{{{variable_slot}}}_reshape(" \
                                     f"opt_{{{variable_slot}}}, {output_reshape})"
        construct_template_transpose = f"opt_{{{variable_slot}}} = " \
                                       f"self.{{{variable_slot}}}_transpose(" \
                                       f"opt_{{{variable_slot}}}, (0, 2, 1, 3))"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template, init_cast, init_reshape, init_transpose],
                TemplateKeywords.CONSTRUCT.value: [construct_template,
                                                   construct_template_cast,
                                                   construct_template_reshape,
                                                   construct_template_transpose]
            }
        }
        exchange_msg = {
            variable_slot: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: op,
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.GROUP_INPUTS.value: [(1, 2)],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: args,
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: weights,
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: trainable_params
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}", f"opt_{{{variable_slot}}}_h", f"opt_{{{variable_slot}}}_c"]
        outputs_mapping = ((0, 0), (1, 1), (2, 2),)
        return template, exchange_msg, outputs_list, outputs_mapping
