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
from mindinsight.mindconverter.graph_based_converter.common.utils import convert_bytes_string_to_string
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


def _padding_format_convert(padding: list):
    """Convert Onnx padding format to Mindspore"""
    num = len(padding)
    if num % 2 != 0:
        raise ValueError(f"Padding list should be even length but got {num}")

    low = 0
    mid = num // 2
    lst = []
    ms_pad_front = low
    ms_pad_back = mid
    while ms_pad_front < mid and ms_pad_back < num:
        lst.append((padding[ms_pad_front], padding[ms_pad_back]))
        ms_pad_front += 1
        ms_pad_back += 1

    return tuple(lst)


class PadMapper(ONNXToMindSporeMapper):
    """Pad mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "nn.Pad"

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs.get("weights")
        params = kwargs.get("params")
        mode = convert_bytes_string_to_string(params.get('mode', 'constant'))
        pads_onnx = params.get("pads") if params.get("pads") else PadMapper._find_val_by_index(0, weights).tolist()
        if mode == 'constant' and params.get('value') is None:
            if params.get('pads') or weights:
                if isinstance(pads_onnx, list):
                    paddings = _padding_format_convert(pads_onnx)
                    return {'paddings': paddings, 'mode': '\"CONSTANT\"'}
        if mode == 'constant':
            if params['value'] == 0:
                mode = '\"CONSTANT\"'
            else:
                msg = "{UNSUPPORTED: value is NOT 0}\"CONSTANT\""
                mode = msg
        elif mode == 'reflect':
            mode = '\"REFLECT\"'
        else:
            msg = f"{{UNSUPPORTED: \"{mode}\"}}\"UNKNOWN\""
            mode = msg
        half_index = len(pads_onnx) // 2
        paddings = (
            (num_begin, num_end)
            for num_begin, num_end in zip(pads_onnx[:half_index], pads_onnx[half_index:])
        )
        return {'paddings': tuple(paddings), 'mode': mode}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()
