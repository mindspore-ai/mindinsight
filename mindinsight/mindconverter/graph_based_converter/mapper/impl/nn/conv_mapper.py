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
import numpy as np
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.common.utils import convert_bytes_string_to_string


def _convert_padding(**kwargs):
    """Convert padding."""
    params = kwargs['params']
    if not params.get('pads'):
        return '\"valid\"', 0
    if sum(params['pads']) == 0:
        return '\"valid\"', 0
    pads_onnx = params['pads']
    half_index = len(pads_onnx) // 2
    padding = []
    for num_begin, num_end in zip(pads_onnx[:half_index], pads_onnx[half_index:]):
        padding += [num_begin, num_end]
    return '\"pad\"', tuple(padding)


class ConvMapper(ONNXToMindSporeMapper):
    """Conv2d mapper."""

    @staticmethod
    def convert_params_torch(**kwargs):
        """Convert params from PyTorch to MindSpore"""
        weights = kwargs['weights']
        params = kwargs['params']
        weight = ConvMapper._find_val_by_index(0, weights)
        weight = np.transpose(weight, list(range(2, weight.ndim)) + [1, 0])
        if isinstance(params['dilations'], list):
            dilation = tuple(params['dilations'])
        else:
            dilation = params['dilations']
        if isinstance(params['strides'], list):
            stride = tuple(params['strides'])
        else:
            stride = params['strides']
        kernel_shape = list(weight.shape)
        in_channels = kernel_shape[-2] * params.get("group", 1)
        out_channels = kernel_shape[-1]
        kernel_size = kernel_shape[:-2]
        if len(kernel_size) == 1:
            kernel_size = kernel_size[0]
        else:
            kernel_size = tuple(kernel_size)
        pad_mode, padding = _convert_padding(params=params)
        return {
            'in_channels': in_channels,
            'out_channels': out_channels,
            'kernel_size': kernel_size,
            'stride': stride,
            'padding': padding,
            'pad_mode': pad_mode,
            'dilation': dilation,
            'group': params['group']}

    @staticmethod
    def convert_params_tf(**kwargs):
        """Convert params from Tensorflow to MindSpore"""
        weights = kwargs['weights']
        params = kwargs['params']
        weight = ConvMapper._find_val_by_index(0, weights)
        bias = ConvMapper._find_val_by_index(1, weights)
        if weight is None:
            raise ValueError("Conv. Mapper cannot get the weight.")

        has_bias = isinstance(bias, np.ndarray)

        auto_pad = None
        if params.get("auto_pad") is not None:
            auto_pad = convert_bytes_string_to_string(params.get("auto_pad"))

        # tmp tf translated ver. mapping
        if isinstance(params.get('dilations'), list):
            dilation = tuple(params.get('dilations'))
        else:
            dilation = params.get('dilations')

        if isinstance(params.get('strides'), list):
            stride = tuple(params.get('strides'))
        else:
            stride = params.get('strides')

        kernel_size = params.get('kernel_shape')
        # Onnx in_channel equals ms inchannel divided by group
        in_channels = weight.shape[1] * params.get('group', 1)
        out_channels = weight.shape[0]
        if len(kernel_size) == 1:
            kernel_size = kernel_size[0]
        else:
            kernel_size = tuple(kernel_size)

        pad_mode, padding = _convert_padding(params=params)

        if auto_pad == "SAME_UPPER":
            pad_mode = "\'same\'"
            padding = 0

        return {
            'in_channels': in_channels,
            'out_channels': out_channels,
            'kernel_size': kernel_size,
            'stride': stride,
            'padding': padding,
            'pad_mode': pad_mode,
            'dilation': dilation,
            'group': params.get('group', 1),
            'has_bias': has_bias
        }

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        kernel_size = kwargs['params'].get('kernel_shape')
        dim = len(kernel_size)
        return f"nn.Conv{dim}d"

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs['weights']
        params = kwargs['params']

        return ConvMapper.convert_params_tf(params=params, weights=weights)

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs['weights']
        weight = ConvMapper._find_val_by_index(0, weights)
        bias = ConvMapper._find_val_by_index(1, weights)

        converted_weights = {'weight': {'data': weight}}
        if isinstance(bias, np.ndarray):
            converted_weights['bias'] = {'data': bias}

        return converted_weights
