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
import abc
import sys
from enum import unique
from importlib import import_module

from lib2to3.pgen2 import parse
from treelib.exceptions import DuplicatedNodeIdError, MultipleRootError, NodeIDAbsentError

from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console

from mindinsight.utils.constant import ScriptConverterErrors
from mindinsight.utils.exceptions import MindInsightException


@unique
class ConverterErrors(ScriptConverterErrors):
    """Converter error codes."""
    SCRIPT_NOT_SUPPORT = 1
    NODE_TYPE_NOT_SUPPORT = 2
    CODE_SYNTAX_ERROR = 3
    NODE_INPUT_TYPE_NOT_SUPPORT = 4
    NODE_INPUT_MISSING = 5
    TREE_NODE_INSERT_FAIL = 6
    UNKNOWN_MODEL = 7
    MODEL_NOT_SUPPORT = 8
    SCRIPT_GENERATE_FAIL = 9
    REPORT_GENERATE_FAIL = 10
    NODE_CONVERSION_ERROR = 11
    INPUT_SHAPE_ERROR = 12
    TF_RUNTIME_ERROR = 13

    BASE_CONVERTER_FAIL = 000
    GRAPH_INIT_FAIL = 100
    TREE_CREATE_FAIL = 200
    SOURCE_FILES_SAVE_FAIL = 300
    GENERATOR_FAIL = 400
    SUB_GRAPH_SEARCHING_FAIL = 500
    MODEL_LOADING_FAIL = 600


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


class MindConverterException(Exception):
    """MindConverter exception."""

    def __init__(self, **kwargs):
        """Initialization of MindInsightException."""
        error = kwargs.get('error', None)
        user_msg = kwargs.get('user_msg', '')
        debug_msg = kwargs.get('debug_msg', '')
        cls_code = kwargs.get('cls_code', 0)

        if isinstance(user_msg, str):
            user_msg = ' '.join(user_msg.split())
        super(MindConverterException, self).__init__()
        self.error = error
        self.user_msg = user_msg
        self.debug_msg = debug_msg
        self.cls_code = cls_code

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
        num = 0xFFFF & self.error.value
        error_code = ''.join((f'{self.cls_code}'.zfill(3), hex(num)[2:].zfill(4).upper()))
        return error_code

    @classmethod
    @abc.abstractmethod
    def raise_from(cls):
        """Raise from below exceptions."""

    @classmethod
    def uniform_catcher(cls, msg):
        """Uniform exception catcher."""

        def decorator(func):
            def _f(*args, **kwargs):
                try:
                    res = func(*args, **kwargs)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    detail_info = f"Error detail: {str(e)}"
                    log_console.error(str(error))
                    log_console.error(detail_info)
                    log.exception(e)
                    sys.exit(0)
                except ModuleNotFoundError as e:
                    detail_info = f"Error detail: Required package not found, please check the runtime environment."
                    log_console.error(str(e))
                    log_console.error(detail_info)
                    log.exception(e)
                    sys.exit(0)
                return res

            return _f

        return decorator

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(*args, **kwargs):
                try:
                    output = func(*args, **kwargs)
                except cls.raise_from() as e:
                    log.error(msg)
                    log.exception(e)
                    raise cls(msg=msg)
                except Exception as e:
                    log.error(msg)
                    log.exception(e)
                    raise e
                return output

            return _f

        return decorator


class BaseConverterFail(MindConverterException):
    """Base converter failed."""

    def __init__(self, msg):
        super(BaseConverterFail, self).__init__(error=ConverterErrors.BASE_CONVERTER_FAIL,
                                                user_msg=msg)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = Exception, cls
        return except_source


class UnknownModel(MindConverterException):
    """The unknown model error."""

    def __init__(self, msg):
        super(UnknownModel, self).__init__(error=ConverterErrors.UNKNOWN_MODEL,
                                           user_msg=msg)

    @classmethod
    def raise_from(cls):
        return cls


class GraphInitFail(MindConverterException):
    """The graph init fail error."""

    def __init__(self, **kwargs):
        super(GraphInitFail, self).__init__(error=ConverterErrors.GRAPH_INIT_FAIL,
                                            user_msg=kwargs.get('msg', ''))

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (FileNotFoundError,
                         ModuleNotFoundError,
                         ModelNotSupport,
                         SubGraphSearchingFail,
                         TypeError,
                         ZeroDivisionError,
                         RuntimeError,
                         cls)
        return except_source


class TreeCreateFail(MindConverterException):
    """The tree create fail."""

    def __init__(self, msg):
        super(TreeCreateFail, self).__init__(error=ConverterErrors.TREE_CREATE_FAIL,
                                             user_msg=msg)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (NodeInputMissing,
                         TreeNodeInsertFail, cls)
        return except_source


class SourceFilesSaveFail(MindConverterException):
    """The source files save fail error."""

    def __init__(self, msg):
        super(SourceFilesSaveFail, self).__init__(error=ConverterErrors.SOURCE_FILES_SAVE_FAIL,
                                                  user_msg=msg)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (NodeInputTypeNotSupport,
                         ScriptGenerateFail,
                         ReportGenerateFail,
                         IOError, cls)
        return except_source


class ModelNotSupport(MindConverterException):
    """The model not support error."""

    def __init__(self, msg):
        super(ModelNotSupport, self).__init__(error=ConverterErrors.MODEL_NOT_SUPPORT,
                                              user_msg=msg,
                                              cls_code=ConverterErrors.GRAPH_INIT_FAIL.value)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (RuntimeError,
                         ModuleNotFoundError,
                         ValueError,
                         AssertionError,
                         TypeError,
                         OSError,
                         ZeroDivisionError, cls)
        return except_source


class TfRuntimeError(MindConverterException):
    """Catch tf runtime error."""

    def __init__(self, msg):
        super(TfRuntimeError, self).__init__(error=ConverterErrors.TF_RUNTIME_ERROR,
                                             user_msg=msg,
                                             cls_code=ConverterErrors.GRAPH_INIT_FAIL.value)

    @classmethod
    def raise_from(cls):
        tf_error_module = import_module('tensorflow.python.framework.errors_impl')
        tf_error = getattr(tf_error_module, 'OpError')
        return tf_error, ValueError, RuntimeError, cls


class NodeInputMissing(MindConverterException):
    """The node input missing error."""

    def __init__(self, msg):
        super(NodeInputMissing, self).__init__(error=ConverterErrors.NODE_INPUT_MISSING,
                                               user_msg=msg,
                                               cls_code=ConverterErrors.TREE_CREATE_FAIL.value)

    @classmethod
    def raise_from(cls):
        return ValueError, IndexError, KeyError, AttributeError, cls


class TreeNodeInsertFail(MindConverterException):
    """The tree node create fail error."""

    def __init__(self, msg):
        super(TreeNodeInsertFail, self).__init__(error=ConverterErrors.TREE_NODE_INSERT_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.TREE_CREATE_FAIL.value)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (OSError,
                         DuplicatedNodeIdError,
                         MultipleRootError,
                         NodeIDAbsentError, cls)
        return except_source


class NodeInputTypeNotSupport(MindConverterException):
    """The node input type NOT support error."""

    def __init__(self, msg):
        super(NodeInputTypeNotSupport, self).__init__(error=ConverterErrors.NODE_INPUT_TYPE_NOT_SUPPORT,
                                                      user_msg=msg,
                                                      cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)

    @classmethod
    def raise_from(cls):
        return ValueError, TypeError, IndexError, cls


class ScriptGenerateFail(MindConverterException):
    """The script generate fail error."""

    def __init__(self, msg):
        super(ScriptGenerateFail, self).__init__(error=ConverterErrors.SCRIPT_GENERATE_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (RuntimeError,
                         parse.ParseError,
                         AttributeError, cls)
        return except_source


class ReportGenerateFail(MindConverterException):
    """The report generate fail error."""

    def __init__(self, msg):
        super(ReportGenerateFail, self).__init__(error=ConverterErrors.REPORT_GENERATE_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        return ZeroDivisionError, cls


class SubGraphSearchingFail(MindConverterException):
    """Sub-graph searching exception."""

    def __init__(self, msg):
        super(SubGraphSearchingFail, self).__init__(error=ConverterErrors.MODEL_NOT_SUPPORT,
                                                    cls_code=ConverterErrors.SUB_GRAPH_SEARCHING_FAIL.value,
                                                    user_msg=msg)

    @classmethod
    def raise_from(cls):
        """Define exception in sub-graph searching module."""
        return IndexError, KeyError, ValueError, AttributeError, ZeroDivisionError, cls


class GeneratorFail(MindConverterException):
    """The Generator fail error."""

    def __init__(self, msg):
        super(GeneratorFail, self).__init__(error=ConverterErrors.NODE_CONVERSION_ERROR,
                                            user_msg=msg,
                                            cls_code=ConverterErrors.GENERATOR_FAIL.value)

    @classmethod
    def raise_from(cls):
        """Raise from exceptions below."""
        except_source = (ValueError, TypeError, cls)
        return except_source


class ModelLoadingFail(MindConverterException):
    """Model loading fail."""

    def __init__(self, msg):
        super(ModelLoadingFail, self).__init__(error=ConverterErrors.INPUT_SHAPE_ERROR,
                                               cls_code=ConverterErrors.MODEL_LOADING_FAIL.value,
                                               user_msg=msg)

    @classmethod
    def raise_from(cls):
        """Define exception when model loading fail."""
        return ValueError, cls
