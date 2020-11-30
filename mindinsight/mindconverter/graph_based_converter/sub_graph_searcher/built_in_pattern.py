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
"""Introduce some standard pattern into MindConverter."""

__all__ = ["BUILT_IN_PATTERN", "register_pattern", "is_built_in_pattern"]

from .common import cal_matching_score
from .pattern import Pattern

BUILT_IN_PATTERN = dict()


def is_built_in_pattern(pattern: Pattern):
    """
    Whether the module name was built-in.

    Args:
        pattern (Pattern): Found pattern.

    Returns:
        bool, true or false.
    """
    for ptn in BUILT_IN_PATTERN:
        if BUILT_IN_PATTERN[ptn].ptn_length == pattern.ptn_length and \
                BUILT_IN_PATTERN[ptn].in_degree == pattern.in_degree and \
                BUILT_IN_PATTERN[ptn].out_degree == pattern.out_degree and \
                BUILT_IN_PATTERN[ptn].ptn_items == pattern.ptn_items:
            return True
    return False


def register_pattern(ptn_name, in_degree, out_degree):
    """
    Register pattern to MindConverter.

    Notes:
        The `out_degree` of pattern refers to the out-edge number in original graph,
        not the output number of the pattern.

    Args:
        out_degree: Out degree of pattern.
        in_degree: In degree of pattern.
        ptn_name (str): Pattern name.

    """

    def _reg(pattern):
        result = pattern()
        if not result:
            return
        BUILT_IN_PATTERN[ptn_name] = Pattern("->".join(result), len(result),
                                             in_degree, out_degree,
                                             ptn_items=result)
        BUILT_IN_PATTERN[ptn_name].additional_score = cal_matching_score(BUILT_IN_PATTERN[ptn_name].ptn_length)

    return _reg


@register_pattern("ConvBnClip", 1, 1)
def _conv_bn_clip():
    """Add conv-bn-clip pattern."""
    return ["Conv", "BatchNormalization", "Clip"]


@register_pattern("ConvBnRL", 1, 1)
def _conv_bn_relu():
    """Add conv-bn-relu pattern."""
    return ["Conv", "BatchNormalization", "Relu"]


@register_pattern("ConvBnConvBnClip", 1, 1)
def _conv_bn_conv_bn_clip():
    """Add conv-bn-conv-bn-clip pattern."""
    return ["Conv", "BatchNormalization", "Conv", "BatchNormalization", "Clip"]


@register_pattern("ConvBnConvBnRL", 1, 1)
def _conv_bn_conv_bn_relu():
    """Add conv-bn-conv-bn-relu pattern."""
    return ["Conv", "BatchNormalization", "Conv", "BatchNormalization", "Relu"]


@register_pattern("ConvBnReLUx2+ConvBn+Add+Relu", 1, 2)
def _convbnrelux3_convbn_add_relu():
    """Add pattern."""
    return ["Conv", "BatchNormalization", "Relu",
            "Conv", "BatchNormalization", "Relu",
            "Conv", "BatchNormalization", "Add", "Relu"]


@register_pattern("UnSampling-op12", 1, 1)
def _up_sampling_in_op12():
    return [
        "Shape", "Slice", "Gather", "Cast", "Slice", "Mul", "Cast", "Concat", "Resize"
    ]


@register_pattern("UpSampling-op10", 1, 1)
def _up_sampling_in_op10():
    return [
        "Shape", "Gather", "Cast", "Slice", "Mul", "Slice", "Cast", "Cast", "Div", "Concat", "Resize"
    ]
