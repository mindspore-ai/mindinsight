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
"""Define custom exception."""
from enum import unique

from mindinsight.utils.constant import ScriptConverterErrors
from mindinsight.utils.exceptions import MindInsightException


@unique
class ConverterErrors(ScriptConverterErrors):
    """Converter error codes."""
    SCRIPT_NOT_SUPPORT = 1
    NODE_TYPE_NOT_SUPPORT = 2
    CODE_SYNTAX_ERROR = 3
    NODE_INPUT_TYPE_NOT_SUPPORT = 4


class ScriptNotSupport(MindInsightException):
    """The script can not support to process."""

    def __init__(self, msg):
        super(ScriptNotSupport, self).__init__(ConverterErrors.SCRIPT_NOT_SUPPORT,
                                               msg,
                                               http_code=400)


class NodeTypeNotSupport(MindInsightException):
    """The astNode can not support to process."""

    def __init__(self, msg):
        super(NodeTypeNotSupport, self).__init__(ConverterErrors.NODE_TYPE_NOT_SUPPORT,
                                                 msg,
                                                 http_code=400)


class CodeSyntaxError(MindInsightException):
    """The CodeSyntaxError class definition."""

    def __init__(self, msg):
        super(CodeSyntaxError, self).__init__(ConverterErrors.CODE_SYNTAX_ERROR,
                                              msg,
                                              http_code=400)


class NodeInputTypeNotSupport(MindInsightException):
    """The node input type NOT support error."""

    def __init__(self, msg):
        super(NodeInputTypeNotSupport, self).__init__(ConverterErrors.NODE_INPUT_TYPE_NOT_SUPPORT,
                                                      msg,
                                                      http_code=400)
