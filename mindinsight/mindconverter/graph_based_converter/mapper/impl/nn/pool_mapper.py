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
from ...gen_setting import Setting


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
    def _convert_params(**kwargs):
        params = kwargs['params']
        transformed_params = dict()
        transformed_params["kernel_size"] = tuple(params['kernel_shape'])
        transformed_params["stride"] = tuple(params['strides'])
        if "pads" in params:
            if sum(params['pads']) == 0:
                pad_mode = '\"valid\"'
            else:
                pad_mode = '\"same\"'
            transformed_params["pad_mode"] = pad_mode

        return transformed_params

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        return Setting()
