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
"""Define custom exception."""
from enum import unique

from mindinsight.utils.constant import WizardErrors
from mindinsight.utils.exceptions import MindInsightException


@unique
class WizardErrorCodes(WizardErrors):
    """Wizard error codes."""
    CODE_SYNTAX_ERROR = 1
    OS_PERMISSION_ERROR = 2
    COMMAND_ERROR = 3
    TEMPLATE_FILE_ERROR = 4


class CodeSyntaxError(MindInsightException):
    """The CodeSyntaxError class definition."""
    def __init__(self, msg):
        super(CodeSyntaxError, self).__init__(WizardErrorCodes.CODE_SYNTAX_ERROR, msg)


class OSPermissionError(MindInsightException):
    def __init__(self, msg):
        super(OSPermissionError, self).__init__(WizardErrorCodes.OS_PERMISSION_ERROR, msg)


class CommandError(MindInsightException):
    def __init__(self, msg):
        super(CommandError, self).__init__(WizardErrorCodes.COMMAND_ERROR, msg)


class TemplateFileError(MindInsightException):
    def __init__(self, msg):
        super(TemplateFileError, self).__init__(WizardErrorCodes.TEMPLATE_FILE_ERROR, msg)
