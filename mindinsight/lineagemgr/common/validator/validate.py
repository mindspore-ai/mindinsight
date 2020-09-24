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
from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError, LineageParamValueError
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.querier.query_model import FIELD_MAPPING
from mindinsight.utils.exceptions import MindInsightException, ParamValueError

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
    'device_num': LineageErrors.LINEAGE_PARAM_DEVICE_NUM_ERROR,
    'limit': LineageErrors.PARAM_VALUE_ERROR,
    'offset': LineageErrors.PARAM_VALUE_ERROR,
    'loss': LineageErrors.LINEAGE_PARAM_LOSS_ERROR,
    'model_size': LineageErrors.LINEAGE_PARAM_MODEL_SIZE_ERROR,
    'sorted_name': LineageErrors.LINEAGE_PARAM_SORTED_NAME_ERROR,
    'sorted_type': LineageErrors.LINEAGE_PARAM_SORTED_TYPE_ERROR,
    'dataset_mark': LineageErrors.LINEAGE_PARAM_DATASET_MARK_ERROR,
    'lineage_type': LineageErrors.LINEAGE_PARAM_LINEAGE_TYPE_ERROR
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
    'device_num': LineageErrorMsg.PARAM_DEVICE_NUM_ERROR.value,
    'limit': LineageErrorMsg.PARAM_LIMIT_ERROR.value,
    'offset': LineageErrorMsg.PARAM_OFFSET_ERROR.value,
    'loss': LineageErrorMsg.LINEAGE_LOSS_ERROR.value,
    'model_size': LineageErrorMsg.LINEAGE_MODEL_SIZE_ERROR.value,
    'sorted_name': LineageErrorMsg.LINEAGE_PARAM_SORTED_NAME_ERROR.value,
    'sorted_type': LineageErrorMsg.LINEAGE_PARAM_SORTED_TYPE_ERROR.value,
    'dataset_mark': LineageErrorMsg.LINEAGE_PARAM_DATASET_MARK_ERROR.value,
    'lineage_type': LineageErrorMsg.LINEAGE_PARAM_LINEAGE_TYPE_ERROR.value
}


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
    for (error_key, error_msgs) in error.items():
        if error_key in SEARCH_MODEL_ERROR_MAPPING.keys():
            error_code = SEARCH_MODEL_ERROR_MAPPING.get(error_key)
            error_msg = SEARCH_MODEL_ERROR_MSG_MAPPING.get(error_key)
            for err_msg in error_msgs:
                if 'operation' in err_msg.lower():
                    error_msg = f'The parameter {error_key} is invalid. {err_msg}'
                    break
            log.error(error_msg)
            raise MindInsightException(error=error_code, message=error_msg)


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
                  "`metric/` or `user_defined/`.".format(list(FIELD_MAPPING.keys()))
        if not isinstance(sorted_name, str):
            log.error(err_msg)
            raise LineageParamValueError(err_msg)
        if not (sorted_name in FIELD_MAPPING
                or (sorted_name.startswith('metric/') and len(sorted_name) > len('metric/'))
                or (sorted_name.startswith('user_defined/') and len(sorted_name) > len('user_defined/'))
                or sorted_name in ['tag']):
            log.error(err_msg)
            raise LineageParamValueError(err_msg)

    sorted_type_param = ['ascending', 'descending', None]
    if "sorted_type" in search_condition:
        if "sorted_name" not in search_condition:
            log.error("The sorted_name must exist when sorted_type exists.")
            raise LineageParamValueError("The sorted_name must exist when sorted_type exists.")

        if search_condition.get("sorted_type") not in sorted_type_param:
            err_msg = "The sorted_type must be ascending or descending."
            log.error(err_msg)
            raise LineageParamValueError(err_msg)


def validate_train_id(relative_path):
    """
    Check if train_id is valid.

    Args:
        relative_path (str): Train ID of a summary directory, e.g. './log1'.

    Returns:
        bool, if train id is valid, return True.

    """
    if not relative_path.startswith('./'):
        log.warning("The relative_path does not start with './'.")
        raise ParamValueError(
            "Summary dir should be relative path starting with './'."
        )
    if len(relative_path.split("/")) > 2:
        log.warning("The relative_path contains multiple '/'.")
        raise ParamValueError(
            "Summary dir should be relative path starting with './'."
        )


def validate_range(name, value, min_value, max_value):
    """
    Check if value is in [min_value, max_value].

    Args:
        name (str): Value name.
        value (Union[int, float]): Value to be check.
        min_value (Union[int, float]): Min value.
        max_value (Union[int, float]): Max value.

    Raises:
        LineageParamValueError, if value type is invalid or value is out of [min_value, max_value].

    """
    if not isinstance(value, (int, float)):
        raise LineageParamValueError("Value should be int or float.")

    if value < min_value or value > max_value:
        raise LineageParamValueError("The %s should in [%d, %d]." % (name, min_value, max_value))


def validate_added_info(added_info: dict):
    """
    Check if added_info is valid.

    Args:
        added_info (dict): The added info.

    Raises:
        bool, if added_info is valid, return True.

    """
    added_info_keys = ["tag", "remark"]
    if not set(added_info.keys()).issubset(added_info_keys):
        err_msg = "Keys of added_info must be in {}.".format(added_info_keys)
        raise LineageParamValueError(err_msg)

    for key, value in added_info.items():
        if key == "tag":
            if not isinstance(value, int):
                raise LineageParamValueError("'tag' must be int.")
            # tag should be in [0, 10].
            validate_range("tag", value, min_value=0, max_value=10)
        elif key == "remark":
            if not isinstance(value, str):
                raise LineageParamValueError("'remark' must be str.")
            # length of remark should be in [0, 128].
            validate_range("length of remark", len(value), min_value=0, max_value=128)
