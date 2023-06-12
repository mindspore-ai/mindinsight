# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""Validate the profiler parameters."""
import os
import sys

from mindinsight.datavisual.utils.tools import to_int
from mindinsight.profiler.common.exceptions.exceptions import ProfilerParamTypeErrorException, \
    ProfilerDeviceIdException, ProfilerOpTypeException, \
    ProfilerSortConditionException, ProfilerFilterConditionException, \
    ProfilerGroupConditionException, ProfilerParamValueErrorException
from mindinsight.profiler.common.log import logger as log

AICORE_TYPE_COL = ["op_type", "total_time", "execution_frequency", "percent"]
AICORE_DETAIL_COL = ["op_name", "op_type", "avg_execution_time", "execution_frequency", "FLOPs(cube)",
                     "FLOPS(cube)", "FLOPs(vec)", "FLOPS(vec)", "full_op_name",]
PYNATIVE_TYPE_COL = ["op_type", "execution_time", "execution_frequency", "percent"]
PYNATIVE_DETAIL_COL = ["op_name", "op_type", "avg_execution_time", "subgraph", "full_op_name"]
AICPU_TYPE_COL = ["op_type", "total_time", "execution_frequency", "percent"]
AICPU_DETAIL_COL = ["op_name", "serial_number", "op_type", "avg_execution_time", "dispatch_time", "execution_frequency",
                    "run_start", "run_end"]
GPU_TYPE_COL = ["op_type", "type_occurrences", "total_time", "proportion", "avg_time"]
GPU_OP_TYPE_COL = ["op_side", "op_type", "op_name", "duration"]
GPU_CUDA_TYPE_COL = ["op_type", "op_name", "op_full_name", "duration"]
GPU_ACTIVITY_COL = ["name", "type", "op_full_name", "stream_id",
                    "block_dim", "grid_dim", "occurrences", "total_duration",
                    "avg_duration", "max_duration", "min_duration"]
GPU_DETAIL_COL = ["op_side", "op_type", "op_name", "op_full_name",
                  "op_occurrences", "op_total_time", "op_avg_time",
                  "proportion", "cuda_activity_cost_time", "cuda_activity_call_count"]
CPU_TYPE_COL = ["op_type", "type_occurrences", "execution_frequency", "total_compute_time",
                "avg_time", "total_time_proportion"]
CPU_DETAIL_COL = ["op_side", "op_type", "op_name", "full_op_name", "op_occurrences",
                  "op_total_time", "op_avg_time", "total_time_proportion", "subgraph"]
MINDDATA_PIPELINE_COL = [
    'op_id', 'op_type', 'num_workers', 'output_queue_average_size',
    'output_queue_length', 'output_queue_usage_rate', 'sample_interval',
    'parent_id'
]


def validate_condition(search_condition):
    """
    Verify the param in search_condition is valid or not.

    Args:
        search_condition (dict): The search condition.

    Raises:
        ProfilerParamTypeErrorException: If the type of the param in search_condition is invalid.
        ProfilerDeviceIdException: If the device_id param in search_condition is invalid.
        ProfilerOpTypeException: If the op_type param in search_condition is invalid.
        ProfilerGroupConditionException: If the group_condition param in search_condition is invalid.
        ProfilerSortConditionException: If the sort_condition param in search_condition is invalid.
        ProfilerFilterConditionException: If the filter_condition param in search_condition is invalid.
    """
    if not isinstance(search_condition, dict):
        log.error("Invalid search_condition type, it should be dict.")
        raise ProfilerParamTypeErrorException(
            "Invalid search_condition type, it should be dict.")

    if "device_id" in search_condition:
        device_id = search_condition.get("device_id")
        if not isinstance(device_id, str):
            raise ProfilerDeviceIdException("Invalid device_id type, it should be str.")

    if "op_type" in search_condition:
        search_scope = get_search_scope(search_condition)
    else:
        raise ProfilerOpTypeException(
            "The op_type must in ['aicpu_type','aicpu_detail', 'aicore_type', 'aicore_detail', "
            "'gpu_op_type', 'gpu_op_info', 'gpu_cuda_activity', 'cpu_op_type', 'cpu_op_info', "
            "'gpu_op_type_info', 'gpu_cuda_type_info']")

    if "group_condition" in search_condition:
        validate_group_condition(search_condition)

    if "sort_condition" in search_condition:
        validate_sort_condition(search_condition, search_scope)

    if "filter_condition" in search_condition:
        validate_filter_condition(search_condition)


def get_search_scope(search_condition):
    """Get search scope."""
    op_type = search_condition.get("op_type")
    if op_type == "aicpu_type":
        search_scope = AICPU_TYPE_COL
    elif op_type == "aicpu_detail":
        search_scope = AICPU_DETAIL_COL
    elif op_type == "aicore_type":
        search_scope = AICORE_TYPE_COL
    elif op_type == "aicore_detail":
        search_scope = AICORE_DETAIL_COL
    elif op_type == "gpu_op_type":
        search_scope = GPU_TYPE_COL
    elif op_type == "gpu_op_info":
        search_scope = GPU_DETAIL_COL
    elif op_type == "gpu_cuda_activity":
        search_scope = GPU_ACTIVITY_COL
    elif op_type == "cpu_op_type":
        search_scope = CPU_TYPE_COL
    elif op_type == "cpu_op_info":
        search_scope = CPU_DETAIL_COL
    elif op_type == "pynative_type":
        search_scope = PYNATIVE_TYPE_COL
    elif op_type == "pynative_detail":
        search_scope = PYNATIVE_DETAIL_COL
    elif op_type == "gpu_op_type_info":
        search_scope = GPU_OP_TYPE_COL
    elif op_type == "gpu_cuda_type_info":
        search_scope = GPU_CUDA_TYPE_COL
    else:
        raise ProfilerOpTypeException(
            "The op_type must in ['aicpu_type','aicpu_detail', 'aicore_type', 'aicore_detail', "
            "'gpu_op_type', 'gpu_op_info', 'gpu_cuda_activity', 'cpu_op_type', 'cpu_op_info', "
            "'gpu_op_type_info', 'gpu_cuda_type_info']")
    return search_scope


def validate_group_condition(search_condition):
    """
    Verify the group_condition in search_condition is valid or not.

    Args:
        search_condition (dict): The search condition.

    Raises:
        ProfilerGroupConditionException: If the group_condition param in search_condition is invalid.
    """
    group_condition = search_condition.get("group_condition")
    if not isinstance(group_condition, dict):
        raise ProfilerGroupConditionException("The group condition must be dict.")
    if "limit" in group_condition:
        limit = group_condition.get("limit", 10)
        if isinstance(limit, bool) \
                or not isinstance(group_condition.get("limit"), int):
            log.error("The limit must be int.")
            raise ProfilerGroupConditionException("The limit must be int.")
        if limit < 1 or limit > 100:
            raise ProfilerGroupConditionException("The limit must in [1, 100].")

    if "offset" in group_condition:
        offset = group_condition.get("offset", 0)
        if isinstance(offset, bool) \
                or not isinstance(group_condition.get("offset"), int):
            log.error("The offset must be int.")
            raise ProfilerGroupConditionException("The offset must be int.")
        if offset < 0:
            raise ProfilerGroupConditionException("The offset must ge 0.")

        if offset > 1000000:
            raise ProfilerGroupConditionException("The offset must le 1000000.")


def validate_sort_condition(search_condition, search_scope):
    """
    Verify the sort_condition in search_condition is valid or not.

    Args:
        search_condition (dict): The search condition.
        search_scope (list): The search scope.

    Raises:
        ProfilerSortConditionException: If the sort_condition param in search_condition is invalid.
    """
    sort_condition = search_condition.get("sort_condition")
    if not isinstance(sort_condition, dict):
        raise ProfilerSortConditionException("The sort condition must be dict.")
    if "name" in sort_condition:
        sorted_name = sort_condition.get("name", "")
        err_msg = "The sorted_name must be in {}".format(search_scope)
        if not isinstance(sorted_name, str):
            log.error("Wrong sorted name type.")
            raise ProfilerSortConditionException("Wrong sorted name type.")
        if sorted_name not in search_scope:
            log.error(err_msg)
            raise ProfilerSortConditionException(err_msg)

    if "type" in sort_condition:
        sorted_type_param = ['ascending', 'descending']
        sorted_type = sort_condition.get("type")
        if sorted_type and sorted_type not in sorted_type_param:
            err_msg = "The sorted type must be ascending or descending."
            log.error(err_msg)
            raise ProfilerSortConditionException(err_msg)


def validate_op_filter_condition(op_condition, value_type=str, value_type_msg='str'):
    """
    Verify the op_condition in filter_condition is valid or not.

    Args:
        op_condition (dict): The op_condition in search_condition.
        value_type (type): The value type. Default: str.
        value_type_msg (str): The value type message. Default: 'str'.

    Raises:
        ProfilerFilterConditionException: If the filter_condition param in search_condition is invalid.
    """
    filter_key = ["in", "not_in", "partial_match_str_in", "display_op_type", "step"]
    if not isinstance(op_condition, dict):
        raise ProfilerFilterConditionException("The filter condition value must be dict.")
    for key, value in op_condition.items():
        if not isinstance(key, str):
            raise ProfilerFilterConditionException("The filter key must be str")
        if not isinstance(value, list):
            raise ProfilerFilterConditionException("The filter value must be list")
        if key not in filter_key:
            raise ProfilerFilterConditionException("The filter key must in {}.".format(filter_key))
        for item in value:
            if not isinstance(item, value_type):
                raise ProfilerFilterConditionException(
                    "The item in filter value must be {}.".format(value_type_msg)
                )


def validate_filter_condition(search_condition):
    """
    Verify the filter_condition in search_condition is valid or not.

    Args:
        search_condition (dict): The search condition.

    Raises:
        ProfilerFilterConditionException: If the filter_condition param in search_condition is invalid.
    """
    filter_condition = search_condition.get("filter_condition")
    if not isinstance(filter_condition, dict):
        raise ProfilerFilterConditionException("The filter condition must be dict.")
    if filter_condition:
        if "op_type" in filter_condition:
            op_type_condition = filter_condition.get("op_type")
            validate_op_filter_condition(op_type_condition)
        if "op_name" in filter_condition:
            op_name_condition = filter_condition.get("op_name")
            validate_op_filter_condition(op_name_condition)


def validate_and_set_job_id_env(job_id_env):
    """
    Validate the job id and set it in environment.

    Args:
        job_id_env (str): The id that to be set in environment parameter `JOB_ID`.

    Returns:
        int, the valid job id env.
    """
    if job_id_env is None:
        return job_id_env
    # get job_id_env in int type
    valid_id = to_int(job_id_env, 'job_id_env')
    # check the range of valid_id
    if valid_id and 255 < valid_id < sys.maxsize:
        os.environ['JOB_ID'] = job_id_env
    else:
        log.warning("Invalid job_id_env %s. The value should be int and between 255 and %s. Use"
                    "default job id env instead.",
                    job_id_env, sys.maxsize)
    return valid_id


def validate_ui_proc(proc_name):
    """
    Validate proc name in restful request.

    Args:
        proc_name (str): The proc name to query. Acceptable value is in
        [`iteration_interval`, `fp_and_bp`, `fp`, `tail`].

    Raises:
        ProfilerParamValueErrorException: If the proc_name is invalid.
    """
    accept_names = ['iteration_interval', 'fp_and_bp', 'fp', 'tail']
    if proc_name not in accept_names:
        log.error("Invalid proc_name. The proc_name for restful api is in %s", accept_names)
        raise ProfilerParamValueErrorException(f'proc_name should be in {accept_names}.')


def validate_minddata_pipeline_condition(condition):
    """
    Verify the minddata pipeline search condition is valid or not.

    Args:
        condition (dict): The minddata pipeline search condition.

    Raises:
        ProfilerParamTypeErrorException: If the type of the search condition is
            invalid.
        ProfilerDeviceIdException: If the device_id param in the search
            condition is invalid.
        ProfilerGroupConditionException: If the group_condition param in the
            search condition is invalid.
        ProfilerSortConditionException: If the sort_condition param in the
            search condition is invalid.
        ProfilerFilterConditionException: If the filter_condition param in the
            search condition is invalid.
    """
    if not isinstance(condition, dict):
        log.error("Invalid condition type, it should be dict.")
        raise ProfilerParamTypeErrorException(
            "Invalid condition type, it should be dict."
        )

    if "device_id" in condition:
        device_id = condition.get("device_id")
        if not isinstance(device_id, str):
            raise ProfilerDeviceIdException(
                "Invalid device_id type, it should be str."
            )

    if "group_condition" in condition:
        validate_group_condition(condition)

    if "sort_condition" in condition:
        validate_sort_condition(condition, MINDDATA_PIPELINE_COL)

    if "filter_condition" in condition:
        filter_condition = condition.get('filter_condition')
        if not isinstance(filter_condition, dict):
            raise ProfilerFilterConditionException(
                "The filter condition must be dict."
            )
        for key, value in filter_condition.items():
            if key == 'op_id':
                validate_op_filter_condition(
                    value, value_type=int, value_type_msg='int'
                )
            elif key == 'op_type':
                validate_op_filter_condition(value)
            elif key == 'is_display_op_detail':
                if not isinstance(value, bool):
                    raise ProfilerFilterConditionException(
                        "The condition must be bool."
                    )
            else:
                raise ProfilerFilterConditionException(
                    "The key {} of filter_condition is not support.".format(key)
                )
