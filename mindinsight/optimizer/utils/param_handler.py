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
import numpy as np
from mindinsight.lineagemgr.model import LineageTable
from mindinsight.optimizer.common.enums import HyperParamKey, HyperParamType
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
        param_type = param_info[HyperParamKey.TYPE.value]
        value = array[index]
        if HyperParamKey.BOUND.value in param_info:
            bound = param_info[HyperParamKey.BOUND.value]
            value = max(bound[0], array[index])
            value = min(bound[1], value)
        if HyperParamKey.CHOICE.value in param_info:
            choices = param_info[HyperParamKey.CHOICE.value]
            nearest_index = int(np.argmin(np.fabs(np.array(choices) - value)))
            value = choices[nearest_index]
        if param_type == HyperParamType.INT.value:
            value = int(value)
        if HyperParamKey.DECIMAL.value in param_info:
            value = np.around(value, decimals=param_info[HyperParamKey.DECIMAL.value])
        array_new.append(value)
        index += 1
    return array_new


def organize_params_target(lineage_table: LineageTable, params_info: dict, target_name):
    """Organize params and target."""
    empty_result = np.array([])
    if lineage_table is None:
        return empty_result, empty_result

    param_keys = list(params_info.keys())

    lineage_df = lineage_table.dataframe_data
    try:
        lineage_df = lineage_df[param_keys + [target_name]]
        lineage_df = lineage_df.dropna(axis=0, how='any')
        return lineage_df[param_keys], lineage_df[target_name]
    except KeyError as exc:
        logger.warning("Some keys not exist in specified params or target. It will suggest params randomly."
                       "Detail: %s.", str(exc))
    return empty_result, empty_result
