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
"""Definition of error code and relative messages in lineage module."""
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg


class LineageParamTypeError(MindInsightException):
    """The parameter type error in lineage module."""

    def __init__(self, msg):
        super(LineageParamTypeError, self).__init__(
            error=LineageErrors.PARAM_TYPE_ERROR,
            message=LineageErrorMsg.PARAM_TYPE_ERROR.value.format(msg)
        )


class LineageParamValueError(MindInsightException):
    """The parameter value error in lineage module."""

    def __init__(self, msg):
        super(LineageParamValueError, self).__init__(
            error=LineageErrors.PARAM_VALUE_ERROR,
            message=LineageErrorMsg.PARAM_VALUE_ERROR.value.format(msg)
        )


class LineageParamRunContextError(MindInsightException):
    """The input parameter run_context error in lineage module."""

    def __init__(self, msg):
        super(LineageParamRunContextError, self).__init__(
            error=LineageErrors.PARAM_RUN_CONTEXT_ERROR,
            message=LineageErrorMsg.PARAM_RUN_CONTEXT_ERROR.value.format(msg)
        )


class LineageGetModelFileError(MindInsightException):
    """The get model file error in lineage module."""

    def __init__(self, msg):
        super(LineageGetModelFileError, self).__init__(
            error=LineageErrors.LINEAGE_GET_MODEL_FILE_ERROR,
            message=LineageErrorMsg.LINEAGE_GET_MODEL_FILE_ERROR.value.format(msg)
        )


class LineageSummaryAnalyzeException(MindInsightException):
    """The summary analyze error in lineage module."""

    def __init__(self, msg=None):
        if msg is None:
            msg = ''
        super(LineageSummaryAnalyzeException, self).__init__(
            error=LineageErrors.SUMMARY_ANALYZE_ERROR,
            message=LineageErrorMsg.SUMMARY_ANALYZE_ERROR.value.format(msg)
        )


class LineageVerificationException(MindInsightException):
    """The summary verification error in lineage module."""
    def __init__(self, msg):
        super(LineageVerificationException, self).__init__(
            error=LineageErrors.SUMMARY_VERIFICATION_ERROR,
            message=LineageErrorMsg.SUMMARY_VERIFICATION_ERROR.value.format(msg)
        )


class LineageLogError(MindInsightException):
    """The lineage collector error."""
    def __init__(self, msg):
        super(LineageLogError, self).__init__(
            error=LineageErrors.LOG_LINEAGE_INFO_ERROR,
            message=LineageErrorMsg.LOG_LINEAGE_INFO_ERROR.value.format(msg)
        )


class LineageEventNotExistException(MindInsightException):
    """The querier error in lineage module."""

    def __init__(self):
        super(LineageEventNotExistException, self).__init__(
            error=LineageErrors.EVENT_NOT_EXIST_ERROR,
            message=LineageErrorMsg.EVENT_NOT_EXIST_ERROR.value
        )


class LineageQuerierParamException(MindInsightException):
    """The querier error in lineage module."""

    def __init__(self, *msg):
        super(LineageQuerierParamException, self).__init__(
            error=LineageErrors.QUERIER_PARAM_ERROR,
            message=LineageErrorMsg.QUERIER_PARAM_ERROR.value.format(*msg)
        )


class LineageSummaryParseException(MindInsightException):
    """The querier error in lineage module."""

    def __init__(self):
        super(LineageSummaryParseException, self).__init__(
            error=LineageErrors.SUMMARY_PARSE_FAIL_ERROR,
            message=LineageErrorMsg.SUMMARY_PARSE_FAIL_ERROR.value
        )


class LineageEventFieldNotExistException(MindInsightException):
    """The querier error in lineage module."""

    def __init__(self, msg):
        super(LineageEventFieldNotExistException, self).__init__(
            error=LineageErrors.EVENT_FIELD_NOT_EXIST_ERROR,
            message=LineageErrorMsg.EVENT_FIELD_NOT_EXIST_ERROR.value.format(msg)
        )


class LineageParamSummaryPathError(MindInsightException):
    """The lineage parameter summary path error."""
    def __init__(self, msg):
        super(LineageParamSummaryPathError, self).__init__(
            error=LineageErrors.LINEAGE_PARAM_SUMMARY_PATH_ERROR,
            message=LineageErrorMsg.LINEAGE_PARAM_SUMMARY_PATH_ERROR.value.format(msg)
        )


class LineageQuerySummaryDataError(MindInsightException):
    """Query summary data error in lineage module."""
    def __init__(self, msg):
        super(LineageQuerySummaryDataError, self).__init__(
            error=LineageErrors.LINEAGE_SUMMARY_DATA_ERROR,
            message=LineageErrorMsg.LINEAGE_SUMMARY_DATA_ERROR.value.format(msg)
        )


class LineageFileNotFoundError(MindInsightException):
    """Summary file not found in lineage module."""
    def __init__(self, msg):
        super(LineageFileNotFoundError, self).__init__(
            error=LineageErrors.LINEAGE_FILE_NOT_FOUND_ERROR,
            message=LineageErrorMsg.LINEAGE_FILE_NOT_FOUND_ERROR.value.format(msg)
        )


class LineageDirNotExistError(MindInsightException):
    """Directory not exist in lineage module."""
    def __init__(self, msg):
        super(LineageDirNotExistError, self).__init__(
            error=LineageErrors.LINEAGE_DIR_NOT_EXIST_ERROR,
            message=LineageErrorMsg.LINEAGE_DIR_NOT_EXIST_ERROR.value.format(msg)
        )


class LineageSearchConditionParamError(MindInsightException):
    """Search condition param is invalid in lineage module."""
    def __init__(self, msg):
        super(LineageSearchConditionParamError, self).__init__(
            error=LineageErrors.LINEAGE_SEARCH_CONDITION_PARAM_ERROR,
            message=LineageErrorMsg.LINEAGE_SEARCH_CONDITION_PARAM_ERROR.value.format(msg)
        )
