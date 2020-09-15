# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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
from ...base import ONNXToMindSporeMapper


class ConvMapper(ONNXToMindSporeMapper):
    """Conv2d mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        weight = kwargs['weights']['weight'].numpy()
        dim = weight.ndim - 2
        return f"nn.Conv{dim}d"

    @staticmethod
    def _convert_params(params, weights):
        weight = weights['weight'].numpy()
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
        pad_mode, padding = ConvMapper._convert_padding(params)
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
    def _convert_trained_weights(weights):
        if weights:
            pass
        return dict()

    @staticmethod
    def _convert_padding(params):
        if sum(params['pads']) == 0:
            return '\"valid\"', 0
        return '\"pad\"', tuple(params['pads'])
