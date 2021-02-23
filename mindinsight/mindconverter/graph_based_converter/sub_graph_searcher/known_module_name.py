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
"""Introduce some standard pattern name into MindConverter."""

__all__ = ["register_module_name", "is_built_in_module_name", "BUILT_IN_MODULE_NAME"]

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.pattern import Pattern

PLACEHOLDER = "PLC"
BUILT_IN_MODULE_NAME = dict()


def is_built_in_module_name(module_name: str):
    """
    Whether the module name was built-in.

    Args:
        module_name (str): Module name.

    Returns:
        bool, true or false.
    """
    return module_name.split("_")[0] in BUILT_IN_MODULE_NAME


def register_module_name(md_name: str, in_degree: int, out_degree: int):
    """
    Register pattern to MindConverter.

    Args:
        out_degree (int): Out degree of pattern.
        in_degree (int): In degree of pattern.
        md_name (str): Module name.

    """

    def _reg(pattern):
        result = pattern()
        if not result:
            return pattern
        BUILT_IN_MODULE_NAME[Pattern("->".join(result), len(result),
                                     in_degree, out_degree,
                                     ptn_items=result)] = md_name
        return pattern

    return _reg


@register_module_name("Bottleneck", 1, 2)
def _resnet_block_0():
    """Add ResNet feature extraction block pattern."""
    return ["Conv", "BatchNormalization", "Relu",
            "Conv", "BatchNormalization", "Relu",
            "Conv", "BatchNormalization", "Add", "Relu"]


@register_module_name("Bottleneck", 1, 2)
def _resnet_block_1():
    """Add ResNet feature extraction block pattern."""
    return [PLACEHOLDER, PLACEHOLDER, "Conv", "BatchNormalization", "Add", "Relu"]


@register_module_name("Bottleneck", 1, 2)
def _resnet_block_2():
    """Add ResNet feature extraction block pattern."""
    return [PLACEHOLDER, PLACEHOLDER, PLACEHOLDER, "Add", "Relu"]


@register_module_name("BasicConvBlock", 1, 1)
def _basic_conv_block_0():
    """Add basic conv block."""
    return ["Conv", "BatchNormalization", "Relu"]


@register_module_name("ConvBN", 1, 1)
def _conv_bn():
    """Add basic conv block."""
    return ["Conv", "BatchNormalization"]


@register_module_name("UnSample", 1, 1)
def _up_sampling_in_op12():
    return [
        "Shape", "Slice", "Gather", "Cast", "Slice", "Mul", "Cast", "Concat", "Resize"
    ]


@register_module_name("UnSample", 1, 1)
def _up_sampling_in_op10():
    return [
        "Shape", "Gather", "Cast", "Slice", "Mul", "Slice", "Cast", "Cast", "Div", "Concat", "Resize"
    ]
