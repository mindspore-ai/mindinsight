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


class DenseMapper(ONNXToMindSporeMapper):
    """Dense mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Dense"

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs['weights']
        weight_index = 0
        bias_index = 1
        bias = DenseMapper._find_val_by_index(bias_index, weights)
        has_bias = isinstance(bias, np.ndarray)
        weight = DenseMapper._find_val_by_index(weight_index, weights).transpose()
        in_channels, out_channels = weight.shape
        return {
            'in_channels': in_channels,
            'out_channels': out_channels,
            'has_bias': has_bias
        }

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs['weights']
        weight = DenseMapper._find_val_by_index(0, weights)
        bias = DenseMapper._find_val_by_index(1, weights)
        return {
            'weight': {'data': weight},
            'bias': {'data': bias}
        }
