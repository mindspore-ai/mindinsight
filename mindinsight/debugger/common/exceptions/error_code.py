# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Debugger error code and messages."""
from enum import Enum, unique
from mindinsight.utils.constant import DebuggerErrors as DebuggerErrorCodes


_PARAM_ERROR_MASK = 0b00001 << 7
_DEBUGGER_GRAPH_ERROR = 0b00010 << 7
_DEBUGGER_RUNNING_ERROR = 0b00011 << 7
_DEBUGGER_SERVER_ERROR = 0b00100 << 7
_DEBUGGER_SESSION_ERROR = 0b00101 << 7


@unique
class DebuggerErrors(DebuggerErrorCodes):
    """Debugger error codes."""
    PARAM_TYPE_ERROR = 0 | _PARAM_ERROR_MASK
    PARAM_VALUE_ERROR = 1 | _PARAM_ERROR_MASK
    STEP_NUM_ERROR = 2 | _PARAM_ERROR_MASK
    DEBUGGER_CONDITION_UNAVAILABLE_ERROR = 3 | _PARAM_ERROR_MASK

    NODE_NOT_IN_GRAPH_ERROR = 0 | _DEBUGGER_GRAPH_ERROR
    GRAPH_NOT_EXIST_ERROR = 1 | _DEBUGGER_GRAPH_ERROR

    CREATE_WATCHPOINT_ERROR = 0 | _DEBUGGER_RUNNING_ERROR
    UPDATE_WATCHPOINT_ERROR = 1 | _DEBUGGER_RUNNING_ERROR
    DELETE_WATCHPOINT_ERROR = 2 | _DEBUGGER_RUNNING_ERROR
    CONTINUE_ERROR = 3 | _DEBUGGER_RUNNING_ERROR
    PAUSE_ERROR = 4 | _DEBUGGER_RUNNING_ERROR
    COMPARE_TENSOR_ERROR = 5 | _DEBUGGER_RUNNING_ERROR
    RECHECK_ERROR = 6 | _DEBUGGER_RUNNING_ERROR
    TENSOR_GRAPH_ERROR = 7 | _DEBUGGER_RUNNING_ERROR
    TENSOR_HIT_ERROR = 8 | _DEBUGGER_RUNNING_ERROR
    SET_RECOMMEND_WATCHPOINT_ERROR = 9 | _DEBUGGER_RUNNING_ERROR

    DEBUGGER_SERVER_RUNNING_ERROR = 0 | _DEBUGGER_SERVER_ERROR
    DEVICE_ID_UNREGISTERED = 1 | _DEBUGGER_SERVER_ERROR
    MODULE_NOT_FOUND_ERROR = 2 | _DEBUGGER_SERVER_ERROR

    DEBUGGER_SESSION_OVER_BOUND_ERROR = 0 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_SESSION_NOT_FOUND_ERROR = 1 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_ONLINE_SESSION_UNAVAILABLE = 2 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_DOWNLOAD_OVER_QUEUE = 3 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_DOWNLOAD_TENSOR_NOT_EXIST = 4 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_RANK_DIR_NOT_FOUND = 5 | _DEBUGGER_SESSION_ERROR
    DEBUGGER_JSON_FILE_PARSE_ERROR = 6 | _DEBUGGER_SESSION_ERROR


@unique
class DebuggerErrorMsg(Enum):
    """Debugger error messages."""
    PARAM_TYPE_ERROR = "TypeError. {}"
    PARAM_VALUE_ERROR = "ValueError. {}"
    DEBUGGER_CONDITION_UNAVAILABLE_ERROR = "Condition is unavailable. {}"

    GRAPH_NOT_EXIST_ERROR = "The graph does not exist."

    CREATE_WATCHPOINT_ERROR = "Create watchpoint failed. {}"
    UPDATE_WATCHPOINT_ERROR = "Update watchpoint failed. {}"
    DELETE_WATCHPOINT_ERROR = "Delete watchpoint failed. {}"
    CONTINUE_ERROR = "Continue debugging failed. {}"
    PAUSE_ERROR = "Pause debugging failed. {}"
    RECHECK_ERROR = "Recheck failed. {}"
    TENSOR_GRAPH_ERROR = "Get tensor graphs failed."
    TENSOR_HIT_ERROR = "Get tensor hits failed."
    SET_RECOMMEND_WATCHPOINT_ERROR = "Set Recommend Watchpoints failed."

    DEBUGGER_SERVER_RUNNING_ERROR = "Debugger server running error. {}"
    DEVICE_ID_UNREGISTERED = "Device id unregistered. Device id: {}"
    MODULE_NOT_FOUND_ERROR = "{} module not found."

    DEBUGGER_SESSION_OVER_BOUND_ERROR = "The amount of sessions is over limitation."
    DEBUGGER_SESSION_NOT_FOUND_ERROR = "Session {} not found."
    DEBUGGER_ONLINE_SESSION_UNAVAILABLE = "Online session is unavailable."
    DEBUGGER_DOWNLOAD_OVER_QUEUE = "There is already a tensor in download"
    DEBUGGER_DOWNLOAD_TENSOR_NOT_EXIST = "No such tensor to download"
    DEBUGGER_RANK_DIR_NOT_FOUND = "No rank directory found under {}."
    DEBUGGER_JSON_FILE_PARSE_ERROR = "Failed to parse the json files. {}"
