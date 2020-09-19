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
"""Exception module."""

from importlib import import_module
from mindinsight.utils.constant import MindInsightModules, GeneralErrors


class MindInsightException(Exception):
    """
    Base class for MindInsight exception.

    Examples:
        >>> raise MindInsightException(GeneralErrors.PATH_NOT_EXISTS_ERROR, 'path not exists')
        >>> raise MindInsightException(DataVisualErrors.CUSTOMIZED_ERROR, 'datavisual error message')
    """

    RUNTIME = 1
    TYPE = 1
    LEVEL = 0
    SYSID = 42

    def __init__(self, error, message, http_code=400):
        """
        Initialization of MindInsightException.

        Args:
            error (Enum): Error value for specified case.
            message (str): Description for exception.
            http_code (int): Http code for exception. Default is 400.
        """
        if isinstance(message, str):
            message = ' '.join(message.split())
        super(MindInsightException, self).__init__(message)
        self.error = error
        self.message = message
        self.http_code = http_code

    def parse_module(self):
        """
        Parse module according to error enum class.

        Note:
            Each enum value, excluding GENERAL, has an Errors class name starting with the enum value
            in Camel-Case referring to specific module.

        Returns:
            Enum, module for specified error.
        """

        module = None
        constant = import_module('mindinsight.utils.constant')
        errors_names = [item for item in dir(constant) if item.endswith('Errors')]
        for name in errors_names:
            errors_cls = getattr(constant, name)
            if isinstance(self.error, errors_cls):
                key = name[:-len('Errors')].upper()
                module = getattr(MindInsightModules, key, None)
                break

        return module

    @property
    def error_code(self):
        """
        Transform exception no to MindInsight error code.

        code compose(4bytes):
        runtime 2bits, type 2bits, level 3bits, sysid 8bits, modid 5bits, value 12bits.

        num = ((0xFF & runtime) << 30) \
                | ((0xFF & type) << 28) \
                | ((0xFF & level) << 25) \
                | ((0xFF & sysid) << 17) \
                | ((0xFF & modid) << 12) \
                | (0x0FFF & value)

        Returns:
            str, Hex string representing the composed MindInsight error code.
        """

        module = self.parse_module()
        if not module:
            raise UnknownError('Unknown module for {}.'.format(self.error))

        num = (((0xFF & self.RUNTIME) << 30)
               | ((0xFF & self.TYPE) << 28)
               | ((0xFF & self.LEVEL) << 25)
               | ((0xFF & self.SYSID) << 17)
               | ((0xFF & module.value) << 12)
               | (0x0FFF & self.error.value))

        return hex(num)[2:].zfill(8).upper()

    def __str__(self):
        return '[{}] code: {}, msg: {}'.format(self.__class__.__name__, self.error_code, self.message)


class ParamValueError(MindInsightException):
    """Request param value error."""
    def __init__(self, error_detail):
        error_msg = 'Invalid parameter value. {}'.format(error_detail)
        super(ParamValueError, self).__init__(
            GeneralErrors.PARAM_VALUE_ERROR,
            error_msg,
            http_code=400)


class ParamTypeError(MindInsightException):
    """Request param type error."""
    def __init__(self, param_name, expected_type):
        error_msg = "Invalid parameter type. '{}' expect {} type.".format(param_name, expected_type)
        super(ParamTypeError, self).__init__(
            GeneralErrors.PARAM_TYPE_ERROR,
            error_msg,
            http_code=400)


class ParamMissError(MindInsightException):
    """Missing param error."""
    def __init__(self, param_name):
        error_msg = "Param missing. '{}' is required.".format(param_name)
        super(ParamMissError, self).__init__(
            GeneralErrors.PARAM_MISSING_ERROR,
            error_msg,
            http_code=400)


class PathNotExistError(MindInsightException):
    """Raised when specified path do not exist."""
    def __init__(self, error_detail):
        """Initialize PathNotExistError."""
        error_msg = 'Specified path does not exist. Detail: {}'.format(error_detail)
        super(PathNotExistError, self).__init__(
            GeneralErrors.PATH_NOT_EXISTS_ERROR,
            error_msg,
            http_code=400)


class FileSystemPermissionError(MindInsightException):
    """Can not access file or dir."""
    def __init__(self, error_detail):
        error_msg = 'File or dir access failed. Detail: {}'.format(error_detail)
        super(FileSystemPermissionError, self).__init__(
            GeneralErrors.FILE_SYSTEM_PERMISSION_ERROR,
            error_msg,
            http_code=400)


class PortNotAvailableError(MindInsightException):
    """Port not available error.."""
    def __init__(self, error_detail):
        error_msg = 'Port not available error. Detail: {}'.format(error_detail)
        super(PortNotAvailableError, self).__init__(
            GeneralErrors.PORT_NOT_AVAILABLE_ERROR,
            error_msg,
            http_code=400)


class UnknownError(MindInsightException):
    """Unknown error."""
    def __init__(self, error_msg):
        super(UnknownError, self).__init__(
            GeneralErrors.UNKNOWN_ERROR,
            error_msg,
            http_code=500)


class UrlDecodeError(MindInsightException):
    """Url decoding failed"""
    def __init__(self, error_detail):
        error_msg = f"Url decode failed. Detail: {error_detail}"
        super(UrlDecodeError, self).__init__(GeneralErrors.URL_DECODE_ERROR,
                                             error_msg,
                                             http_code=400)
