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
"""Constant definition."""
from enum import Enum, unique

SEPARATOR_IN_ONNX_OP = "::"
SEPARATOR_IN_SCOPE = "/"
SEPARATOR_BTW_NAME_AND_ID = "_"
LINK_IN_SCOPE = "-"
LEFT_BUCKET = "["
RIGHT_BUCKET = "]"

BLANK_SYM = " "
FIRST_LEVEL_INDENT = BLANK_SYM * 4
SECOND_LEVEL_INDENT = BLANK_SYM * 8
NEW_LINE = "\n"

MINI_FREQUENCY = 4

ONNX_TYPE_INT = 2
ONNX_TYPE_INTS = 7
ONNX_TYPE_FLOAT = 1
ONNX_TYPE_FLOATS = 6
ONNX_TYPE_STRING = 3


@unique
class CodeFormatConfig(Enum):
    PEP8 = "pep8"


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
