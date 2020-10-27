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
from .pattern import Pattern

BUILT_IN_PATTERN = dict()


def register_pattern(ptn_name, in_degree, out_degree):
    """
    Register pattern to MindConverter.

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


__all__ = ["BUILT_IN_PATTERN", "register_pattern"]
