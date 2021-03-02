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
import math

import numpy as np

from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords


class PoolMapper(ONNXToMindSporeMapper):
    """Pool mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        if kwargs['op_name'] == 'onnx::AveragePool':
            op_name = 'nn.AvgPool{}d'
        else:
            op_name = 'nn.MaxPool{}d'
        dim = len(kwargs['params']['strides'])
        return op_name.format(dim)

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        transformed_params = dict()
        transformed_params["kernel_size"] = tuple(params['kernel_shape'])
        transformed_params["stride"] = tuple(params['strides'])

        return transformed_params

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _get_ms_opt_shape(**kwargs):
        """Get output shape in MindSpore."""
        params = kwargs['raw_params']
        input_shape = params['input_shape']
        kernel_shape = params['kernel_shape']
        strides = params['strides']
        dilations = params.get('dilations', (1, 1))
        ms_opt_shape = np.true_divide(np.subtract(np.array(input_shape[-len(kernel_shape):], dtype=np.float32),
                                                  ((np.array(kernel_shape, dtype=np.float32) - 1) *
                                                   np.array(dilations, dtype=np.float32) + 1)) + 1,
                                      np.array(strides, dtype=np.float32)).tolist()
        ms_opt_shape_ceil = tuple(math.ceil(ms_opt_shape_axis) for ms_opt_shape_axis in ms_opt_shape)
        return ms_opt_shape_ceil

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())

        ms_opt_shape = PoolMapper._get_ms_opt_shape(**kwargs)
        tensor_opt_shape = kwargs['raw_params']['output_shape']
        tensor_ipt_shape = kwargs['raw_params']['input_shape']
        kernel_shape = kwargs['raw_params']['kernel_shape']
        dilations = kwargs['raw_params'].get('dilations', (1, 1))
        strides = kwargs['raw_params']['strides']

        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}(opt_{{{variable_slot}}})"

        init_template_pad, construct_template_pad, paddings = \
            PoolMapper._generate_pad_init_and_construct(tensor_opt_shape, tensor_ipt_shape,
                                                        ms_opt_shape, variable_slot,
                                                        kernel_shape, dilations, strides)

        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template_pad, init_template],
                TemplateKeywords.CONSTRUCT.value: [construct_template_pad, construct_template]
            }
        }

        args['paddings'] = paddings

        exchange_msg = {
            variable_slot: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: op,
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: args,
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: dict(),
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: dict()
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _generate_pad_init_and_construct(tensor_opt_shape, tensor_ipt_shape,
                                         ms_opt_shape, variable_slot, kernel_shape, dilations, strides):
        """Generate pad code in init and construct."""
        onnx_opt_shape = tensor_opt_shape[-len(ms_opt_shape):]
        onnx_ipt_shape = tensor_ipt_shape[-len(ms_opt_shape):]

        if np.any(np.array(ms_opt_shape) > np.array(onnx_opt_shape)):
            raise ValueError(f"ms_opt_shape[{ms_opt_shape}] should be no larger than onnx_opt_shape[{onnx_opt_shape}].")

        if np.all(np.array(ms_opt_shape) == np.array(onnx_opt_shape)):
            shape_diff = np.zeros(len(ms_opt_shape)).astype(np.int).tolist()
        else:
            shape_diff = np.subtract((np.array(onnx_opt_shape) - 1) * np.array(strides),
                                     np.subtract(np.array(onnx_ipt_shape),
                                                 (np.array(kernel_shape) - 1) * np.array(dilations) + 1)).tolist()

        zero_pad_single = (0, 0)
        paddings = [zero_pad_single]
        num_zero_pads = len(tensor_opt_shape) - len(ms_opt_shape)
        for _ in range(num_zero_pads - 1):
            paddings.append(zero_pad_single)

        for axis_diff in shape_diff:
            paddings.append((int(axis_diff // 2), int(axis_diff // 2 + axis_diff % 2)))

        init_template_pad = f"self.pad_{{{variable_slot}}} = nn.Pad(paddings={{paddings}})"
        construct_template_pad = f"opt_{{{variable_slot}}} = self.pad_{{{variable_slot}}}" \
                                 f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"

        return init_template_pad, construct_template_pad, tuple(paddings)
