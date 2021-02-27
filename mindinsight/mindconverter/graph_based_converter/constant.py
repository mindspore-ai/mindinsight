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
"""Constant definition."""
from enum import Enum, unique

import numpy as np

SEPARATOR_IN_ONNX_OP = "::"
SEPARATOR_IN_SCOPE = "/"
SEPARATOR_BTW_NAME_AND_ID = "_"
SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT = "="
LINK_IN_SCOPE = "-"
LINK_IN_WEIGHT_NAME = "."
LEFT_BUCKET = "["
RIGHT_BUCKET = "]"

BLANK_SYM = " "
FIRST_LEVEL_INDENT = BLANK_SYM * 4
SECOND_LEVEL_INDENT = BLANK_SYM * 8
NEW_LINE = "\n"

ONNX_TYPE_INT = 2
ONNX_TYPE_INTS = 7
ONNX_TYPE_FLOAT = 1
ONNX_TYPE_FLOATS = 6
ONNX_TYPE_STRING = 3

DYNAMIC_SHAPE = -1
SCALAR_WITHOUT_SHAPE = 0
UNKNOWN_DIM_VAL = "unk__001"

ONNX_MIN_VER = "1.8.0"
TF2ONNX_MIN_VER = "1.7.1"
ONNXRUNTIME_MIN_VER = "1.5.2"
ONNXOPTIMIZER_MIN_VER = "0.1.2"
ONNXOPTIMIZER_MAX_VER = "0.1.2"


DTYPE_MAP = {
    1: np.float32,
    2: np.uint8,
    3: np.int8,
    4: np.uint16,
    5: np.int16,
    6: np.int32,
    7: np.int64,
    8: str,
    9: bool,
    10: np.float16,
    11: np.double,
    12: np.uint32,
    13: np.uint64,
    14: np.complex64,
    15: np.complex128,
    16: None
}


@unique
class TemplateKeywords(Enum):
    """Define keywords in template message."""
    INIT = "init"
    CONSTRUCT = "construct"


@unique
class ExchangeMessageKeywords(Enum):
    """Define keywords in exchange message."""
    METADATA = "metadata"

    @unique
    class MetadataScope(Enum):
        """Define metadata scope keywords in exchange message."""
        SOURCE = "source"
        OPERATION = "operation"
        INPUTS = "inputs"
        INPUTS_SHAPE = "inputs_shape"
        OUTPUTS = "outputs"
        OUTPUTS_SHAPE = "outputs_shape"
        PRECURSOR = "precursor_nodes"
        SUCCESSOR = "successor_nodes"
        ATTRS = "attributes"
        SCOPE = "scope"

    @unique
    class VariableScope(Enum):
        """Define variable scope keywords in exchange message."""
        OPERATION = "operation"
        VARIABLE_NAME = "variable_name"
        OUTPUT_TYPE = "output_type"
        TSR_TYPE = "tensor"
        ARR_TYPE = "array"
        INPUTS = "inputs"
        ARGS = "args"
        WEIGHTS = "weights"
        TRAINABLE_PARAMS = "trainable_params"
        PARAMETERS_DECLARED = "parameters"
        GROUP_INPUTS = "group_inputs"


ONNX_MODEL_SUFFIX = "onnx"
TENSORFLOW_MODEL_SUFFIX = "pb"
BINARY_HEADER_PYTORCH_BITS = 32

ARGUMENT_LENGTH_LIMIT = 128

ARGUMENT_NUM_LIMIT = 32

ARGUMENT_LEN_LIMIT = 64

EXPECTED_NUMBER = 1

MIN_SCOPE_LENGTH = 2

ONNX_OPSET_VERSION = 11


NO_CONVERTED_OPERATORS = [
    "onnx::Constant",
    "Constant"
]

THIRD_PART_VERSION = {
    "onnx": (ONNX_MIN_VER,),
    "onnxruntime": (ONNXRUNTIME_MIN_VER,),
    "onnxoptimizer": (ONNXOPTIMIZER_MIN_VER,),
    "tf2onnx": (TF2ONNX_MIN_VER,)
}


@unique
class NodeType(Enum):
    MODULE = "module"
    OPERATION = "operation"
    CLASS = "class"
    FUNC = "func"
    INPUTS = "DataInput"


@unique
class InputType(Enum):
    TENSOR = "tensor"
    LIST = "list"


@unique
class FrameworkType(Enum):
    ONNX = 0
    TENSORFLOW = 1
    UNKNOWN = 2


@unique
class WeightType(Enum):
    PARAMETER = 0
    COMMON = 1


def get_imported_module():
    """
    Generate imported module header.

    Returns:
        str, imported module.
    """
    return f"import numpy as np{NEW_LINE}" \
           f"import mindspore{NEW_LINE}" \
           f"import mindspore.ops as P{NEW_LINE}" \
           f"from mindspore import nn{NEW_LINE}" \
           f"from mindspore import Tensor, Parameter{NEW_LINE * 3}"
