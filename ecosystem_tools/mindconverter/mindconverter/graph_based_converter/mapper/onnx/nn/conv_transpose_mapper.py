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
from mindconverter.graph_based_converter.common.utils import convert_bytes_string_to_string

from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindconverter.graph_based_converter.mapper.onnx.ops.conv_back_prop_input_mapper import \
    ConvBackPropInputMapper


class ConvTransposeMapper(ONNXToMindSporeMapper):
    """ConvTranspose mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        # MindSpore only support Conv2dTranspose.
        kernel_size = kwargs['params'].get('kernel_shape', tuple())
        dim = len(kernel_size)
        if dim == 3:
            return "nn.Conv3dTranspose"
        if dim != 2:
            raise ValueError("MindSpore only support Conv2dTranspose and Conv3dTranspose.")
        return "P.Conv2DBackpropInput"

    @staticmethod
    def _convert_params_for_raw_conv3dtranspose(**kwargs):
        """Convert params for Conv3dTranspose."""
        weights = kwargs["weights"]
        params = kwargs["params"]
        weight = ConvTransposeMapper._find_val_by_index(0, weights)
        bias = ConvTransposeMapper._find_val_by_index(1, weights)
        if weight is None:
            raise ValueError("ConvTranspose. Mapper cannot get the weight.")

        has_bias = isinstance(bias, np.ndarray)

        auto_pad = params.get("auto_pad")
        if auto_pad is not None:
            auto_pad = convert_bytes_string_to_string(auto_pad)

        dilation = params.get("dilations", 1)
        if isinstance(dilation, list):
            dilation = tuple(dilation)

        stride = params.get("strides", 1)
        if isinstance(stride, list):
            stride = tuple(params.get("strides"))

        kernel_size = params.get("kernel_shape")

        in_channels = weight.shape[0]
        out_channels = weight.shape[1] * params.get("group", 1)
        if len(kernel_size) == 1:
            kernel_size = kernel_size[0]
        else:
            kernel_size = tuple(kernel_size)

        pad_mode, padding = ConvBackPropInputMapper.convert_padding(params=params)
        if auto_pad == "SAME_UPPER":
            pad_mode = '\"same\"'
            padding = 0

        output_padding = params.get("output_padding", 0)
        if isinstance(output_padding, list):
            output_padding = tuple(output_padding)

        return {
            "in_channels": in_channels,
            "out_channels": out_channels,
            "kernel_size": kernel_size,
            "stride": stride,
            "padding": padding,
            "pad_mode": pad_mode,
            "output_padding": output_padding,
            "dilation": dilation,
            "group": params.get("group", 1),
            "has_bias": has_bias
        }

    @staticmethod
    def _convert_params(**kwargs):
        kernel_size = kwargs["params"].get("kernel_shape", 0)
        dim = len(kernel_size)
        if dim == 3:
            return ConvTransposeMapper._convert_params_for_raw_conv3dtranspose(**kwargs)
        if dim != 2:
            raise ValueError("MindSpore only support Conv2dTranspose and Conv3dTranspose.")
        return ConvBackPropInputMapper.convert_params(**kwargs)

    @staticmethod
    def _convert_trained_weights(**kwargs):
        kernel_size = kwargs["params"].get("kernel_shape", tuple())
        dim = len(kernel_size)
        if dim == 2:
            return ConvBackPropInputMapper.convert_trained_weights(**kwargs)

        weights = kwargs['weights']
        weight = ConvTransposeMapper._find_val_by_index(0, weights)
        bias = ConvTransposeMapper._find_val_by_index(1, weights)

        converted_weights = {'weight': {'data': weight}}
        if isinstance(bias, np.ndarray):
            converted_weights['bias'] = {'data': bias}

        return converted_weights

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        raw_params = kwargs.get("raw_params", dict())
        kernel_size = raw_params.get("kernel_shape")
        dim = len(kernel_size)
        if dim == 3:
            return template, exchange_msg, outputs_list, outputs_mapping

        return ConvBackPropInputMapper.generate_snippet_template(**kwargs)
