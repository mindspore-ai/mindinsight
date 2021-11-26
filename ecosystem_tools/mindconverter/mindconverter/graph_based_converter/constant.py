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
import os
import stat

import numpy as np

AUTO_DETECT_NODES = True

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

UNKNOWN_SHAPE_WITHOUT_PRECURSOR_NODES = -2
DYNAMIC_SHAPE = -1
SCALAR_WITHOUT_SHAPE = 0
UNKNOWN_DIM_VAL = "unk__001"

ONNX_MIN_VER = "1.8.0"
TF2ONNX_MIN_VER = "1.7.1"
ONNXRUNTIME_MIN_VER = "1.5.2"
ONNXOPTIMIZER_MIN_VER = "0.1.2"
ONNXOPTIMIZER_MAX_VER = "0.1.2"
MINDSPORE_MIN_VER = "1.2.0"
TENSORFLOW_MIN_VER = "1.15.0"
TORCH_MIN_VER = "1.8.2"
TORCH_MAX_VER = "1.8.2"
CHECKPOINT_SEGMENT_SIZE = 2040109465  # 1.9GB, no more than 2GB

WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL
RW_MODE_FOR_OWNER = stat.S_IRUSR | stat.S_IWUSR
RWX_MODE_FOR_OWNER = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

MAIN_CLASS_NAME = "MindSporeModel"

MAX_INT = 9223372036854775807

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

ONNX_MS_MAP = {1: 'mindspore.float32',
               2: 'mindspore.uint8',
               3: 'mindspore.int8',
               4: 'mindspore.uint16',
               5: 'mindspore.int16',
               6: 'mindspore.int32',
               7: 'mindspore.int64',
               8: 'mindspore.string',
               9: 'mindspore.bool_',
               10: 'mindspore.float16',
               11: 'mindspore.double',
               12: 'mindspore.uint32',
               13: 'mindspore.uint64',
               14: 'UNSUPPORTED',
               15: 'UNSUPPORTED',
               16: 'UNSUPPORTED'}

PYTORCH_MS_MAP = {
    "default": "mindspore.float32",
    0: "mindspore.uint8",
    1: "mindspore.int8",
    2: "mindspore.int16",
    3: "mindspore.int32",
    4: "mindspore.int64",
    5: "mindspore.float16",
    6: "mindspore.float32",
    7: "mindspore.float64",
    11: "mindspore.bool_"
}

MS_DATA_EDGE = 0

OUTPUT_PROTO_TYPE = "Output"


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

ARGUMENT_LENGTH_LIMIT = 255

ARGUMENT_NUM_LIMIT = 32

ARGUMENT_LEN_LIMIT = 64

EXPECTED_NUMBER = 1

MIN_SCOPE_LENGTH = 2

ONNX_OPSET_VERSION = 11

NO_CONVERTED_OPERATORS = [
    "onnx::Constant",
    "Constant"
]

UNCONVERTED_ATEN_OPERATORS = [
    "aten::Int",
    "aten::contiguous",
    "aten::ScalarImplicit"
]

THIRD_PART_VERSION = {
    "onnx": (ONNX_MIN_VER,),
    "onnxruntime": (ONNXRUNTIME_MIN_VER,),
    "onnxoptimizer": (ONNXOPTIMIZER_MIN_VER,),
    "tf2onnx": (TF2ONNX_MIN_VER,),
    "mindspore": (MINDSPORE_MIN_VER,),
    "tensorflow": (TENSORFLOW_MIN_VER,),
    "torch": (TORCH_MIN_VER, TORCH_MAX_VER)
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
    PYTORCH = 3


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
           f"import mindspore.numpy as ms_np{NEW_LINE}" \
           f"import mindspore.ops as P{NEW_LINE}" \
           f"from mindspore import nn{NEW_LINE}" \
           f"from mindspore import Tensor, Parameter{NEW_LINE * 3}"


@unique
class ONNXAttributeType(Enum):
    """The ONNX AttributeProto data type enum."""
    UNDEFINED = 0
    FLOAT = 1
    INT = 2
    STRING = 3
    TENSOR = 4
    GRAPH = 5
    SPARSE_TENSOR = 11
    TYPE_PROTO = 13

    FLOATS = 6
    INTS = 7
    STRINGS = 8
    TENSORS = 9
    GRAPHS = 10
    SPARSE_TENSORS = 12
    TYPE_PROTOS = 14


@unique
class ONNXTensorType(Enum):
    """The ONNX TensorProto data type enum."""
    UNDEFINED = 0
    FLOAT = 1
    UINT8 = 2
    INT8 = 3
    UINT16 = 4
    INT16 = 5
    INT32 = 6
    INT64 = 7
    STRING = 8
    BOOL = 9

    FLOAT16 = 10

    DOUBLE = 11
    UINT32 = 12
    UINT64 = 13
    COMPLEX64 = 14

    BFLOAT16 = 16


@unique
class MSDataType(Enum):
    """The MSGraph data type enum."""
    DT_UNDEFINED = 0
    DT_BOOL = 1
    DT_INT8 = 2
    DT_INT16 = 3
    DT_INT32 = 4
    DT_INT64 = 5
    DT_UINT8 = 6
    DT_UINT16 = 7
    DT_UINT32 = 8
    DT_UINT64 = 9
    DT_FLOAT16 = 10
    DT_FLOAT32 = 11
    DT_FLOAT64 = 12
    DT_STRING = 13
    DT_TENSOR = 14
    DT_GRAPH = 15
    DT_BOOLS = 16
    DT_INTS8 = 17
    DT_INTS16 = 18
    DT_INTS32 = 19
    DT_INTS64 = 20
    DT_UINTS8 = 21
    DT_UINTS16 = 22
    DT_UINTS32 = 23
    DT_UINTS64 = 24
    DT_FLOATS16 = 25
    DT_FLOATS32 = 26
    DT_FLOATS64 = 27
    DT_STRINGS = 28
    DT_TENSORS = 29
    DT_GRAPHS = 30
    DT_TUPLE = 31
    DT_LIST = 32
    DT_DICT = 33
    DT_NONE = 34
    DT_SYM_INST = 35
    DT_BASE_INT = 36
    DT_BASE_UINT = 37
    DT_BASE_FLOAT = 38
    DT_TYPE = 39
    DT_ANYTHING = 40
    DT_REFKEY = 41
    DT_REF = 42
