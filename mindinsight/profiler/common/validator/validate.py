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
"""Validate the profiler parameters."""
from mindinsight.profiler.common.exceptions.exceptions import ProfilerParamTypeErrorException, \
    ProfilerParamValueErrorException, ProfilerDeviceIdException, ProfilerOpTypeException, \
    ProfilerSortConditionException, ProfilerFilterConditionException, ProfilerGroupConditionException
from mindinsight.profiler.common.log import logger as log

AICORE_TYPE_COL = ["op_type", "execution_time", "execution_frequency", "precent"]
AICORE_DETAIL_COL = ["op_name", "op_type", "execution_time", "subgraph", "full_op_name"]
AICPU_COL = ["serial_number", "op_name", "total_time", "dispatch_time", "RunV2_start",
             "compute_start", "memcpy_start", "memcpy_end", "RunV2_end"]


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
        op_type = search_condition.get("op_type")
        if op_type == "aicpu":
            search_scope = AICPU_COL
        elif op_type == "aicore_type":
            search_scope = AICORE_TYPE_COL
        elif op_type == "aicore_detail":
            search_scope = AICORE_DETAIL_COL
        else:
            raise ProfilerOpTypeException("The op_type must in ['aicpu', 'aicore_type', 'aicore_detail']")
    else:
        raise ProfilerOpTypeException("The op_type must in ['aicpu', 'aicore_type', 'aicore_detail']")

    if "group_condition" in search_condition:
        group_condition = search_condition.get("group_condition")
        if not isinstance(group_condition, dict):
            raise ProfilerGroupConditionException("The group condition must be dict.")
        if "limit" in group_condition:
            limit = group_condition.get("limit", 0)
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

    if "sort_condition" in search_condition:
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
            if sorted_type not in sorted_type_param:
                err_msg = "The sorted type must be ascending or descending."
                log.error(err_msg)
                raise ProfilerParamValueErrorException(err_msg)

    if "filter_condition" in search_condition:
        def validate_op_filter_condition(op_condition):
            if not isinstance(op_condition, dict):
                raise ProfilerFilterConditionException("Wrong op_type filter condition.")
            for key, value in op_condition.items():
                if not isinstance(key, str):
                    raise ProfilerFilterConditionException("The filter key must be str")
                if not isinstance(value, list):
                    raise ProfilerFilterConditionException("The filter value must be list")
                if key not in filter_key:
                    raise ProfilerFilterConditionException("The filter key must in {}.".format(filter_key))
                for item in value:
                    if not isinstance(item, str):
                        raise ProfilerFilterConditionException("The item in filter value must be str")

        filter_condition = search_condition.get("filter_condition")
        if not isinstance(filter_condition, dict):
            raise ProfilerFilterConditionException("The filter condition must be dict.")
        filter_key = ["in", "not_in", "partial_match_str_in"]
        if filter_condition:
            if "op_type" in filter_condition:
                op_type_condition = filter_condition.get("op_type")
                validate_op_filter_condition(op_type_condition)
            if "op_name" in filter_condition:
                op_name_condition = filter_condition.get("op_name")
                validate_op_filter_condition(op_name_condition)
            if "op_type" not in filter_condition and "op_name" not in filter_condition:
                raise ProfilerFilterConditionException("The key of filter_condition is not support")
