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


class OneHotMapper(ONNXToMindSporeMapper):
    """OneHot mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.OneHot"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs.get('params')
        converted_params = {}
        if params.get('axis'):
            converted_params['axis'] = params.get('axis')
        if kwargs.get('weights'):
            weights = kwargs.get('weights')
            depth = weights[0]
            val = weights[1]
            if depth and isinstance(depth.value, np.ndarray):
                ms_depth = depth.value[0]
                converted_params['depth'] = ms_depth
            if val and isinstance(val.value, np.ndarray):
                ms_off_val = val.value[0]
                ms_on_val = val.value[1]
                converted_params['off_value'] = ms_off_val
                converted_params['on_value'] = ms_on_val
        return converted_params

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()
