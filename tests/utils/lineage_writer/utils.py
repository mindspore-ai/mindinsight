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
"""Lineage writer utils."""
from functools import wraps

from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg
from mindinsight.utils.exceptions import MindInsightException


class LineageParamRunContextError(MindInsightException):
    """The input parameter run_context error in lineage module."""

    def __init__(self, msg):
        super(LineageParamRunContextError, self).__init__(
            error=LineageErrors.PARAM_RUN_CONTEXT_ERROR,
            message=LineageErrorMsg.PARAM_RUN_CONTEXT_ERROR.value.format(msg),
            http_code=400
        )


class LineageGetModelFileError(MindInsightException):
    """The get model file error in lineage module."""

    def __init__(self, msg):
        super(LineageGetModelFileError, self).__init__(
            error=LineageErrors.LINEAGE_GET_MODEL_FILE_ERROR,
            message=LineageErrorMsg.LINEAGE_GET_MODEL_FILE_ERROR.value.format(msg),
            http_code=400
        )


class LineageLogError(MindInsightException):
    """The lineage collector error."""
    def __init__(self, msg):
        super(LineageLogError, self).__init__(
            error=LineageErrors.LOG_LINEAGE_INFO_ERROR,
            message=LineageErrorMsg.LOG_LINEAGE_INFO_ERROR.value.format(msg),
            http_code=400
        )


def try_except(logger):
    """
    Catch or raise exceptions while collecting lineage.

    Args:
        logger (logger): The logger instance which logs the warning info.

    Returns:
        function, the decorator which we use to retry the decorated function.
    """
    def try_except_decorate(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except (AttributeError, MindInsightException,
                    LineageParamRunContextError, LineageLogError,
                    LineageGetModelFileError, IOError) as err:
                logger.error(err)

                try:
                    raise_except = self.raise_exception
                except AttributeError:
                    raise_except = False

                if raise_except is True:
                    raise

        return wrapper
    return try_except_decorate
