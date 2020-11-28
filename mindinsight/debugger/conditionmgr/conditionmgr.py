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
"""
Condition manager..

This module provide condition manager function.
"""
from mindinsight.debugger.conditionmgr.condition import Condition
from mindinsight.debugger.conditionmgr.condition import TargetTypeEnum
from mindinsight.debugger.conditionmgr.condition_list import CONDITION_LIST
from mindinsight.debugger.conditionmgr.log import logger


class ConditionMgr:
    """Condition manager."""

    def __init__(self):
        self.conditions = {}
        self.no_parameter_conditions = []
        self._register_default_conditions()

    def _register_default_conditions(self):
        """Register default condition definitions"""
        self.register_conditions(CONDITION_LIST)

    def register_condition(self, condition):
        """Register conditions into dict"""
        if not condition.parameters:
            self.no_parameter_conditions.append(condition.id)
        self.conditions[condition.id] = condition

    def register_conditions(self, conditions):
        """Register conditions"""
        for condition in conditions:
            self.register_condition(condition)

    def get_condition(self, condition_id) -> Condition:
        """Get condition by condition id"""
        return self.conditions[condition_id]

    def has_condition(self, condition_id, condition_context) -> bool:
        """Return if the condition exist and avilible"""
        if condition_id in self.conditions:
            condition = self.get_condition(condition_id)
            return condition.is_available(condition_context)
        logger.warning("Condition id %s not found.", condition_id)
        return False

    def get_no_param_condition(self) -> list:
        """Return the list of condition without parameters"""
        return self.no_parameter_conditions

    @staticmethod
    def check_and_sort(collections, target_type, reply):
        """Check the collection and sort conditions"""
        collection = collections.get(target_type)
        if collection:
            collection = sorted(collection, key=lambda x: x.get('id'))
            reply.append({"id": target_type + "_condition_collection", "conditions": collection})
        else:
            logger.warning("Condition collection for %s is None.", target_type)

    def get_all_collections(self, condition_context):
        """Get all register conditions."""

        collections = {
            TargetTypeEnum.WEIGHT.value: [], TargetTypeEnum.TENSOR.value: [], TargetTypeEnum.GRADIENT.value: [],
            TargetTypeEnum.ACTIVATION.value: []
        }
        for condition in self.conditions.values():
            parameters = []
            if not condition.is_available(condition_context):
                continue
            for param in condition.parameters:
                if not param.visible_on_ui:
                    continue
                parameters.append({
                    "name": param.name,
                    "type": param.type.name,
                    "support_disable": param.support_disable,
                    "default_value": param.default_value,
                    "param_type": param.param_type,
                    "required_params": param.required_params
                })
            collections[condition.supported_target_type.value].append({
                "id": condition.id,
                "parameters": parameters,
                "supported_target_type": condition.supported_target_type.name,
                "abbr": condition.abbr
            })

        reply = []
        self.check_and_sort(collections, TargetTypeEnum.TENSOR.value, reply)
        self.check_and_sort(collections, TargetTypeEnum.WEIGHT.value, reply)
        self.check_and_sort(collections, TargetTypeEnum.ACTIVATION.value, reply)
        self.check_and_sort(collections, TargetTypeEnum.GRADIENT.value, reply)

        return reply
