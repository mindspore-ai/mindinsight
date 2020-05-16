# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Profiler error code and messages."""
from enum import unique, Enum

from mindinsight.utils.constant import ProfilerMgrErrors


_GENERAL_MASK = 0b00001 << 7
_PARSER_MASK = 0b00010 << 7
_ANALYSER_MASK = 0b00011 << 7


@unique
class ProfilerErrors(ProfilerMgrErrors):
    """Profiler error codes."""
    # general error code
    PARAM_VALUE_ERROR = 0 | _GENERAL_MASK
    PATH_ERROR = 1 | _GENERAL_MASK
    PARAM_TYPE_ERROR = 2 | _GENERAL_MASK
    DIR_NOT_FOUND_ERROR = 3 | _GENERAL_MASK
    FILE_NOT_FOUND_ERROR = 4 | _GENERAL_MASK
    IO_ERROR = 5 | _GENERAL_MASK

    # parser error code
    DEVICE_ID_MISMATCH_ERROR = 0 | _PARSER_MASK
    RAW_FILE_ERROR = 1 | _PARSER_MASK

    # analyser error code
    COLUMN_NOT_EXIST_ERROR = 0 | _ANALYSER_MASK
    ANALYSER_NOT_EXIST_ERROR = 1 | _ANALYSER_MASK


@unique
class ProfilerErrorMsg(Enum):
    """Profiler error messages."""
    # general error msg
    PARAM_VALUE_ERROR = 'Param value error. {}'
    PATH_ERROR = 'Path error. {}'
    PARAM_TYPE_ERROR = 'Param type error. {}'
    DIR_NOT_FOUND_ERROR = 'The dir <{}> not found.'
    FILE_NOT_FOUND_ERROR = 'The file <{}> not found.'
    IO_ERROR = 'Read or write file fail.'

    # parser error msg
    DEVICE_ID_MISMATCH_ERROR = 'The device ID mismatch.'
    RAW_FILE_ERROR = 'Raw file error. {}'

    # analyser error msg
    COLUMN_NOT_EXIST_ERROR = 'The column {} does not exist.'
    ANALYSER_NOT_EXIST_ERROR = 'The analyser {} does not exist.'
