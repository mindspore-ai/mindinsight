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
from ....common import utils


class ResizeMapper(ONNXToMindSporeMapper):
    """Resize mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        params = kwargs.get("params")
        onnx_coordinate_transform = params.get("coordinate_transformation_mode")
        if onnx_coordinate_transform is not None:
            onnx_coordinate_transform = utils.convert_bytes_string_to_string(onnx_coordinate_transform)

        interpolation_mode = params.get("mode")
        if interpolation_mode is not None:
            interpolation_mode = utils.convert_bytes_string_to_string(interpolation_mode)

        # Define which MindSpore Resize operator to be used
        if interpolation_mode == "linear":
            return "P.ResizeBilinear"

        if interpolation_mode == "nearest":
            return "P.ResizeNearestNeighbor"

        # For undefined situation, use bilinear as default.
        return "P.ResizeBilinear"

    @staticmethod
    def _convert_params(**kwargs):
        weights = kwargs.get("weights")
        params = kwargs.get("params")
        # Set default params
        align_corners = False

        if len(weights) > 3:
            raise ValueError("For resize, `weights` length less or equal to 3.")

        onnx_coordinate_transform = params.get("coordinate_transformation_mode")
        if onnx_coordinate_transform is not None:
            onnx_coordinate_transform = utils.convert_bytes_string_to_string(onnx_coordinate_transform)

        if onnx_coordinate_transform == "align_corners" or "half_pixel" in onnx_coordinate_transform:
            align_corners = True

        # Get requested size for resize
        size = list(weights.values())[-1][-2:].tolist()

        return {"size": tuple(size),
                "align_corners": align_corners}

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        if kwargs.get("weights", None):
            return Setting()
        return Setting()
