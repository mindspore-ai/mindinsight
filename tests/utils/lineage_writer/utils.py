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
import os
from functools import wraps

from marshmallow import ValidationError

from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError, LineageParamValueError
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING
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


def validate_int_params(int_param, param_name):
    """
    Verify the parameter which type is integer valid or not.

    Args:
        int_param (int): parameter that is integer,
            including epoch, dataset_batch_size, step_num
        param_name (str): the name of parameter,
            including epoch, dataset_batch_size, step_num

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    if not isinstance(int_param, int) or int_param <= 0 or int_param > pow(2, 63) - 1:
        if param_name == 'step_num':
            log.error('Invalid step_num. The step number should be a positive integer.')
            raise MindInsightException(error=LineageErrors.PARAM_STEP_NUM_ERROR,
                                       message=LineageErrorMsg.PARAM_STEP_NUM_ERROR.value)

        if param_name == 'dataset_batch_size':
            log.error('Invalid dataset_batch_size. '
                      'The batch size should be a positive integer.')
            raise MindInsightException(error=LineageErrors.PARAM_BATCH_SIZE_ERROR,
                                       message=LineageErrorMsg.PARAM_BATCH_SIZE_ERROR.value)


def validate_file_path(file_path, allow_empty=False):
    """
    Verify that the file_path is valid.

    Args:
        file_path (str): Input file path.
        allow_empty (bool): Whether file_path can be empty.

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    try:
        if allow_empty and not file_path:
            return file_path
        return safe_normalize_path(file_path, raise_key='dataset_path', safe_prefixes=None)
    except ValidationError as error:
        log.error(str(error))
        raise MindInsightException(error=LineageErrors.PARAM_FILE_PATH_ERROR,
                                   message=str(error))


EVAL_RUN_CONTEXT_ERROR_MSG_MAPPING = {
    'metrics': LineageErrorMsg.PARAM_EVAL_METRICS_ERROR.value,
}
EVAL_RUN_CONTEXT_ERROR_MAPPING = {
    'valid_dataset': LineageErrors.PARAM_DATASET_ERROR,
    'metrics': LineageErrors.PARAM_EVAL_METRICS_ERROR
}


def validate_raise_exception(raise_exception):
    """
    Validate raise_exception.

    Args:
        raise_exception (bool): decide raise exception or not,
            if True, raise exception; else, catch exception and continue.

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    if not isinstance(raise_exception, bool):
        log.error("Invalid raise_exception. It should be True or False.")
        raise MindInsightException(
            error=LineageErrors.PARAM_RAISE_EXCEPTION_ERROR,
            message=LineageErrorMsg.PARAM_RAISE_EXCEPTION_ERROR.value
        )


def validate_user_defined_info(user_defined_info):
    """
    Validate user defined info， delete the item if its key is in lineage.

    Args:
        user_defined_info (dict): The user defined info.

    Raises:
        LineageParamTypeError: If the type of parameters is invalid.
        LineageParamValueError: If user defined keys have been defined in lineage.

    """
    if not isinstance(user_defined_info, dict):
        log.error("Invalid user defined info. It should be a dict.")
        raise LineageParamTypeError("Invalid user defined info. It should be dict.")
    for key, value in user_defined_info.items():
        if not isinstance(key, str):
            error_msg = "Dict key type {} is not supported in user defined info." \
                        "Only str is permitted now.".format(type(key))
            log.error(error_msg)
            raise LineageParamTypeError(error_msg)
        if not isinstance(value, (int, str, float)):
            error_msg = "Dict value type {} is not supported in user defined info." \
                        "Only str, int and float are permitted now.".format(type(value))
            log.error(error_msg)
            raise LineageParamTypeError(error_msg)

    field_map = set(FIELD_MAPPING.keys())
    user_defined_keys = set(user_defined_info.keys())
    insertion = list(field_map & user_defined_keys)

    if insertion:
        for key in insertion:
            user_defined_info.pop(key)
        raise LineageParamValueError("There are some keys have defined in lineage. "
                                     "Duplicated key(s): %s. " % insertion)


def make_directory(path):
    """Make directory."""
    if path is None or not isinstance(path, str) or not path.strip():
        log.error("Invalid input path: %r.", path)
        raise LineageParamTypeError("Invalid path type")

    # convert relative path to abs path
    path = os.path.realpath(path)
    log.debug("The abs path is %r", path)

    # check path exist and its write permissions]
    if os.path.exists(path):
        real_path = path
    else:
        # All exceptions need to be caught because create directory maybe have some limit(permissions)
        log.debug("The directory(%s) doesn't exist, will create it", path)
        try:
            os.makedirs(path, exist_ok=True)
            real_path = path
        except PermissionError as err:
            log.error("No write permission on the directory(%r), error = %r", path, err)
            raise LineageParamTypeError("No write permission on the directory.")
    return real_path
