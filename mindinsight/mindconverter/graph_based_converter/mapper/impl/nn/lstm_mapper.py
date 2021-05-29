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
import numpy as np
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
    WeightType



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
        weights = kwargs["weights"]
        weight_ih = LSTMMapper._find_val_by_index(0, weights)
        weight_hh = LSTMMapper._find_val_by_index(1, weights)
        bias = LSTMMapper._find_val_by_index(2, weights)
        init_h = LSTMMapper._find_val_by_index(3, weights)
        init_c = LSTMMapper._find_val_by_index(4, weights)

        ih_shape = weight_ih.shape
        weight_ih = weight_ih.reshape(ih_shape[0], 4, -1, ih_shape[-1])
        gpu_weight_ih = weight_ih[:, [0, 2, 3, 1], :, :]
        gpu_weight_ih = gpu_weight_ih.reshape(ih_shape)
        ascend_weight_ih = weight_ih[:, [0, 3, 2, 1], :, :].reshape(ih_shape)

        hh_shape = weight_hh.shape
        weight_hh = weight_hh.reshape(hh_shape[0], 4, -1, hh_shape[-1])
        gpu_weight_hh = weight_hh[:, [0, 2, 3, 1], :, :]
        gpu_weight_hh = gpu_weight_hh.reshape(hh_shape)
        ascend_weight_hh = weight_hh[:, [0, 3, 2, 1], :, :].reshape(hh_shape)

        bidirectional = bool(ih_shape[0] > 1)
        gpu_weights = list()
        converted_gpu_weights = dict()
        converted_ascend_weights = dict()
        converted_weights = dict()
        gpu_weights.append(gpu_weight_ih[0].reshape(-1, 1, 1))
        gpu_weights.append(gpu_weight_hh[0].reshape(-1, 1, 1))
        weight_fw0 = np.concatenate([ascend_weight_ih[0], ascend_weight_hh[0]], axis=1)
        converted_ascend_weights['weight_fw0'] = {
            'data': weight_fw0.transpose(1, 0).astype(np.float16)
        }
        if bidirectional:
            gpu_weights.append(gpu_weight_ih[1].reshape(-1, 1, 1))
            gpu_weights.append(gpu_weight_hh[1].reshape(-1, 1, 1))
            weight_bw0 = np.concatenate([ascend_weight_ih[1], ascend_weight_hh[1]], axis=1)
            converted_ascend_weights['weight_bw0'] = {
                'data': weight_bw0.transpose(1, 0).astype(np.float16)
            }
        if bias is not None:
            bias_shape = bias.shape
            bias = bias.reshape(bias_shape[0], 2, 4, -1)
            gpu_bias = bias[:, :, [0, 2, 3, 1], :]
            gpu_bias = gpu_bias.reshape(bias_shape)
            gpu_weights.append(gpu_bias.reshape(-1, 1, 1))
            ascend_bias = bias[:, :, [0, 3, 2, 1], :]
            ascend_bias = (ascend_bias[:, 0, :, :] + ascend_bias[:, 1, :, :]).reshape(bias_shape[0], -1)
            converted_ascend_weights['bias_fw0'] = {'data': ascend_bias[0].astype(np.float16)}
            if bidirectional:
                converted_ascend_weights['bias_bw0'] = {'data': ascend_bias[1].astype(np.float16)}

        gpu_weights = np.concatenate(gpu_weights, axis=0)
        converted_gpu_weights['weight'] = {'data': gpu_weights}
        converted_weights.update(converted_gpu_weights)
        converted_weights.update(converted_ascend_weights)
        if init_h is not None:
            converted_weights['init_h'] = {'data': init_h, 'type': WeightType.PARAMETER.value}
            converted_weights['init_c'] = {'data': init_c, 'type': WeightType.PARAMETER.value}
        return converted_weights

    @staticmethod
    def _generate_snippet_template(**kwargs):
        """generate snippet template"""
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        init_h = LSTMMapper._find_val_by_index(3, weights)
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
        construct_template_cast = f"opt_{{{variable_slot}}} = " \
                                     f"self.{{{variable_slot}}}_cast(" \
                                     f"opt_{{{variable_slot}}}, mindspore.float32)"
        construct_template_reshape = f"opt_{{{variable_slot}}} = " \
                                     f"self.{{{variable_slot}}}_reshape(" \
                                     f"opt_{{{variable_slot}}}, {output_reshape})"
        construct_template_transpose = f"opt_{{{variable_slot}}} = " \
                                       f"self.{{{variable_slot}}}_transpose(" \
                                       f"opt_{{{variable_slot}}}, (0, 2, 1, 3))"

        if init_h is not None:
            h_shape = init_h.shape
            h_dtype = init_h.dtype
            args['h_shape'] = h_shape
            args['h_dtype'] = h_dtype
            init_h_param = f"self.{{{variable_slot}}}_init_h = " \
                           f"Parameter(Tensor(np.zeros({{h_shape}}).astype(np.{{h_dtype}})), " \
                           f"name=None, requires_grad=False)"
            init_c_param = f"self.{{{variable_slot}}}_init_c = " \
                           f"Parameter(Tensor(np.zeros({{h_shape}}).astype(np.{{h_dtype}})), " \
                           f"name=None, requires_grad=False)"
            construct_template = f"opt_{{{variable_slot}}}, (opt_{{{variable_slot}}}_h, " \
                                f"opt_{{{variable_slot}}}_c) = self.{{{variable_slot}}}" \
                                f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}," \
                                f"(self.{{{variable_slot}}}_init_h, self.{{{variable_slot}}}_init_c))"
            template = {
                variable_slot: {
                    TemplateKeywords.INIT.value: [init_h_param, init_c_param, init_template, init_cast,
                                                  init_reshape, init_transpose],
                    TemplateKeywords.CONSTRUCT.value: [construct_template,
                                                       construct_template_cast,
                                                       construct_template_reshape,
                                                       construct_template_transpose]
                }
            }
        else:
            construct_template = f"opt_{{{variable_slot}}}, (opt_{{{variable_slot}}}_h, " \
                                f"opt_{{{variable_slot}}}_c) = self.{{{variable_slot}}}" \
                                f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
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
