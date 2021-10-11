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
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class GlobalPoolMapper(ONNXToMindSporeMapper):
    """AvgPool mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        if kwargs['op_name'] == 'onnx::GlobalAveragePool':
            op_name = 'nn.AvgPool{}d'
        else:
            op_name = 'nn.MaxPool{}d'
        dim = 1 if len(kwargs['params']['input_shape']) == 3 else 2
        return op_name.format(dim)

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        dim = 1 if len(params['input_shape']) == 3 else 2
        if dim == 1:
            kernel_size = params['input_shape'][-1] // params['output_shape'][-1]
        else:
            kernel_size_height = params['input_shape'][-2] // params['output_shape'][-2]
            kernel_size_width = params['input_shape'][-1] // params['output_shape'][-1]
            kernel_size = (kernel_size_height, kernel_size_width)
        return {
            'kernel_size': kernel_size
        }

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()
