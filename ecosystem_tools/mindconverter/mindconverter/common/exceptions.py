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
"""Define custom exception."""
import abc
import sys
from enum import unique, Enum
from importlib import import_module

from lib2to3.pgen2 import parse

from mindconverter.common.log import MindConverterLogger


@unique
class ConverterErrors(Enum):
    """Converter error codes."""
    SCRIPT_NOT_SUPPORT = 1
    NODE_TYPE_NOT_SUPPORT = 2
    CODE_SYNTAX_ERROR = 3
    CONVERT_FROM_UI_ERRORS = 4

    BASE_CONVERTER_FAIL = 000
    GRAPH_INIT_FAIL = 100
    SOURCE_FILES_SAVE_FAIL = 200
    GENERATOR_FAIL = 300
    SUB_GRAPH_SEARCHING_FAIL = 400


class MindConverterAstException(Exception):
    """
    Base class for MindInsight exception.

    Examples:
        >>> raise MindConverterAstException(GeneralErrors.PATH_NOT_EXISTS_ERROR, 'path not exists')
        >>> raise MindConverterAstException(DataVisualErrors.CUSTOMIZED_ERROR, 'datavisual error message')
    """

    RUNTIME = 1
    TYPE = 1
    LEVEL = 0
    SYSID = 42
    MODULE = 7

    def __init__(self, error, message):
        """
        Initialization of MindConverterAstException.

        Args:
            error (Enum): Error value for specified case.
            message (str): Description for exception.
        """
        if isinstance(message, str):
            message = ' '.join(message.split())
        super(MindConverterAstException, self).__init__(message)
        self.error = error
        self.message = message

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

        num = (((0xFF & self.RUNTIME) << 30)
               | ((0xFF & self.TYPE) << 28)
               | ((0xFF & self.LEVEL) << 25)
               | ((0xFF & self.SYSID) << 17)
               | ((0xFF & self.MODULE) << 12)
               | (0x0FFF & self.error.value))

        return hex(num)[2:].zfill(8).upper()

    def __str__(self):
        return '[{}] code: {}, msg: {}'.format(self.__class__.__name__, self.error_code, self.message)


class ScriptNotSupport(MindConverterAstException):
    """The script can not support to process."""

    def __init__(self, msg):
        super(ScriptNotSupport, self).__init__(ConverterErrors.SCRIPT_NOT_SUPPORT, msg)


class NodeTypeNotSupport(MindConverterAstException):
    """The astNode can not support to process."""

    def __init__(self, msg):
        super(NodeTypeNotSupport, self).__init__(ConverterErrors.NODE_TYPE_NOT_SUPPORT, msg)


class CodeSyntaxError(MindConverterAstException):
    """The CodeSyntaxError class definition."""

    def __init__(self, msg):
        super(CodeSyntaxError, self).__init__(ConverterErrors.CODE_SYNTAX_ERROR, msg)


class ConvertFromUIError(MindConverterAstException):
    """The ConvertFromUIError class definition"""

    def __init__(self, msg):
        super(ConvertFromUIError, self).__init__(ConverterErrors.CONVERT_FROM_UI_ERRORS, msg)


class MindConverterException(Exception):
    """MindConverter exception."""
    BASE_ERROR_CODE = None  # ConverterErrors.BASE_CONVERTER_FAIL.value
    # ERROR_CODE should be declared in child exception.
    ERROR_CODE = None

    def __init__(self, **kwargs):
        """Initialization of MindConverterException."""
        user_msg = kwargs.get('user_msg', '')

        if isinstance(user_msg, str):
            user_msg = ' '.join(user_msg.split())

        super(MindConverterException, self).__init__()
        self.user_msg = user_msg
        self.root_exception_error_code = None

    def __str__(self):
        return '[{}] code: {}, msg: {}'.format(self.__class__.__name__, self.error_code(), self.user_msg)

    def __repr__(self):
        return self.__str__()

    def error_code(self):
        """"
        Calculate error code.

        code compose(2bytes)
        error: 16bits.
        num = 0xFFFF & error
        error_cods

        Returns:
            str, Hex string representing the composed MindConverter error code.
        """
        if self.root_exception_error_code:
            return self.root_exception_error_code
        if self.BASE_ERROR_CODE is None or self.ERROR_CODE is None:
            raise ValueError("MindConverterException has not been initialized.")
        num = 0xFFFF & self.ERROR_CODE  # 0xFFFF & self.error.value
        error_code = f"{str(self.BASE_ERROR_CODE).zfill(3)}{hex(num)[2:].zfill(4).upper()}"
        return error_code

    @classmethod
    @abc.abstractmethod
    def raise_from(cls):
        """Raise from below exceptions."""

    @classmethod
    def normalize_error_msg(cls, error_msg):
        """Normalize error msg for common python exception."""
        if cls.BASE_ERROR_CODE is None or cls.ERROR_CODE is None:
            raise ValueError("MindConverterException has not been initialized.")
        num = 0xFFFF & cls.ERROR_CODE  # 0xFFFF & self.error.value
        error_code = f"{str(cls.BASE_ERROR_CODE).zfill(3)}{hex(num)[2:].zfill(4).upper()}"
        return f"[{cls.__name__}] code: {error_code}, msg: {error_msg}"

    @classmethod
    def uniform_catcher(cls, msg: str = ""):
        """Uniform exception catcher."""
        get_lib_notice_info = getattr(import_module("mindconverter.graph_based_converter.common.utils"),
                                      "get_lib_notice_info")

        def decorator(func):
            def _f(*args, **kwargs):
                try:
                    res = func(*args, **kwargs)
                except cls.raise_from() as e:
                    error = cls() if not msg else cls(msg=msg)
                    detail_info = str(e)
                    if not isinstance(e, MindConverterException):
                        detail_info = cls.normalize_error_msg(str(e))

                    MindConverterLogger.error(detail_info)
                    MindConverterLogger.error(error, console=False)
                    MindConverterLogger.exception(e, console=False)
                    MindConverterLogger.warning(get_lib_notice_info())
                    sys.exit(-1)
                except ModuleNotFoundError as e:
                    detail_info = "Error detail: Required package not found, please check the runtime environment."
                    MindConverterLogger.error(f"{str(e)}\n{detail_info}")
                    MindConverterLogger.exception(e, console=False)
                    MindConverterLogger.warning(get_lib_notice_info())
                    sys.exit(-1)
                return res

            return _f

        return decorator

    @classmethod
    def check_except(cls, msg, added_except=None):
        """Check except."""

        def decorator(func):
            def _f(*args, **kwargs):
                raise_from = cls.raise_from() + (added_except,) if added_except else cls.raise_from()
                try:
                    output = func(*args, **kwargs)
                except raise_from as e:
                    error = cls(msg=msg)
                    error_code = e.error_code() if isinstance(e, MindConverterException) else None
                    error.root_exception_error_code = error_code
                    MindConverterLogger.error(msg)
                    MindConverterLogger.exception(e, console=False)
                    raise error
                except Exception as e:
                    MindConverterLogger.error(msg)
                    MindConverterLogger.exception(e, console=False)
                    raise e
                return output

            return _f

        return decorator


class BaseConverterError(MindConverterException):
    """Base converter failed."""

    @unique
    class ErrCode(Enum):
        """Define error code of BaseConverterError."""
        UNKNOWN_ERROR = 0
        UNKNOWN_MODEL = 1
        PARAM_MISSING = 2
        BAD_PARAM = 3

    BASE_ERROR_CODE = ConverterErrors.BASE_CONVERTER_FAIL.value
    ERROR_CODE = ErrCode.UNKNOWN_ERROR.value
    DEFAULT_MSG = "Failed to start base converter."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(BaseConverterError, self).__init__(user_msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = Exception, UnknownModelError, ParamMissingError, cls
        return except_source


class UnknownModelError(BaseConverterError):
    """The unknown model error."""
    ERROR_CODE = BaseConverterError.ErrCode.UNKNOWN_MODEL.value

    def __init__(self, msg, **kwargs):
        super(UnknownModelError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        return cls


class ParamMissingError(BaseConverterError):
    """Define cli params missing error."""
    ERROR_CODE = BaseConverterError.ErrCode.PARAM_MISSING.value

    def __init__(self, msg, **kwargs):
        super(ParamMissingError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        return cls


class BadParamError(BaseConverterError):
    """Define cli bad params error."""
    ERROR_CODE = BaseConverterError.ErrCode.BAD_PARAM.value

    def __init__(self, msg, **kwargs):
        super(BadParamError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        return cls


class GraphInitError(MindConverterException):
    """The graph init fail error."""

    @unique
    class ErrCode(Enum):
        """Define error code of GraphInitError."""
        UNKNOWN_ERROR = 0
        MODEL_LOADING_ERROR = 1
        TF_RUNTIME_ERROR = 2
        MI_RUNTIME_ERROR = 3

    BASE_ERROR_CODE = ConverterErrors.GRAPH_INIT_FAIL.value
    ERROR_CODE = ErrCode.UNKNOWN_ERROR.value
    DEFAULT_MSG = "Error occurred when init graph object."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(GraphInitError, self).__init__(user_msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (FileNotFoundError,
                         ModuleNotFoundError,
                         ModelLoadingError,
                         RuntimeIntegrityError,
                         TypeError,
                         ZeroDivisionError,
                         RuntimeError,
                         cls)
        return except_source


class FileSaveError(MindConverterException):
    """The source files save fail error."""

    @unique
    class ErrCode(Enum):
        """Define error code of SourceFilesSaveError."""
        UNKNOWN_ERROR = 0
        NODE_INPUT_TYPE_NOT_SUPPORT = 1
        SCRIPT_GENERATE_FAIL = 2
        REPORT_GENERATE_FAIL = 3
        CKPT_GENERATE_FAIL = 4
        MAP_GENERATE_FAIL = 5
        MODEL_SAVE_FAIL = 6

    BASE_ERROR_CODE = ConverterErrors.SOURCE_FILES_SAVE_FAIL.value
    ERROR_CODE = ErrCode.UNKNOWN_ERROR.value
    DEFAULT_MSG = "Error occurred when save source files."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(FileSaveError, self).__init__(user_msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (NodeInputTypeNotSupportError,
                         ScriptGenerationError,
                         ReportGenerationError,
                         CheckPointGenerationError,
                         WeightMapGenerationError,
                         OnnxModelSaveError,
                         IOError, cls)
        return except_source


class ModelLoadingError(GraphInitError):
    """The model not support error."""

    ERROR_CODE = GraphInitError.ErrCode.MODEL_LOADING_ERROR.value

    def __init__(self, msg, **kwargs):
        super(ModelLoadingError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        onnxruntime_error = getattr(import_module('onnxruntime.capi'), 'onnxruntime_pybind11_state')
        except_source = (RuntimeError,
                         ModuleNotFoundError,
                         ValueError,
                         AssertionError,
                         TypeError,
                         OSError,
                         ZeroDivisionError,
                         onnxruntime_error.Fail,
                         onnxruntime_error.InvalidArgument,
                         onnxruntime_error.NoSuchFile,
                         onnxruntime_error.NoModel,
                         onnxruntime_error.EngineError,
                         onnxruntime_error.RuntimeException,
                         onnxruntime_error.InvalidProtobuf,
                         onnxruntime_error.ModelLoaded,
                         onnxruntime_error.NotImplemented,
                         onnxruntime_error.InvalidGraph,
                         onnxruntime_error.EPFail,
                         cls)
        return except_source


class TfRuntimeError(GraphInitError):
    """Catch tf runtime error."""
    ERROR_CODE = GraphInitError.ErrCode.TF_RUNTIME_ERROR.value
    DEFAULT_MSG = "Error occurred when init graph, TensorFlow runtime error."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(TfRuntimeError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        tf_error_module = import_module('tensorflow.python.framework.errors_impl')
        tf_error = getattr(tf_error_module, 'OpError')
        return tf_error, ValueError, RuntimeError, cls


class RuntimeIntegrityError(GraphInitError):
    """Catch runtime error."""
    ERROR_CODE = GraphInitError.ErrCode.MI_RUNTIME_ERROR.value

    def __init__(self, msg, **kwargs):
        super(RuntimeIntegrityError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        return RuntimeError, AttributeError, ImportError, ModuleNotFoundError, cls


class NodeInputTypeNotSupportError(FileSaveError):
    """The node input type NOT support error."""
    ERROR_CODE = FileSaveError.ErrCode.NODE_INPUT_TYPE_NOT_SUPPORT.value

    def __init__(self, msg, **kwargs):
        super(NodeInputTypeNotSupportError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        return ValueError, TypeError, IndexError, cls


class ScriptGenerationError(FileSaveError):
    """The script generate fail error."""
    ERROR_CODE = FileSaveError.ErrCode.SCRIPT_GENERATE_FAIL.value

    def __init__(self, msg, **kwargs):
        super(ScriptGenerationError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (RuntimeError,
                         parse.ParseError,
                         AttributeError, cls)
        return except_source


class ReportGenerationError(FileSaveError):
    """The report generate fail error."""
    ERROR_CODE = FileSaveError.ErrCode.REPORT_GENERATE_FAIL.value

    def __init__(self, msg, **kwargs):
        super(ReportGenerationError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        return ZeroDivisionError, cls


class CheckPointGenerationError(FileSaveError):
    """The checkpoint generate fail error."""
    ERROR_CODE = FileSaveError.ErrCode.CKPT_GENERATE_FAIL.value

    def __init__(self, msg, **kwargs):
        super(CheckPointGenerationError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        return cls


class WeightMapGenerationError(FileSaveError):
    """The weight names map generate fail error."""
    ERROR_CODE = FileSaveError.ErrCode.MAP_GENERATE_FAIL.value

    def __init__(self, msg, **kwargs):
        super(WeightMapGenerationError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exception below."""
        return cls


class OnnxModelSaveError(FileSaveError):
    """The onnx model save fail error."""
    ERROR_CODE = FileSaveError.ErrCode.MODEL_SAVE_FAIL.value

    def __init__(self, msg, **kwargs):
        super(OnnxModelSaveError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exception below."""
        return cls


class SubGraphSearchingError(MindConverterException):
    """Sub-graph searching exception."""

    @unique
    class ErrCode(Enum):
        """Define error code of SourceFilesSaveError."""
        BASE_ERROR = 0
        PATTERN_REG_CONFLICT_ERROR = 1
        PATTERN_INVALID_ERROR = 2
        MODULE_NAME_INVALID_ERROR = 3

    BASE_ERROR_CODE = ConverterErrors.SUB_GRAPH_SEARCHING_FAIL.value
    ERROR_CODE = ErrCode.BASE_ERROR.value
    DEFAULT_MSG = "Sub-Graph pattern searching fail."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(SubGraphSearchingError, self).__init__(user_msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Define exception in sub-graph searching module."""
        return IndexError, KeyError, ValueError, AttributeError, ZeroDivisionError, cls


class PatternConflictError(SubGraphSearchingError):
    """Pattern conflict exception for user defined pattern."""
    ERROR_CODE = SubGraphSearchingError.ErrCode.PATTERN_REG_CONFLICT_ERROR.value

    def __init__(self, msg, **kwargs):
        super(PatternConflictError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Define exception in sub-graph searching module."""
        return KeyError, ValueError, cls


class PatternInvalidError(SubGraphSearchingError):
    """Registered pattern is invalid for user defined pattern."""
    ERROR_CODE = SubGraphSearchingError.ErrCode.PATTERN_INVALID_ERROR.value

    def __init__(self, msg, **kwargs):
        super(PatternInvalidError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Define exception in sub-graph searching module."""
        return KeyError, ValueError, cls


class ModuleNameDefineError(SubGraphSearchingError):
    """Registered module name is invalid."""
    ERROR_CODE = SubGraphSearchingError.ErrCode.MODULE_NAME_INVALID_ERROR.value

    def __init__(self, msg, **kwargs):
        super(ModuleNameDefineError, self).__init__(msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """It will be raised when user-define module name is invalid."""
        return cls


class GeneratorError(MindConverterException):
    """The Generator fail error."""

    @unique
    class ErrCode(Enum):
        """Define error code of SourceFilesSaveError."""
        BASE_ERROR = 0
        STATEMENT_GENERATION_ERROR = 1
        CONVERTED_OPERATOR_LOADING_ERROR = 2

    BASE_ERROR_CODE = ConverterErrors.GENERATOR_FAIL.value
    ERROR_CODE = ErrCode.BASE_ERROR.value
    DEFAULT_MSG = "Error occurred when generate code."

    def __init__(self, msg=DEFAULT_MSG, **kwargs):
        super(GeneratorError, self).__init__(user_msg=msg, **kwargs)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (ValueError, TypeError, SyntaxError, cls)
        return except_source
