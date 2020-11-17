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
import sys
from enum import unique

from lib2to3.pgen2 import parse
from treelib.exceptions import DuplicatedNodeIdError, MultipleRootError, NodeIDAbsentError

from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console

from mindinsight.utils.constant import ScriptConverterErrors
from mindinsight.utils.exceptions import MindInsightException, ParamMissError


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

    BASE_CONVERTER_FAIL = 000
    GRAPH_INIT_FAIL = 100
    TREE_CREATE_FAIL = 200
    SOURCE_FILES_SAVE_FAIL = 300


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

    @staticmethod
    def raise_from():
        """Raise from below exceptions."""
        return None

    @classmethod
    def check_except_with_print_pytorch(cls, msg):
        """Check except in pytorch."""

        def decorator(func):
            def _f(graph_path, sample_shape, output_folder, report_folder):
                try:
                    func(graph_path=graph_path, sample_shape=sample_shape,
                         output_folder=output_folder, report_folder=report_folder)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    detail_info = f"Error detail: {str(e)}"
                    log_console.error(str(error))
                    log_console.error(detail_info)
                    log.exception(e)
                    sys.exit(-1)
            return _f
        return decorator

    @classmethod
    def check_except_with_print_tf(cls, msg):
        """Check except in tf."""

        def decorator(func):
            def _f(graph_path, sample_shape,
                   input_nodes, output_nodes,
                   output_folder, report_folder):
                try:
                    func(graph_path=graph_path, sample_shape=sample_shape,
                         input_nodes=input_nodes, output_nodes=output_nodes,
                         output_folder=output_folder, report_folder=report_folder)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    detail_info = f"Error detail: {str(e)}"
                    log_console.error(str(error))
                    log_console.error(detail_info)
                    log.exception(e)
                    sys.exit(-1)

            return _f

        return decorator


class BaseConverterFail(MindConverterException):
    """Base converter failed."""
    def __init__(self, msg):
        super(BaseConverterFail, self).__init__(error=ConverterErrors.BASE_CONVERTER_FAIL,
                                                user_msg=msg)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (UnknownModel,
                         ParamMissError)
        return except_source

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(file_config):
                try:
                    func(file_config=file_config)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    detail_info = f"Error detail: {str(e)}"
                    log_console.error(str(error))
                    log_console.error(detail_info)
                    log.exception(e)
                    sys.exit(-1)
            return _f
        return decorator


class UnknownModel(MindConverterException):
    """The unknown model error."""
    def __init__(self, msg):
        super(UnknownModel, self).__init__(error=ConverterErrors.UNKNOWN_MODEL,
                                           user_msg=msg)


class GraphInitFail(MindConverterException):
    """The graph init fail error."""
    def __init__(self, **kwargs):
        super(GraphInitFail, self).__init__(error=ConverterErrors.GRAPH_INIT_FAIL,
                                            user_msg=kwargs.get('msg', ''))

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (FileNotFoundError,
                         ModuleNotFoundError,
                         ModelNotSupport,
                         TypeError,
                         ZeroDivisionError)
        return except_source

    @classmethod
    def check_except_pytorch(cls, msg):
        """Check except for pytorch."""
        return super().check_except_with_print_pytorch(msg)

    @classmethod
    def check_except_tf(cls, msg):
        """Check except for tf."""
        return super().check_except_with_print_tf(msg)


class TreeCreateFail(MindConverterException):
    """The tree create fail."""
    def __init__(self, msg):
        super(TreeCreateFail, self).__init__(error=ConverterErrors.TREE_CREATE_FAIL,
                                             user_msg=msg)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (NodeInputMissing,
                         TreeNodeInsertFail)
        return except_source

    @classmethod
    def check_except_pytorch(cls, msg):
        """Check except."""
        return super().check_except_with_print_pytorch(msg)

    @classmethod
    def check_except_tf(cls, msg):
        """Check except for tf."""
        return super().check_except_with_print_tf(msg)


class SourceFilesSaveFail(MindConverterException):
    """The source files save fail error."""
    def __init__(self, msg):
        super(SourceFilesSaveFail, self).__init__(error=ConverterErrors.SOURCE_FILES_SAVE_FAIL,
                                                  user_msg=msg)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (NodeInputTypeNotSupport,
                         ScriptGenerateFail,
                         ReportGenerateFail,
                         IOError)
        return except_source

    @classmethod
    def check_except_pytorch(cls, msg):
        """Check except."""
        return super().check_except_with_print_pytorch(msg)

    @classmethod
    def check_except_tf(cls, msg):
        """Check except for tf."""
        return super().check_except_with_print_tf(msg)


class ModelNotSupport(MindConverterException):
    """The model not support error."""
    def __init__(self, msg):
        super(ModelNotSupport, self).__init__(error=ConverterErrors.MODEL_NOT_SUPPORT,
                                              user_msg=msg,
                                              cls_code=ConverterErrors.GRAPH_INIT_FAIL.value)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (RuntimeError,
                         ValueError,
                         TypeError,
                         OSError,
                         ZeroDivisionError)
        return except_source

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(arch, model_path, **kwargs):
                try:
                    output = func(arch, model_path=model_path, **kwargs)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    log.error(msg)
                    log.exception(e)
                    raise error from e
                return output
            return _f
        return decorator


class NodeInputMissing(MindConverterException):
    """The node input missing error."""
    def __init__(self, msg):
        super(NodeInputMissing, self).__init__(error=ConverterErrors.NODE_INPUT_MISSING,
                                               user_msg=msg,
                                               cls_code=ConverterErrors.TREE_CREATE_FAIL.value)


class TreeNodeInsertFail(MindConverterException):
    """The tree node create fail error."""
    def __init__(self, msg):
        super(TreeNodeInsertFail, self).__init__(error=ConverterErrors.TREE_NODE_INSERT_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.TREE_CREATE_FAIL.value)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (OSError,
                         DuplicatedNodeIdError,
                         MultipleRootError,
                         NodeIDAbsentError)
        return except_source

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(arch, graph):
                try:
                    output = func(arch, graph=graph)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    log.error(msg)
                    log.exception(e)
                    raise error from e
                return output
            return _f
        return decorator


class NodeInputTypeNotSupport(MindConverterException):
    """The node input type NOT support error."""
    def __init__(self, msg):
        super(NodeInputTypeNotSupport, self).__init__(error=ConverterErrors.NODE_INPUT_TYPE_NOT_SUPPORT,
                                                      user_msg=msg,
                                                      cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)


class ScriptGenerateFail(MindConverterException):
    """The script generate fail error."""
    def __init__(self, msg):
        super(ScriptGenerateFail, self).__init__(error=ConverterErrors.SCRIPT_GENERATE_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = (RuntimeError,
                         parse.ParseError,
                         AttributeError)
        return except_source

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(arch, mapper):
                try:
                    output = func(arch, mapper=mapper)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    log.error(msg)
                    log.exception(e)
                    raise error from e
                return output
            return _f
        return decorator


class ReportGenerateFail(MindConverterException):
    """The report generate fail error."""
    def __init__(self, msg):
        super(ReportGenerateFail, self).__init__(error=ConverterErrors.REPORT_GENERATE_FAIL,
                                                 user_msg=msg,
                                                 cls_code=ConverterErrors.SOURCE_FILES_SAVE_FAIL.value)

    @staticmethod
    def raise_from():
        """Raise from exceptions below."""
        except_source = ZeroDivisionError
        return except_source

    @classmethod
    def check_except(cls, msg):
        """Check except."""

        def decorator(func):
            def _f(arch, mapper):
                try:
                    output = func(arch, mapper=mapper)
                except cls.raise_from() as e:
                    error = cls(msg=msg)
                    log.error(msg)
                    log.exception(e)
                    raise error from e
                return output
            return _f
        return decorator
