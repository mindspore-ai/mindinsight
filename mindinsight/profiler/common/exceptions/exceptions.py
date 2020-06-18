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
"""Definition of error code and relative messages in profiler module."""
from mindinsight.profiler.common.exceptions.error_code import ProfilerErrors, \
    ProfilerErrorMsg
from mindinsight.utils.exceptions import MindInsightException


class ProfilerParamValueErrorException(MindInsightException):
    """The parameter value error in profiler module."""

    def __init__(self, msg):
        super(ProfilerParamValueErrorException, self).__init__(
            error=ProfilerErrors.PARAM_VALUE_ERROR,
            message=ProfilerErrorMsg.PARAM_VALUE_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerPathErrorException(MindInsightException):
    """The path error in profiler module."""

    def __init__(self, msg):
        super(ProfilerPathErrorException, self).__init__(
            error=ProfilerErrors.PATH_ERROR,
            message=ProfilerErrorMsg.PATH_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerParamTypeErrorException(MindInsightException):
    """The parameter type error in profiler module."""

    def __init__(self, msg):
        super(ProfilerParamTypeErrorException, self).__init__(
            error=ProfilerErrors.PARAM_TYPE_ERROR,
            message=ProfilerErrorMsg.PARAM_TYPE_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerDirNotFoundException(MindInsightException):
    """The dir not found exception in profiler module."""

    def __init__(self, msg):
        super(ProfilerDirNotFoundException, self).__init__(
            error=ProfilerErrors.DIR_NOT_FOUND_ERROR,
            message=ProfilerErrorMsg.DIR_NOT_FOUND_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerFileNotFoundException(MindInsightException):
    """The file not found exception in profiler module."""

    def __init__(self, msg):
        super(ProfilerFileNotFoundException, self).__init__(
            error=ProfilerErrors.FILE_NOT_FOUND_ERROR,
            message=ProfilerErrorMsg.FILE_NOT_FOUND_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerIOException(MindInsightException):
    """The IO exception in profiler module."""

    def __init__(self):
        super(ProfilerIOException, self).__init__(
            error=ProfilerErrors.IO_ERROR,
            message=ProfilerErrorMsg.IO_ERROR.value,
            http_code=400
        )


class ProfilerDeviceIdMismatchException(MindInsightException):
    """The device id mismatch exception in profiler module."""

    def __init__(self):
        super(ProfilerDeviceIdMismatchException, self).__init__(
            error=ProfilerErrors.DEVICE_ID_MISMATCH_ERROR,
            message=ProfilerErrorMsg.DEVICE_ID_MISMATCH_ERROR.value,
            http_code=400
        )


class ProfilerRawFileException(MindInsightException):
    """The raw file exception in profiler module."""

    def __init__(self, msg):
        super(ProfilerRawFileException, self).__init__(
            error=ProfilerErrors.RAW_FILE_ERROR,
            message=ProfilerErrorMsg.RAW_FILE_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerColumnNotExistException(MindInsightException):
    """The column does not exist exception in profiler module."""

    def __init__(self, msg):
        super(ProfilerColumnNotExistException, self).__init__(
            error=ProfilerErrors.COLUMN_NOT_EXIST_ERROR,
            message=ProfilerErrorMsg.COLUMN_NOT_EXIST_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerAnalyserNotExistException(MindInsightException):
    """The analyser in profiler module."""

    def __init__(self, msg):
        super(ProfilerAnalyserNotExistException, self).__init__(
            error=ProfilerErrors.ANALYSER_NOT_EXIST_ERROR,
            message=ProfilerErrorMsg.ANALYSER_NOT_EXIST_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerDeviceIdException(MindInsightException):
    """The parameter device_id error in profiler module."""

    def __init__(self, msg):
        super(ProfilerDeviceIdException, self).__init__(
            error=ProfilerErrors.DEVICE_ID_ERROR,
            message=ProfilerErrorMsg.DEIVICE_ID_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerOpTypeException(MindInsightException):
    """The parameter op_type error in profiler module."""

    def __init__(self, msg):
        super(ProfilerOpTypeException, self).__init__(
            error=ProfilerErrors.OP_TYPE_ERROR,
            message=ProfilerErrorMsg.OP_TYPE_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerSortConditionException(MindInsightException):
    """The parameter sort_condition error in profiler module."""

    def __init__(self, msg):
        super(ProfilerSortConditionException, self).__init__(
            error=ProfilerErrors.SORT_CONDITION_ERROR,
            message=ProfilerErrorMsg.SORT_CONDITION_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerFilterConditionException(MindInsightException):
    """The parameter filer_condition error in profiler module."""

    def __init__(self, msg):
        super(ProfilerFilterConditionException, self).__init__(
            error=ProfilerErrors.FILTER_CONDITION_ERROR,
            message=ProfilerErrorMsg.FILTER_CONDITION_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerGroupConditionException(MindInsightException):
    """The parameter group_condition error in profiler module."""

    def __init__(self, msg):
        super(ProfilerGroupConditionException, self).__init__(
            error=ProfilerErrors.GROUP_CONDITION_ERROR,
            message=ProfilerErrorMsg.GROUP_CONDITION_ERROR.value.format(msg),
            http_code=400
        )


class ProfilerColumnNotSupportSortException(MindInsightException):
    """The column does not support to sort error in profiler module."""

    def __init__(self, msg):
        super(ProfilerColumnNotSupportSortException, self).__init__(
            error=ProfilerErrors.COLUMN_NOT_SUPPORT_SORT_ERROR,
            message=ProfilerErrorMsg.COLUMN_NOT_SUPPORT_SORT_ERROR.value.format(msg),
            http_code=400
        )


class StepNumNotSupportedException(MindInsightException):
    """The step number error in profiler module."""

    def __init__(self, msg):
        super(StepNumNotSupportedException, self).__init__(
            error=ProfilerErrors.STEP_NUM_NOT_SUPPORTED_ERROR,
            message=ProfilerErrorMsg.STEP_NUM_NOT_SUPPORTED_ERROR.value.format(msg),
            http_code=400
        )


class JobIdMismatchException(MindInsightException):
    """The Job ID mismatch error in profiler module."""

    def __init__(self):
        super(JobIdMismatchException, self).__init__(
            error=ProfilerErrors.JOB_ID_MISMATCH_ERROR,
            message=ProfilerErrorMsg.JOB_ID_MISMATCH_ERROR.value,
            http_code=400
        )


class ProfilerPipelineOpNotExistException(MindInsightException):
    """The minddata pipeline operator does not exist error in profiler module."""

    def __init__(self, msg):
        super(ProfilerPipelineOpNotExistException, self).__init__(
            error=ProfilerErrors.PIPELINE_OP_NOT_EXIST_ERROR,
            message=ProfilerErrorMsg.PIPELINE_OP_NOT_EXIST_ERROR.value.format(msg),
            http_code=400
        )
