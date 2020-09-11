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
from ...base import ONNXToMindSporeMapper


class PoolMapper(ONNXToMindSporeMapper):
    """MaxPool mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        if kwargs['op_name'] == 'onnx::AveragePool':
            op_name = 'nn.AvgPool{}d'
        else:
            op_name = 'nn.MaxPool{}d'
        dim = len(kwargs['params']['strides'])
        return op_name.format(dim)

    @staticmethod
    def _convert_params(params, weights):
        if sum(params['pads']) == 0:
            pad_mode = '\"valid\"'
        else:
            pad_mode = '\"same\"'
        return {
            'kernel_size': tuple(params['kernel_shape']),
            'stride': tuple(params['strides']),
            'pad_mode': pad_mode
        }

    @staticmethod
    def _convert_trained_weights(weights):
        if weights:
            pass
        return dict()
