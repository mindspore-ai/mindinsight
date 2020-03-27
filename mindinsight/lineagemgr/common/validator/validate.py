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
"""Validate the parameters."""
import os

from marshmallow import ValidationError

from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamMissingError, \
    LineageParamTypeError, LineageParamValueError, LineageDirNotExistError
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING
from mindinsight.utils.exceptions import MindInsightException

try:
    from mindspore.nn import Cell
    from mindspore.train.summary import SummaryRecord
except (ImportError, ModuleNotFoundError):
    log.warning('MindSpore Not Found!')

TRAIN_RUN_CONTEXT_ERROR_MAPPING = {
    'optimizer': LineageErrors.PARAM_OPTIMIZER_ERROR,
    'loss_fn': LineageErrors.PARAM_LOSS_FN_ERROR,
    'net_outputs': LineageErrors.PARAM_NET_OUTPUTS_ERROR,
    'train_network': LineageErrors.PARAM_TRAIN_NETWORK_ERROR,
    'train_dataset': LineageErrors.PARAM_DATASET_ERROR,
    'epoch_num': LineageErrors.PARAM_EPOCH_NUM_ERROR,
    'batch_num': LineageErrors.PARAM_BATCH_NUM_ERROR,
    'parallel_mode': LineageErrors.PARAM_TRAIN_PARALLEL_ERROR,
    'device_number': LineageErrors.PARAM_DEVICE_NUMBER_ERROR,
    'list_callback': LineageErrors.PARAM_CALLBACK_LIST_ERROR,
    'train_dataset_size': LineageErrors.PARAM_DATASET_SIZE_ERROR,
}

SEARCH_MODEL_ERROR_MAPPING = {
    'summary_dir': LineageErrors.LINEAGE_PARAM_SUMMARY_DIR_ERROR,
    'loss_function': LineageErrors.LINEAGE_PARAM_LOSS_FUNCTION_ERROR,
    'train_dataset_path': LineageErrors.LINEAGE_PARAM_TRAIN_DATASET_PATH_ERROR,
    'train_dataset_count': LineageErrors.LINEAGE_PARAM_TRAIN_DATASET_COUNT_ERROR,
    'test_dataset_path': LineageErrors.LINEAGE_PARAM_TEST_DATASET_PATH_ERROR,
    'test_dataset_count': LineageErrors.LINEAGE_PARAM_TEST_DATASET_COUNT_ERROR,
    'network': LineageErrors.LINEAGE_PARAM_NETWORK_ERROR,
    'optimizer': LineageErrors.LINEAGE_PARAM_OPTIMIZER_ERROR,
    'learning_rate': LineageErrors.LINEAGE_PARAM_LEARNING_RATE_ERROR,
    'epoch': LineageErrors.LINEAGE_PARAM_EPOCH_ERROR,
    'batch_size': LineageErrors.LINEAGE_PARAM_BATCH_SIZE_ERROR,
    'limit': LineageErrors.PARAM_VALUE_ERROR,
    'offset': LineageErrors.PARAM_VALUE_ERROR,
    'loss': LineageErrors.LINEAGE_PARAM_LOSS_ERROR,
    'model_size': LineageErrors.LINEAGE_PARAM_MODEL_SIZE_ERROR,
    'sorted_name': LineageErrors.LINEAGE_PARAM_SORTED_NAME_ERROR,
    'sorted_type': LineageErrors.LINEAGE_PARAM_SORTED_TYPE_ERROR,
    'lineage_type': LineageErrors.LINEAGE_PARAM_LINEAGE_TYPE_ERROR
}


TRAIN_RUN_CONTEXT_ERROR_MSG_MAPPING = {
    'optimizer': LineageErrorMsg.PARAM_OPTIMIZER_ERROR.value,
    'loss_fn': LineageErrorMsg.PARAM_LOSS_FN_ERROR.value,
    'net_outputs': LineageErrorMsg.PARAM_NET_OUTPUTS_ERROR.value,
    'train_network': LineageErrorMsg.PARAM_TRAIN_NETWORK_ERROR.value,
    'epoch_num': LineageErrorMsg.PARAM_EPOCH_NUM_ERROR.value,
    'batch_num': LineageErrorMsg.PARAM_BATCH_NUM_ERROR.value,
    'parallel_mode': LineageErrorMsg.PARAM_TRAIN_PARALLEL_ERROR.value,
    'device_number': LineageErrorMsg.PARAM_DEVICE_NUMBER_ERROR.value,
    'list_callback': LineageErrorMsg.PARAM_CALLBACK_LIST_ERROR.value
}

SEARCH_MODEL_ERROR_MSG_MAPPING = {
    'summary_dir': LineageErrorMsg.LINEAGE_PARAM_SUMMARY_DIR_ERROR.value,
    'loss_function': LineageErrorMsg.LINEAGE_LOSS_FUNCTION_ERROR.value,
    'train_dataset_path': LineageErrorMsg.LINEAGE_TRAIN_DATASET_PATH_ERROR.value,
    'train_dataset_count': LineageErrorMsg.LINEAGE_TRAIN_DATASET_COUNT_ERROR.value,
    'test_dataset_path': LineageErrorMsg.LINEAGE_TEST_DATASET_PATH_ERROR.value,
    'test_dataset_count': LineageErrorMsg.LINEAGE_TEST_DATASET_COUNT_ERROR.value,
    'network': LineageErrorMsg.LINEAGE_NETWORK_ERROR.value,
    'optimizer': LineageErrorMsg.LINEAGE_OPTIMIZER_ERROR.value,
    'learning_rate': LineageErrorMsg.LINEAGE_LEARNING_RATE_ERROR.value,
    'epoch': LineageErrorMsg.PARAM_EPOCH_NUM_ERROR.value,
    'batch_size': LineageErrorMsg.PARAM_BATCH_SIZE_ERROR.value,
    'limit': LineageErrorMsg.PARAM_LIMIT_ERROR.value,
    'offset': LineageErrorMsg.PARAM_OFFSET_ERROR.value,
    'loss': LineageErrorMsg.LINEAGE_LOSS_ERROR.value,
    'model_size': LineageErrorMsg.LINEAGE_MODEL_SIZE_ERROR.value,
    'sorted_name': LineageErrorMsg.LINEAGE_PARAM_SORTED_NAME_ERROR.value,
    'sorted_type': LineageErrorMsg.LINEAGE_PARAM_SORTED_TYPE_ERROR.value,
    'lineage_type': LineageErrorMsg.LINEAGE_PARAM_LINEAGE_TYPE_ERROR.value
}


EVAL_RUN_CONTEXT_ERROR_MAPPING = {
    'valid_dataset': LineageErrors.PARAM_DATASET_ERROR,
    'metrics': LineageErrors.PARAM_EVAL_METRICS_ERROR
}

EVAL_RUN_CONTEXT_ERROR_MSG_MAPPING = {
    'metrics': LineageErrorMsg.PARAM_EVAL_METRICS_ERROR.value,
}


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


def validate_network(network):
    """
    Verify if the network is valid.

    Args:
        network (Cell): See mindspore.nn.Cell.

    Raises:
        LineageParamMissingError: If the network is None.
        MindInsightException: If the network is invalid.
    """
    if not network:
        error_msg = "The input network for TrainLineage should not be None."
        log.error(error_msg)
        raise LineageParamMissingError(error_msg)

    if not isinstance(network, Cell):
        log.error("Invalid network. Network should be an instance"
                  "of mindspore.nn.Cell.")
        raise MindInsightException(
            error=LineageErrors.PARAM_TRAIN_NETWORK_ERROR,
            message=LineageErrorMsg.PARAM_TRAIN_NETWORK_ERROR.value
        )


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
            return
        safe_normalize_path(file_path, raise_key='dataset_path', safe_prefixes=None)
    except ValidationError as error:
        log.error(str(error))
        raise MindInsightException(error=LineageErrors.PARAM_FILE_PATH_ERROR,
                                   message=str(error))


def validate_train_run_context(schema, data):
    """
    Validate mindspore train run_context data according to schema.

    Args:
        schema (Schema): data schema.
        data (dict): data to check schema.

    Raises:
        MindInsightException: If the parameters are invalid.
    """

    errors = schema().validate(data)
    for error_key, error_msg in errors.items():
        if error_key in TRAIN_RUN_CONTEXT_ERROR_MAPPING.keys():
            error_code = TRAIN_RUN_CONTEXT_ERROR_MAPPING.get(error_key)
            if TRAIN_RUN_CONTEXT_ERROR_MSG_MAPPING.get(error_key):
                error_msg = TRAIN_RUN_CONTEXT_ERROR_MSG_MAPPING.get(error_key)
            log.error(error_msg)
            raise MindInsightException(error=error_code, message=error_msg)


def validate_eval_run_context(schema, data):
    """
    Validate mindspore evaluation job run_context data according to schema.

    Args:
        schema (Schema): data schema.
        data (dict): data to check schema.

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    errors = schema().validate(data)
    for error_key, error_msg in errors.items():
        if error_key in EVAL_RUN_CONTEXT_ERROR_MAPPING.keys():
            error_code = EVAL_RUN_CONTEXT_ERROR_MAPPING.get(error_key)
            if EVAL_RUN_CONTEXT_ERROR_MSG_MAPPING.get(error_key):
                error_msg = EVAL_RUN_CONTEXT_ERROR_MSG_MAPPING.get(error_key)
            log.error(error_msg)
            raise MindInsightException(error=error_code, message=error_msg)


def validate_search_model_condition(schema, data):
    """
    Validate search model condition.

    Args:
        schema (Schema): Data schema.
        data (dict): Data to check schema.

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    error = schema().validate(data)
    for error_key in error.keys():
        if error_key in SEARCH_MODEL_ERROR_MAPPING.keys():
            error_code = SEARCH_MODEL_ERROR_MAPPING.get(error_key)
            error_msg = SEARCH_MODEL_ERROR_MSG_MAPPING.get(error_key)
            log.error(error_msg)
            raise MindInsightException(error=error_code, message=error_msg)


def validate_summary_record(summary_record):
    """
    Validate summary_record.

    Args:
        summary_record (SummaryRecord): SummaryRecord is used to record
            the summary value, and summary_record is an instance of SummaryRecord,
            see mindspore.train.summary.SummaryRecord

    Raises:
        MindInsightException: If the parameters are invalid.
    """
    if not isinstance(summary_record, SummaryRecord):
        log.error("Invalid summary_record. It should be an instance "
                  "of mindspore.train.summary.SummaryRecord.")
        raise MindInsightException(
            error=LineageErrors.PARAM_SUMMARY_RECORD_ERROR,
            message=LineageErrorMsg.PARAM_SUMMARY_RECORD_ERROR.value
        )


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


def validate_filter_key(keys):
    """
    Verify the keys of filtering is valid or not.

    Args:
        keys (list): The keys to get the relative lineage info.

    Raises:
        LineageParamTypeError: If keys is not list.
        LineageParamValueError: If the value of keys is invalid.
    """
    filter_keys = [
        'metric', 'hyper_parameters', 'algorithm',
        'train_dataset', 'model', 'valid_dataset',
        'dataset_graph'
    ]

    if not isinstance(keys, list):
        log.error("Keys must be list.")
        raise LineageParamTypeError("Keys must be list.")

    for element in keys:
        if not isinstance(element, str):
            log.error("Element of keys must be str.")
            raise LineageParamTypeError("Element of keys must be str.")

    if not set(keys).issubset(filter_keys):
        err_msg = "Keys must be in {}.".format(filter_keys)
        log.error(err_msg)
        raise LineageParamValueError(err_msg)


def validate_condition(search_condition):
    """
    Verify the param in search_condition is valid or not.

    Args:
        search_condition (dict): The search condition.

    Raises:
        LineageParamTypeError: If the type of the param in search_condition is invalid.
        LineageParamValueError: If the value of the param in search_condition is invalid.
    """
    if not isinstance(search_condition, dict):
        log.error("Invalid search_condition type, it should be dict.")
        raise LineageParamTypeError("Invalid search_condition type, "
                                    "it should be dict.")

    if "limit" in search_condition:
        if isinstance(search_condition.get("limit"), bool) \
                or not isinstance(search_condition.get("limit"), int):
            log.error("The limit must be int.")
            raise LineageParamTypeError("The limit must be int.")

    if "offset" in search_condition:
        if isinstance(search_condition.get("offset"), bool) \
                or not isinstance(search_condition.get("offset"), int):
            log.error("The offset must be int.")
            raise LineageParamTypeError("The offset must be int.")

    if "sorted_name" in search_condition:
        sorted_name = search_condition.get("sorted_name")
        err_msg = "The sorted_name must be in {} or start with " \
                  "`metric_`.".format(list(FIELD_MAPPING.keys()))
        if not isinstance(sorted_name, str):
            log.error(err_msg)
            raise LineageParamValueError(err_msg)
        if sorted_name not in FIELD_MAPPING and not (
                sorted_name.startswith('metric_') and len(sorted_name) > 7):
            log.error(err_msg)
            raise LineageParamValueError(err_msg)

    sorted_type_param = ['ascending', 'descending', None]
    if "sorted_type" in search_condition:
        if "sorted_name" not in search_condition:
            log.error("The sorted_name have to exist when sorted_type exists.")
            raise LineageParamValueError("The sorted_name have to exist when sorted_type exists.")

        if search_condition.get("sorted_type") not in sorted_type_param:
            err_msg = "The sorted_type must be ascending or descending."
            log.error(err_msg)
            raise LineageParamValueError(err_msg)


def validate_path(summary_path):
    """
    Verify the summary path is valid or not.

    Args:
        summary_path (str): The summary path which is a dir.

    Raises:
        LineageParamValueError: If the input param value is invalid.
        LineageDirNotExistError: If the summary path is invalid.
    """
    try:
        summary_path = safe_normalize_path(
            summary_path, "summary_path", None, check_absolute_path=True
        )
    except ValidationError:
        log.error("The summary path is invalid.")
        raise LineageParamValueError("The summary path is invalid.")
    if not os.path.isdir(summary_path):
        log.error("The summary path does not exist or is not a dir.")
        raise LineageDirNotExistError("The summary path does not exist or is not a dir.")

    return summary_path
