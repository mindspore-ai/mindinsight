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
from mindinsight.mindconverter.graph_based_converter.mapper.impl.nn.conv_mapper import ConvMapper


class Conv2dTransposeMapper(ONNXToMindSporeMapper):
    """Conv2dTranspose mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        # MindSpore only support Conv2dTranspose.
        kernel_size = kwargs['params'].get('kernel_shape')
        dim = len(kernel_size)
        if dim != 2:
            raise ValueError("MindSpore only support Conv2dTranspose.")
        return "nn.Conv2dTranspose"

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs['weights']
        params = kwargs['params']
        return ConvMapper.convert_params_tf(params=params, weights=weights)

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs['weights']
        weight = Conv2dTransposeMapper._find_val_by_index(0, weights)
        bias = Conv2dTransposeMapper._find_val_by_index(1, weights)

        converted_weights = {'weight': {'data': weight}}
        if isinstance(bias, np.ndarray):
            converted_weights['bias'] = {'data': bias}

        return converted_weights
