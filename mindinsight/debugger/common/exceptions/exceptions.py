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
"""Definition of error code and relative messages in debugger module."""
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.debugger.common.exceptions.error_code import DebuggerErrors, DebuggerErrorMsg


class DebuggerParamTypeError(MindInsightException):
    """The parameter type error in debugger module."""

    def __init__(self, msg):
        super(DebuggerParamTypeError, self).__init__(
            error=DebuggerErrors.PARAM_TYPE_ERROR,
            message=DebuggerErrorMsg.PARAM_TYPE_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerParamValueError(MindInsightException):
    """The parameter value error in debugger module."""

    def __init__(self, msg):
        super(DebuggerParamValueError, self).__init__(
            error=DebuggerErrors.PARAM_VALUE_ERROR,
            message=DebuggerErrorMsg.PARAM_VALUE_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerCreateWatchPointError(MindInsightException):
    """The error about creating watch point."""

    def __init__(self, msg):
        super(DebuggerCreateWatchPointError, self).__init__(
            error=DebuggerErrors.CREATE_WATCHPOINT_ERROR,
            message=DebuggerErrorMsg.CREATE_WATCHPOINT_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerUpdateWatchPointError(MindInsightException):
    """The error about updating watch point."""

    def __init__(self, msg):
        super(DebuggerUpdateWatchPointError, self).__init__(
            error=DebuggerErrors.UPDATE_WATCHPOINT_ERROR,
            message=DebuggerErrorMsg.UPDATE_WATCHPOINT_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerDeleteWatchPointError(MindInsightException):
    """The error about deleting watch point."""

    def __init__(self, msg):
        super(DebuggerDeleteWatchPointError, self).__init__(
            error=DebuggerErrors.DELETE_WATCHPOINT_ERROR,
            message=DebuggerErrorMsg.DELETE_WATCHPOINT_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerRecheckError(MindInsightException):
    """The error about deleting watch point."""

    def __init__(self, msg):
        super(DebuggerRecheckError, self).__init__(
            error=DebuggerErrors.RECHECK_ERROR,
            message=DebuggerErrorMsg.RECHECK_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerCompareTensorError(MindInsightException):
    """The error about comparing tensors."""

    def __init__(self, msg):
        super(DebuggerCompareTensorError, self).__init__(
            error=DebuggerErrors.COMPARE_TENSOR_ERROR,
            message=msg,
            http_code=400
        )


class DebuggerContinueError(MindInsightException):
    """The error about continuing debugging."""
    def __init__(self, msg):
        super(DebuggerContinueError, self).__init__(
            error=DebuggerErrors.CONTINUE_ERROR,
            message=DebuggerErrorMsg.CONTINUE_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerPauseError(MindInsightException):
    """The error about pausing debugging."""
    def __init__(self, msg):
        super(DebuggerPauseError, self).__init__(
            error=DebuggerErrors.PAUSE_ERROR,
            message=DebuggerErrorMsg.PAUSE_ERROR.value.format(msg),
            http_code=400
        )


class DebuggerNodeNotInGraphError(MindInsightException):
    """The node is not in the graph."""
    def __init__(self, node_name, node_type=None):
        if node_type is not None:
            err_msg = f"Cannot find the node in graph by the given name. node name: {node_name}, type: {node_type}."
        else:
            err_msg = f"Cannot find the node in graph by the given name. node name: {node_name}."
        super(DebuggerNodeNotInGraphError, self).__init__(
            error=DebuggerErrors.NODE_NOT_IN_GRAPH_ERROR,
            message=err_msg,
            http_code=400
        )


class DebuggerGraphNotExistError(MindInsightException):
    """The graph does not exist."""
    def __init__(self):
        super(DebuggerGraphNotExistError, self).__init__(
            error=DebuggerErrors.GRAPH_NOT_EXIST_ERROR,
            message=DebuggerErrorMsg.GRAPH_NOT_EXIST_ERROR.value,
            http_code=400
        )


class DebuggerStepNumError(MindInsightException):
    """The graph does not exist."""
    def __init__(self):
        super(DebuggerStepNumError, self).__init__(
            error=DebuggerErrors.STEP_NUM_ERROR,
            message="The type of step number should be int32.",
            http_code=400
        )


class DebuggerTensorGraphError(MindInsightException):
    """The error about comparing tensors."""

    def __init__(self):
        super(DebuggerTensorGraphError, self).__init__(
            error=DebuggerErrors.TENSOR_GRAPH_ERROR,
            message=DebuggerErrorMsg.TENSOR_GRAPH_ERROR.value,
            http_code=400
        )


class DebuggerTensorHitError(MindInsightException):
    """The error about comparing tensors."""

    def __init__(self):
        super(DebuggerTensorHitError, self).__init__(
            error=DebuggerErrors.TENSOR_HIT_ERROR,
            message=DebuggerErrorMsg.TENSOR_HIT_ERROR.value,
            http_code=400
        )


class DebuggerSetRecommendWatchpointsError(MindInsightException):
    """The set recommend watchpoints error in debugger module."""

    def __init__(self):
        super(DebuggerSetRecommendWatchpointsError, self).__init__(
            error=DebuggerErrors.SET_RECOMMEND_WATCHPOINT_ERROR,
            message=DebuggerErrorMsg.SET_RECOMMEND_WATCHPOINT_ERROR.value,
            http_code=400
        )


class DebuggerConditionUnavailableError(MindInsightException):
    """The condition unavailable error in debugger module."""

    def __init__(self, msg):
        super(DebuggerConditionUnavailableError, self).__init__(
            error=DebuggerErrors.DEBUGGER_CONDITION_UNAVAILABLE_ERROR,
            message=DebuggerErrorMsg.DEBUGGER_CONDITION_UNAVAILABLE_ERROR.value.format(msg),
            http_code=400
        )
