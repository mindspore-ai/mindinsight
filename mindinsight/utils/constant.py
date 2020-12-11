# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Constant module."""


from enum import Enum


class MindInsightModules(Enum):
    """
    Enum definition for MindInsight error types.

    Note:
        Each enum value, excluding GENERAL, has an Errors class name starting with the enum value
        in Camel-Case referring to specific module.
    """
    GENERAL = 0
    LINEAGEMGR = 2
    DATAVISUAL = 5
    PROFILERMGR = 6
    SCRIPTCONVERTER = 7
    WIZARD = 9
    OPTIMIZER = 10
    DEBUGGER = 11


class GeneralErrors(Enum):
    """Enum definition for general errors."""
    UNKNOWN_ERROR = 0
    PARAM_TYPE_ERROR = 1
    PARAM_VALUE_ERROR = 2
    PARAM_MISSING_ERROR = 3
    PATH_NOT_EXISTS_ERROR = 4
    FILE_SYSTEM_PERMISSION_ERROR = 8
    PORT_NOT_AVAILABLE_ERROR = 9
    URL_DECODE_ERROR = 10
    COMPUTING_RESOURCE_ERROR = 11


class ProfilerMgrErrors(Enum):
    """Enum definition for profiler errors."""


class LineageMgrErrors(Enum):
    """Enum definition for lineage errors."""


class DebuggerErrors(Enum):
    """Enum definition for debugger errors."""


class DataVisualErrors(Enum):
    """Enum definition for datavisual errors."""
    RESTFUL_API_NOT_EXIST = 1
    REQUEST_METHOD_NOT_ALLOWED = 2
    MAX_COUNT_EXCEEDED_ERROR = 3
    CRC_FAILED = 4
    TRAIN_JOB_NOT_EXIST = 5
    SUMMARY_LOG_PATH_INVALID = 6
    SUMMARY_LOG_IS_LOADING = 7
    NODE_NOT_IN_GRAPH_ERROR = 9
    PATH_NOT_DIRECTORY_ERROR = 10
    PLUGIN_NOT_AVAILABLE = 11
    GRAPH_NOT_EXIST = 12
    IMAGE_NOT_EXIST = 13
    SCALAR_NOT_EXIST = 14
    HISTOGRAM_NOT_EXIST = 15
    TRAIN_JOB_DETAIL_NOT_IN_CACHE = 16
    QUERY_STRING_CONTAINS_NULL_BYTE = 17
    TENSOR_NOT_EXIST = 18
    MAX_RESPONSE_DATA_EXCEEDED_ERROR = 19
    STEP_TENSOR_DATA_NOT_IN_CACHE = 20
    CRC_LENGTH_FAILED = 21
    TENSOR_TOO_LARGE = 22


class ScriptConverterErrors(Enum):
    """Enum definition for mindconverter errors."""


class WizardErrors(Enum):
    """Enum definition for mindwizard errors."""


class OptimizerErrors(Enum):
    """Enum definition for optimizer errors."""
    SAMPLES_NOT_ENOUGH = 1
    CORRELATION_NAN = 2
    HYPER_CONFIG_ERROR = 3
    OPTIMIZER_TERMINATE = 4
    CONFIG_PARAM_ERROR = 5
    HYPER_CONFIG_ENV_ERROR = 6
