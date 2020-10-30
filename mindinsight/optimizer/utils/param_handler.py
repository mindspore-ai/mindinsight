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
"""Utils for params."""
import math
import numpy as np

from mindinsight.lineagemgr.model import LineageTable, USER_DEFINED_PREFIX, METRIC_PREFIX
from mindinsight.optimizer.common.enums import HyperParamKey, HyperParamType, HyperParamSource, TargetKey, \
    TargetGoal, TunableSystemDefinedParams, TargetGroup, SystemDefinedTargets
from mindinsight.optimizer.common.log import logger


def generate_param(param_info, n=1):
    """Generate param."""
    value = None
    if HyperParamKey.BOUND.value in param_info:
        bound = param_info[HyperParamKey.BOUND.value]
        value = np.random.uniform(bound[0], bound[1], n)
        if param_info[HyperParamKey.TYPE.value] == HyperParamType.INT.value:
            value = value.astype(HyperParamType.INT.value)
    if HyperParamKey.CHOICE.value in param_info:
        indexes = np.random.randint(0, len(param_info[HyperParamKey.CHOICE.value]), n)
        value = [param_info[HyperParamKey.CHOICE.value][index] for index in indexes]
    if HyperParamKey.DECIMAL.value in param_info:
        value = np.around(value, decimals=param_info[HyperParamKey.DECIMAL.value])
    return np.array(value)


def generate_arrays(params_info: dict, n=1):
    """Generate arrays."""
    suggest_params = None
    for _, param_info in params_info.items():
        suggest_param = generate_param(param_info, n).reshape((-1, 1))
        if suggest_params is None:
            suggest_params = suggest_param
        else:
            suggest_params = np.hstack((suggest_params, suggest_param))
    if n == 1:
        return suggest_params[0]
    return suggest_params


def match_value_type(array, params_info: dict):
    """Make array match params type."""
    array_new = []
    index = 0
    for _, param_info in params_info.items():
        value = array[index]
        bound = param_info.get(HyperParamKey.BOUND.value)
        choice = param_info.get(HyperParamKey.CHOICE.value)
        if bound is not None:
            value = max(bound[0], array[index])
            value = min(bound[1], value)
        if choice is not None:
            nearest_index = int(np.argmin(np.fabs(np.array(choice) - value)))
            value = choice[nearest_index]
        if param_info.get(HyperParamKey.TYPE.value) == HyperParamType.INT.value:
            value = int(value)
            if bound is not None and value < bound[0]:
                value = math.ceil(bound[0])
            elif bound is not None and value >= bound[1]:
                # bound[1] is 2.0, value is 1; bound[1] is 2.1, value is 2
                value = math.floor(bound[1]) - 1
        if HyperParamKey.DECIMAL.value in param_info:
            value = np.around(value, decimals=param_info[HyperParamKey.DECIMAL.value])
        array_new.append(value)
        index += 1
    return array_new


def organize_params_target(lineage_table: LineageTable, params_info: dict, target_info):
    """Organize params and target."""
    empty_result = np.array([])
    if lineage_table is None:
        return empty_result, empty_result

    param_keys = []
    for param_key, param_info in params_info.items():
        # It will be a user_defined param:
        # 1. if 'source' is specified as 'user_defined'
        # 2. if 'source' is not specified and the param is not a system_defined key
        source = param_info.get(HyperParamKey.SOURCE.value)
        prefix = _get_prefix(param_key, source, HyperParamSource.USER_DEFINED.value,
                             USER_DEFINED_PREFIX, TunableSystemDefinedParams.list_members())
        param_key = f'{prefix}{param_key}'
        if prefix == USER_DEFINED_PREFIX:
            param_info[HyperParamKey.SOURCE.value] = HyperParamSource.USER_DEFINED.value
        else:
            param_info[HyperParamKey.SOURCE.value] = HyperParamSource.SYSTEM_DEFINED.value

        param_keys.append(param_key)

    target_name = target_info[TargetKey.NAME.value]
    group = target_info.get(TargetKey.GROUP.value)
    prefix = _get_prefix(target_name, group, TargetGroup.METRIC.value,
                         METRIC_PREFIX, SystemDefinedTargets.list_members())
    target_name = prefix + target_name
    lineage_df = lineage_table.dataframe_data
    try:
        lineage_df = lineage_df[param_keys + [target_name]]
        lineage_df = lineage_df.dropna(axis=0, how='any')

        target_column = np.array(lineage_df[target_name])
        if TargetKey.GOAL.value in target_info and \
                target_info.get(TargetKey.GOAL.value) == TargetGoal.MAXIMUM.value:
            target_column = -target_column

        return np.array(lineage_df[param_keys]), target_column
    except KeyError as exc:
        logger.warning("Some keys not exist in specified params or target. It will suggest params randomly."
                       "Detail: %s.", str(exc))
    return empty_result, empty_result


def _get_prefix(name, field, other_defined_field, other_defined_prefix, system_defined_fields):
    if (field == other_defined_field) or (field is None and name not in system_defined_fields):
        return other_defined_prefix
    return ''
