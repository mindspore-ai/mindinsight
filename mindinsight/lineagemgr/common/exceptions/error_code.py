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
"""Lineage error code and messages."""
from enum import Enum, unique
from mindinsight.utils.constant import LineageMgrErrors as LineageErrorCodes


_PARAM_ERROR_MASK = 0b00001 << 7
_MINDSPORE_COLLECTOR_ERROR = 0b00011 << 7
_MODEL_LINEAGE_API_ERROR_MASK = 0b00100 << 7
_DATASET_COLLECTOR_ERROR_MASK = 0b00101 << 7
_DATASET_LINEAGE_ERROR_MASK = 0b00110 << 7
_SUMMARY_ANALYZE_ERROR_MASK = 0b00111 << 7
_QUERIER_ERROR_MASK = 0b01000 << 7


@unique
class LineageErrors(LineageErrorCodes):
    """Lineage error codes."""
    PARAM_TYPE_ERROR = 0 | _PARAM_ERROR_MASK
    PARAM_VALUE_ERROR = 1 | _PARAM_ERROR_MASK
    PARAM_MISSING_ERROR = 2 | _PARAM_ERROR_MASK
    PARAM_SUMMARY_RECORD_ERROR = 3 | _PARAM_ERROR_MASK
    PARAM_RAISE_EXCEPTION_ERROR = 4 | _PARAM_ERROR_MASK

    # MindSpore Collector error codes.
    PARAM_RUN_CONTEXT_ERROR = 0 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_OPTIMIZER_ERROR = 1 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_LOSS_FN_ERROR = 2 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_TRAIN_NETWORK_ERROR = 3 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_DATASET_ERROR = 4 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_EPOCH_NUM_ERROR = 5 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_BATCH_NUM_ERROR = 6 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_TRAIN_PARALLEL_ERROR = 7 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_DEVICE_NUMBER_ERROR = 8 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_FILE_PATH_ERROR = 9 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_DATASET_SIZE_ERROR = 10 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_LEARNING_RATE_ERROR = 11 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_EVAL_METRICS_ERROR = 12 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_BATCH_SIZE_ERROR = 13 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_NET_OUTPUTS_ERROR = 14 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_CALLBACK_LIST_ERROR = 15 | _MINDSPORE_COLLECTOR_ERROR
    LINEAGE_GET_MODEL_FILE_ERROR = 16 | _MINDSPORE_COLLECTOR_ERROR
    LOG_LINEAGE_INFO_ERROR = 17 | _MINDSPORE_COLLECTOR_ERROR
    PARAM_STEP_NUM_ERROR = 18 | _MINDSPORE_COLLECTOR_ERROR

    # Model lineage error codes.
    LINEAGE_PARAM_METRIC_ERROR = 1 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_LOSS_FUNCTION_ERROR = 4 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_TRAIN_DATASET_PATH_ERROR = 5 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_TRAIN_DATASET_COUNT_ERROR = 6 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_TEST_DATASET_PATH_ERROR = 7 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_TEST_DATASET_COUNT_ERROR = 8 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_NETWORK_ERROR = 9 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_OPTIMIZER_ERROR = 10 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_LEARNING_RATE_ERROR = 11 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_EPOCH_ERROR = 12 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_BATCH_SIZE_ERROR = 13 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_NOT_SUPPORT_ERROR = 14 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_LOSS_ERROR = 15 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_MODEL_SIZE_ERROR = 16 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_SUMMARY_DIR_ERROR = 17 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_SORTED_NAME_ERROR = 18 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_SORTED_TYPE_ERROR = 19 | _MODEL_LINEAGE_API_ERROR_MASK

    LINEAGE_DIR_NOT_EXIST_ERROR = 20 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_SUMMARY_DATA_ERROR = 21 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_FILE_NOT_FOUND_ERROR = 22 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_SEARCH_CONDITION_PARAM_ERROR = 24 | _MODEL_LINEAGE_API_ERROR_MASK

    LINEAGE_PARAM_LINEAGE_TYPE_ERROR = 25 | _MODEL_LINEAGE_API_ERROR_MASK
    LINEAGE_PARAM_DEVICE_NUM_ERROR = 26 | _MODEL_LINEAGE_API_ERROR_MASK

    # Dataset lineage error codes.
    LINEAGE_PARAM_DATASET_MARK_ERROR = 0 | _DATASET_LINEAGE_ERROR_MASK

    SUMMARY_ANALYZE_ERROR = 0 | _SUMMARY_ANALYZE_ERROR_MASK
    SUMMARY_VERIFICATION_ERROR = 1 | _SUMMARY_ANALYZE_ERROR_MASK

    # Querier error codes.
    EVENT_NOT_EXIST_ERROR = 0 | _QUERIER_ERROR_MASK
    QUERIER_PARAM_ERROR = 1 | _QUERIER_ERROR_MASK
    SUMMARY_PARSE_FAIL_ERROR = 2 | _QUERIER_ERROR_MASK
    EVENT_FIELD_NOT_EXIST_ERROR = 4 | _QUERIER_ERROR_MASK


@unique
class LineageErrorMsg(Enum):
    """Lineage error messages."""
    PARAM_TYPE_ERROR = "TypeError. {}"
    PARAM_VALUE_ERROR = "ValueError. {}"
    PARAM_MISSING_ERROR = "MissingError. {}"
    PARAM_LIMIT_ERROR = "Invalid input limit. 0 < limit <= 100"
    PARAM_OFFSET_ERROR = "Invalid input offset. 0 <= offset <= 100000"
    PARAM_SUMMARY_RECORD_ERROR = "Invalid value for summary_record. It should be an instance of " \
                                 "mindspore.train.summary.SummaryRecord"
    PARAM_RAISE_EXCEPTION_ERROR = "Invalid value for raise_exception. It should be True or False."
    # Lineage error messages.
    LINEAGE_SUMMARY_DATA_ERROR = "Query summary data error: {}"
    LINEAGE_FILE_NOT_FOUND_ERROR = "File not found error: {}"
    LINEAGE_DIR_NOT_EXIST_ERROR = "Dir not exist error: {}"
    LINEAGE_SEARCH_CONDITION_PARAM_ERROR = "Search_condition param error: {}"

    # MindSpore Collector error messages.
    PARAM_RUN_CONTEXT_ERROR = "The parameter run_context is invalid. It should be an instance of " \
                              "mindspore.train.callback.RunContext. {}"

    PARAM_OPTIMIZER_ERROR = "The parameter optimizer is invalid. It should be an instance of " \
                            "mindspore.nn.optim.optimizer.Optimizer."

    PARAM_LOSS_FN_ERROR = "The parameter loss_fn is invalid. It should be a Function."

    PARAM_NET_OUTPUTS_ERROR = "The parameter net_outputs is invalid. It should be a Tensor."

    PARAM_TRAIN_NETWORK_ERROR = "The parameter train_network is invalid. It should be an instance of " \
                                "mindspore.nn.cell.Cell."

    PARAM_EPOCH_NUM_ERROR = "The parameter epoch is invalid. It should be a positive integer."

    PARAM_STEP_NUM_ERROR = "The parameter step_num is invalid. It should be a positive integer."

    PARAM_BATCH_NUM_ERROR = "The parameter batch_num is invalid. It should be a non-negative integer."

    PARAM_TRAIN_PARALLEL_ERROR = "The parameter parallel_mode is invalid. It should be an integer" \
                                 "between 0 and 4."

    PARAM_DEVICE_NUMBER_ERROR = "The parameter device_number is invalid. It should be a positive integer."

    PARAM_LEARNING_RATE_ERROR = "The parameter learning_rate is invalid. It should be a float number or " \
                                "an instance of mindspore.common.tensor.Tensor."

    PARAM_EVAL_METRICS_ERROR = "The parameter metrics is invalid. It should be a dictionary."

    PARAM_BATCH_SIZE_ERROR = "The parameter batch_size is invalid. It should be a non-negative integer."

    PARAM_DEVICE_NUM_ERROR = "The parameter device_num is invalid. It should be a non-negative integer."

    PARAM_CALLBACK_LIST_ERROR = "The parameter list_callback is invalid. It should be an instance of " \
                                "mindspore.train.callback._ListCallback."

    LINEAGE_GET_MODEL_FILE_ERROR = "Error when get model file size. {}"

    LINEAGE_METRIC_ERROR = "The parameter {} is invalid. " \
                           "It should be a dict and the value should be a float or a integer"

    LINEAGE_COMPARE_OPERATION_ERROR = "The schema error and compare operation should be" \
                                      " 'eq', 'lt', 'gt', 'ge', 'le', 'in'."

    LINEAGE_PARAM_SUMMARY_DIR_ERROR = "The parameter summary_dir is invalid. It should be a dict and the value " \
                                      "should be a string."

    LINEAGE_TRAIN_DATASET_PATH_ERROR = "The parameter train_dataset_path is invalid." \
                                       " It should be a dict and the value should be a string."

    LINEAGE_TRAIN_DATASET_COUNT_ERROR = "The parameter train_dataset_count is invalid. It should be a dict " \
                                        "and the value should be a integer between 0 and pow(2, 63) -1."

    LINEAGE_TEST_DATASET_PATH_ERROR = "The parameter test_dataset_path is invalid. " \
                                      "It should be a dict and the value should be a string."

    LINEAGE_TEST_DATASET_COUNT_ERROR = "The parameter test_dataset_count is invalid. It should be a dict " \
                                       "and the value should be a integer between 0 and pow(2, 63) -1."

    LINEAGE_NETWORK_ERROR = "The parameter network is invalid. It should be a dict and the value should be a string."

    LINEAGE_OPTIMIZER_ERROR = "The parameter optimizer is invalid. " \
                              "It should be a dict and the value should be a string."

    LINEAGE_LOSS_FUNCTION_ERROR = "The parameter loss_function is invalid. " \
                                  "It should be a dict and the value should be a string."

    LINEAGE_LOSS_ERROR = "The parameter loss is invalid. " \
                         "It should be a float."

    LINEAGE_MODEL_SIZE_ERROR = "The parameter model_size is invalid. " \
                               "It should be an integer between 0 and pow(2, 63) -1."

    LINEAGE_LEARNING_RATE_ERROR = "The parameter learning_rate is invalid. " \
                                  "It should be a dict and the value should be a float or a integer."

    LINEAGE_PARAM_SORTED_NAME_ERROR = "The parameter sorted_name is invalid. " \
                                      "It should be a string."

    LINEAGE_PARAM_SORTED_TYPE_ERROR = "The parameter sorted_type is invalid. " \
                                      "It should be a string."

    LINEAGE_PARAM_LINEAGE_TYPE_ERROR = "The parameter lineage_type is invalid. " \
                                       "It should be 'dataset' or 'model'."

    LINEAGE_PARAM_DATASET_MARK_ERROR = "The parameter dataset_mark is invalid. " \
                                       "It should be a string."

    SUMMARY_ANALYZE_ERROR = "Failed to analyze summary log. {}"
    SUMMARY_VERIFICATION_ERROR = "Verification failed in summary analysis. {}"

    # Querier error codes.
    EVENT_NOT_EXIST_ERROR = "Train and evaluation event not exist in summary log."
    QUERIER_PARAM_ERROR = "Querier param <{}> invalid. {}"
    SUMMARY_PARSE_FAIL_ERROR = "All summary logs parsing failed."
    EVENT_FIELD_NOT_EXIST_ERROR = 'Event field <{}> not exist.'

    LOG_LINEAGE_INFO_ERROR = "Fail to write lineage information into log file. {}"
