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
from mindconverter.graph_based_converter.common.utils import convert_bytes_string_to_string
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
    WeightType


class ConvBackPropInputMapper(ONNXToMindSporeMapper):
    """ConvBackPropInput mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        kernel_size = kwargs['params'].get('kernel_shape', tuple())
        if len(kernel_size) != 2:
            raise AttributeError("MindSpore only support Conv2dTranspose and Conv3dTranspose.")
        dim = len(kernel_size)
        return f"P.Conv{dim}DBackpropInput"

    @staticmethod
    def _convert_padding(**kwargs):
        """Convert padding."""
        params = kwargs['params']

        if params.get('auto_pad'):
            auto_pad = convert_bytes_string_to_string(params.get('auto_pad'))
            if auto_pad == "SAME_UPPER":
                pad_mode = '\"same\"'
                padding = 0
                return pad_mode, padding

        if not params.get('pads'):
            return '\"valid\"', 0
        if sum(params['pads']) == 0:
            return '\"valid\"', 0
        pads_onnx = params['pads']
        half_index = len(pads_onnx) // 2
        paddings = []
        for num_begin, num_end in zip(pads_onnx[:half_index], pads_onnx[half_index:]):
            paddings += [num_begin, num_end]
        return '\"pad\"', tuple(paddings)

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs['weights']
        params = kwargs['params']
        weight = ConvBackPropInputMapper._find_val_by_index(0, weights)
        if weight is None:
            raise ValueError("ConvBackPropInput. Mapper cannot get weight.")

        if isinstance(params.get('dilations'), list):
            dilation = tuple(params.get('dilations'))
        else:
            dilation = params.get('dilations')

        if isinstance(params.get('strides'), list):
            stride = tuple(params.get('strides'))
        else:
            stride = params.get('strides')

        kernel_size = params.get('kernel_shape', tuple())
        out_channel = weight.shape[1]
        if len(kernel_size) == 1:
            kernel_size = kernel_size[0]
        else:
            kernel_size = tuple(kernel_size)

        pad_mode, padding = ConvBackPropInputMapper._convert_padding(params=params)

        return {
            'out_channel': out_channel,
            'kernel_size': kernel_size,
            'stride': stride,
            'pad': padding,
            'pad_mode': pad_mode,
            'dilation': dilation,
            'group': params.get('group', 1)
        }

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs['weights']
        weight = ConvBackPropInputMapper._find_val_by_index(0, weights)
        bias = ConvBackPropInputMapper._find_val_by_index(1, weights)
        onnx_name_weight = ConvBackPropInputMapper._find_onnx_name_by_index(0, weights)
        onnx_name_bias = ConvBackPropInputMapper._find_onnx_name_by_index(1, weights)
        converted_weights = {
            'weight': {'data': weight, 'type': WeightType.PARAMETER.value, 'onnx_name': onnx_name_weight}
        }
        if isinstance(bias, np.ndarray):
            converted_weights['bias'] = {'data': bias, 'type': WeightType.PARAMETER.value, 'onnx_name': onnx_name_bias}
        return converted_weights

    @staticmethod
    def _deconv_output_length(pad_mode, input_length, filter_size, stride_size, dilation_size, padding, output_padding):
        """Calculate the length of output."""
        length = 0
        filter_size = filter_size + (filter_size - 1) * (dilation_size - 1)
        if pad_mode == '\"valid\"':
            if filter_size - stride_size > 0:
                length = input_length * stride_size + filter_size - stride_size + output_padding
            else:
                length = input_length * stride_size + output_padding
        elif pad_mode == '\"same\"':
            length = input_length * stride_size + output_padding
        elif pad_mode == '\"pad\"':
            length = input_length * stride_size - padding + filter_size - stride_size + output_padding
        return length

    @staticmethod
    def _deconv_output_shape(input_shape, args, output_padding):
        """Calculate the height and wide of output."""
        kernel_shape = args['kernel_size']
        stride = args['stride']
        dilation = args['dilation']
        padding = args['pad']
        pad_mode = args['pad_mode']

        padding_h = padding[0] + padding[1] if isinstance(padding, tuple) else 0
        padding_w = padding[2] + padding[3] if isinstance(padding, tuple) else 0

        h_out = ConvBackPropInputMapper._deconv_output_length(pad_mode, input_shape[0], kernel_shape[0], stride[0],
                                                              dilation[0], padding_h, output_padding[0])
        w_out = ConvBackPropInputMapper._deconv_output_length(pad_mode, input_shape[1], kernel_shape[1], stride[1],
                                                              dilation[1], padding_w, output_padding[1])
        return h_out, w_out

    @staticmethod
    def bias_str(variable_slot, init_tmp_list, construct_tmp_list):
        """Add init and construct code for Bias."""
        variable_slot_bias_name = f"{variable_slot}/bias"
        init_tmp_list.append(f"self.{{{variable_slot}}}_bias_add = P.BiasAdd()")
        init_tmp_list.append(f"self.{{{variable_slot}}}_bias = {{{variable_slot_bias_name}}}")
        construct_tmp_list.append(
            f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}_bias_add(opt_{{{variable_slot}}}, "
            f"self.{{{variable_slot}}}_bias)")

        return init_tmp_list, construct_tmp_list

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation").replace("onnx::", "onnx.")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get('weights')
        trainable_params = kwargs.get('trainable_params', dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        raw_params = kwargs['raw_params']
        _, _, input_h, input_w = raw_params['input_shape']
        output_padding = raw_params.get('output_padding', (0, 0))

        h_out, w_out = ConvBackPropInputMapper._deconv_output_shape((input_h, input_w), args, output_padding)

        variable_slot = "var_0"
        variable_slot_weight_name = f"{variable_slot}/weight"
        init_template_list = [f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})",
                              f"self.{{{variable_slot}}}_weight = {{{variable_slot_weight_name}}}",
                              *ConvBackPropInputMapper.output_shape_str(variable_slot, True)]

        args['h_out'] = h_out
        args['w_out'] = w_out
        construct_template_list = [f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}"
                                   f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, "
                                   f"self.{{{variable_slot}}}_weight, "
                                   f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}.shape[0], "
                                   f"{', '.join(ConvBackPropInputMapper.output_shape_str(variable_slot))}))"]

        if trainable_params.get('bias'):
            init_template_list, construct_template_list = ConvBackPropInputMapper.bias_str(variable_slot,
                                                                                           init_template_list,
                                                                                           construct_template_list)
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: init_template_list,
                TemplateKeywords.CONSTRUCT.value: construct_template_list
            }
        }
        exchange_msg = ConvBackPropInputMapper._get_exchange_msg(variable_slot, op, args, weights, trainable_params)

        exchange_msg[variable_slot][ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value] = {
            "weight": ""}
        if trainable_params.get("bias"):
            exchange_msg[variable_slot][ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value][
                "bias"] = ""
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_exchange_msg(variable_slot, op, args, weights, trainable_params):
        """Generate exchange msg."""
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
        return exchange_msg

    @staticmethod
    def output_shape_str(variable_slot, has_value=False):
        """Return output_shape."""
        if has_value:
            output_str = [f"self.{{{variable_slot}}}_out_channel = {{out_channel}}",
                          f"self.{{{variable_slot}}}_h_out = {{h_out}}",
                          f"self.{{{variable_slot}}}_w_out = {{w_out}}"]
        else:
            output_str = [f"self.{{{variable_slot}}}_out_channel",
                          f"self.{{{variable_slot}}}_h_out",
                          f"self.{{{variable_slot}}}_w_out"]
        return output_str

    @staticmethod
    def convert_padding(**kwargs):
        """Called for ConvTranspose mapper."""
        return ConvBackPropInputMapper._convert_padding(**kwargs)

    @staticmethod
    def convert_params(**kwargs):
        """Called for ConvTranspose mapper."""
        return ConvBackPropInputMapper._convert_params(**kwargs)

    @staticmethod
    def convert_trained_weights(**kwargs):
        """Called for ConvTranspose mapper."""
        return ConvBackPropInputMapper._convert_trained_weights(**kwargs)

    @staticmethod
    def generate_snippet_template(**kwargs):
        """Called from ConvTranspose mapper."""
        return ConvBackPropInputMapper._generate_snippet_template(**kwargs)
