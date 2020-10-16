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


class PadMapper(ONNXToMindSporeMapper):
    """Pad mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Pad"

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        if params['mode'] == 'constant':
            if params['value'] == 0:
                mode = '\"CONSTANT\"'
            else:
                msg = "{UNSUPPORTED: value is NOT 0}\"CONSTANT\""
                mode = msg
        elif params['mode'] == 'reflect':
            mode = '\"REFLECT\"'
        else:
            msg = f"{{UNSUPPORTED: \"{params['mode']}\"}}\"UNKNOWN\""
            mode = msg
        pads_onnx = params['pads']
        half_index = len(pads_onnx) // 2
        paddings = (
            (num_begin, num_end) for num_begin, num_end in zip(pads_onnx[:half_index], pads_onnx[half_index:]))
        return {'paddings': tuple(paddings),
                'mode': mode}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        return dict()
