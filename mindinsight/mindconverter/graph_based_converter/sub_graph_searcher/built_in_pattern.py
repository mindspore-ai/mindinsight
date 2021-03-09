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
"""Introduce some standard pattern into MindConverter."""

__all__ = ["BUILT_IN_PATTERN", "register_pattern", "is_built_in_pattern",
           "USER_DEFINED_PATTERN", "user_defined_pattern"]

from collections import OrderedDict

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.known_module_name import register_module_name

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import cal_matching_score
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.pattern import Pattern

BUILT_IN_PATTERN = dict()
USER_DEFINED_PATTERN = OrderedDict()


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
            return pattern
        if ptn_name in BUILT_IN_PATTERN:
            raise KeyError(f"{ptn_name} exists, `ptn_name` must be unique.")

        BUILT_IN_PATTERN[ptn_name] = Pattern("->".join(result), len(result),
                                             in_degree, out_degree,
                                             ptn_items=result)
        BUILT_IN_PATTERN[ptn_name].additional_score = cal_matching_score(BUILT_IN_PATTERN[ptn_name].ptn_length)
        BUILT_IN_PATTERN[ptn_name].ptn_name = ptn_name
        return pattern

    return _reg


def user_defined_pattern(pattern_name: str):
    """
    Register user define pattern to MindConverter.

    Args:
        pattern_name (str): Pattern name.
    """

    def _f(ptn):
        pattern = ptn()
        if not pattern:
            raise ValueError("`ptn` cannot be None.")
        if not pattern_name:
            raise ValueError("`pattern_name` cannot be None.")
        USER_DEFINED_PATTERN[pattern_name] = pattern
        return ptn

    return _f


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


@register_pattern("Multi-Head-Attention", 2, 1)
@register_module_name("MultiHeadAttn", 2, 1)
def _multi_head_attention():
    return [
        "MatMul", "Add", "MatMul", "Add", "Reshape", "MatMul", "Add", "Reshape",
        "Transpose", "Reshape", "Transpose", "Transpose", "MatMul", "Div", "Add", "Softmax",
        "MatMul", "Transpose", "Reshape", "MatMul", "Add"
    ]


@register_pattern("Multi-Head-Attention-1", 2, 1)
@register_module_name("MultiHeadAttn", 2, 1)
def _multi_head_attention_1():
    return [
        "MatMul", "Add", "MatMul", "Add", "MatMul", "Add", "Reshape",
        "Transpose", "Reshape", "Reshape", "Transpose", "Transpose", "MatMul", "Div", "Add",
        "Softmax", "MatMul", "Transpose", "Reshape", "MatMul", "Add"
    ]


@register_pattern("Multi-Head-Attention-with-Einsum", 2, 1)
@register_module_name("MultiHeadAttn", 2, 1)
def _multi_head_attention_with_einsum():
    return [
        "MatMul", "Add", "MatMul", "Add", "MatMul", "Add", "Reshape",
        "Transpose", "Reshape", "Reshape", "Transpose", "Transpose", "MatMul", "Div", "Add", "Softmax",
        "MatMul", "Transpose", "Einsum", "Add"
    ]


@register_pattern("Multi-Head-Attention-TF", 2, 1)
@register_module_name("MultiHeadAttn", 2, 1)
def _multi_head_attention_tf():
    return [
        "MatMul", "Reshape", "Transpose", "MatMul", "Reshape", "Transpose",
        "MatMul", "Reshape", "Transpose", "MatMul",
        "Mul", "Add", "Softmax", "MatMul", "Transpose", "Reshape", "MatMul"
    ]


@register_pattern("Layer-Normalization", 1, 1)
@register_module_name("LayerNorm", 1, 1)
def _layer_norm():
    return [
        "ReduceMean", "Sub", "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add"
    ]


@register_pattern("Layer-Normalization-TF", 1, 1)
@register_module_name("LayerNorm", 1, 1)
def _layer_norm_tf():
    return [
        "ReduceMean", "Sub", "Mul", "ReduceMean", "Add", "Sqrt", "Reciprocal", "Mul", "Mul", "Neg", "Mul", "Add"
    ]


@register_pattern("Feed-Forward-Network-TF", 1, 1)
@register_module_name("FFN", 1, 1)
def _ffn_tf():
    return [
        "MatMul", "Pow", "Mul", "Add", "Mul", "Tanh", "Add", "Mul", "Mul", "MatMul"
    ]


@register_pattern("Layer-Normalization-with-cast", 1, 1)
@register_module_name("LayerNorm", 1, 1)
def _layer_norm_with_cast():
    return [
        "ReduceMean", "Sub", "Cast", "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add"
    ]


@register_pattern("GeLU", 1, 1)
@register_module_name("GeLU", 1, 1)
def _gelu():
    return [
        "Div", "Erf", "Add", "Mul", "Mul"
    ]


@register_pattern("Linear", 1, 1)
@register_module_name("Linear", 1, 1)
def _linear():
    return [
        "MatMul", "Add"
    ]


@register_pattern("New-GeLU", 1, 1)
@register_module_name("NewGeLU", 1, 1)
def _new_gelu():
    return [
        "Mul", "Pow", "Mul", "Add", "Mul", "Tanh", "Add", "Mul"
    ]
