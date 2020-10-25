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
"""Transformer."""
from mindinsight.optimizer.utils.param_handler import match_value_type
from mindinsight.optimizer.common.enums import HyperParamSource, HyperParamKey


class Transformer:
    """Transformer."""
    @staticmethod
    def transform_list_to_dict(params_info, suggest_list):
        """Transform from tuner."""
        suggest_list = match_value_type(suggest_list, params_info)
        param_dict = {}
        user_defined_info = {}
        for index, param_name in enumerate(params_info):
            param_item = {param_name: suggest_list[index]}
            param_dict.update(param_item)
            source = params_info.get(param_name).get(HyperParamKey.SOURCE.value)
            if source is not None and source == HyperParamSource.USER_DEFINED.value:
                user_defined_info.update(param_item)

        return param_dict, user_defined_info
