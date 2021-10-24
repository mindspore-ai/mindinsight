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
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
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
        gpu_weight_ih, ascend_weight_ih = LSTMMapper._get_gpu_ascend_weight(weight_ih)
        gpu_weight_hh, ascend_weight_hh = LSTMMapper._get_gpu_ascend_weight(weight_hh)

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
    def _get_gpu_ascend_weight(weight):
        """Get GPU and Ascend weight."""
        weight_shape = weight.shape
        weight = weight.reshape(weight_shape[0], 4, -1, weight_shape[-1])
        gpu_weight = weight[:, [0, 2, 3, 1], :, :]
        gpu_weight = gpu_weight.reshape(weight_shape)
        ascend_weight = weight[:, [0, 3, 2, 1], :, :].reshape(weight_shape)
        return gpu_weight, ascend_weight

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
        init_params, construct_params = LSTMMapper._get_init_construct_params(variable_slot, output_reshape)

        if init_h is not None:
            h_shape = init_h.shape
            h_dtype = init_h.dtype
            args['h_shape'] = h_shape
            args['h_dtype'] = h_dtype
            template = LSTMMapper._get_template_with_init_h(variable_slot, init_template, init_params, construct_params)
        else:
            construct_template = f"opt_{{{variable_slot}}}, (opt_{{{variable_slot}}}_h, " \
                                 f"opt_{{{variable_slot}}}_c) = self.{{{variable_slot}}}" \
                                 f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
            template = {
                variable_slot: {
                    TemplateKeywords.INIT.value: [init_template, init_params["cast"], init_params["reshape"],
                                                  init_params["transpose"]],
                    TemplateKeywords.CONSTRUCT.value: [construct_template,
                                                       construct_params["cast"],
                                                       construct_params["reshape"],
                                                       construct_params["transpose"]]
                }
            }

        exchange_msg = LSTMMapper._get_exchange_msg(variable_slot, op, args, weights, trainable_params)
        outputs_list = [f"opt_{{{variable_slot}}}", f"opt_{{{variable_slot}}}_h", f"opt_{{{variable_slot}}}_c"]
        outputs_mapping = ((0, 0), (1, 1), (2, 2),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_init_construct_params(variable_slot, output_reshape):
        """Get init and construct codes for parameters."""
        init_reshape = f"self.{{{variable_slot}}}_reshape = P.Reshape()"
        init_transpose = f"self.{{{variable_slot}}}_transpose = P.Transpose()"
        init_cast = f"self.{{{variable_slot}}}_cast = P.Cast()"
        construct_cast = f"opt_{{{variable_slot}}} = " \
                         f"self.{{{variable_slot}}}_cast(opt_{{{variable_slot}}}, mindspore.float32)"
        construct_reshape = f"opt_{{{variable_slot}}} = " \
                            f"self.{{{variable_slot}}}_reshape(opt_{{{variable_slot}}}, {output_reshape})"
        construct_transpose = f"opt_{{{variable_slot}}} = " \
                              f"self.{{{variable_slot}}}_transpose(opt_{{{variable_slot}}}, (0, 2, 1, 3))"

        init_codes = {"cast": init_cast, "reshape": init_reshape, "transpose": init_transpose}
        construct_codes = {"cast": construct_cast, "reshape": construct_reshape, "transpose": construct_transpose}
        return init_codes, construct_codes

    @staticmethod
    def _get_template_with_init_h(variable_slot, init_template, init_params, construct_params):
        """Get template with init_h."""
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
                TemplateKeywords.INIT.value: [init_h_param, init_c_param, init_template, init_params["cast"],
                                              init_params["reshape"], init_params["transpose"]],
                TemplateKeywords.CONSTRUCT.value: [construct_template,
                                                   construct_params["cast"],
                                                   construct_params["reshape"],
                                                   construct_params["transpose"]]
            }
        }
        return template

    @staticmethod
    def _get_exchange_msg(variable_slot, op, args, weights, trainable_params):
        """Get exchange msg for mapper."""
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
        return exchange_msg
