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
"""Test the validate module."""
from unittest import TestCase

from mindinsight.lineagemgr.common.exceptions.exceptions import \
    LineageParamValueError, LineageParamTypeError
from mindinsight.lineagemgr.common.validator.model_parameter import \
    SearchModelConditionParameter
from mindinsight.lineagemgr.common.validator.validate import \
    validate_search_model_condition
from mindinsight.utils.exceptions import MindInsightException


class TestValidateSearchModelCondition(TestCase):
    """Test the mothod of validate_search_model_condition."""
    def test_validate_search_model_condition(self):
        """Test the mothod of validate_search_model_condition."""
        condition = {
            'summary_dir': 'xxx'
        }
        self.assertRaisesRegex(
            LineageParamTypeError,
            'The search_condition element summary_dir should be dict.',
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'xxx': 'xxx'
        }
        self.assertRaisesRegex(
            LineageParamValueError,
            'The search attribute not supported.',
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'learning_rate': {
                'xxx': 'xxx'
            }
        }
        self.assertRaisesRegex(
            LineageParamValueError,
            "The compare condition should be in",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            "offset": 100001
        }
        self.assertRaisesRegex(
            MindInsightException,
            "Invalid input offset. 0 <= offset <= 100000",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'summary_dir': {
                'eq': 111
            },
            'limit': 10
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter summary_dir is invalid. It should be a dict and the value should be a string",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'learning_rate': {
                'in': 1.0
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter learning_rate is invalid. It should be a dict and the value should be a float or a integer",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'learning_rate': {
                'lt': True
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter learning_rate is invalid. It should be a dict and the value should be a float or a integer",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'learning_rate': {
                'gt': [1.0]
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter learning_rate is invalid. It should be a dict and the value should be a float or a integer",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'loss_function': {
                'ge': 1
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter loss_function is invalid. It should be a dict and the value should be a string",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'train_dataset_count': {
                'in': 2
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter train_dataset_count is invalid. It should be a dict "
            "and the value should be a integer between 0",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'network': {
                'le': 2
            },
            'optimizer': {
                'eq': 'xxx'
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter network is invalid. It should be a dict and the value should be a string",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'batch_size': {
                'lt': 2,
                'gt': 'xxx'
            },
            'model_size': {
                'eq': 222
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter batch_size is invalid. It should be a non-negative integer.",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'test_dataset_count': {
                'lt': -2
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter test_dataset_count is invalid. It should be a dict "
            "and the value should be a integer between 0",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'epoch': {
                'lt': False
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter epoch is invalid. It should be a positive integer.",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            "learning_rate": {
                "ge": ""
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter learning_rate is invalid. It should be a dict and the value should be a float or a integer",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            "train_dataset_count": {
                "ge": 8.0
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter train_dataset_count is invalid. It should be a dict "
            "and the value should be a integer between 0",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            1: {
                "ge": 8.0
            }
        }
        self.assertRaisesRegex(
            LineageParamValueError,
            "The search attribute not supported.",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'metric_': {
                "ge": 8.0
            }
        }
        LineageParamValueError('The search attribute not supported.')
        self.assertRaisesRegex(
            LineageParamValueError,
            "The search attribute not supported.",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

        condition = {
            'metric_attribute': {
                'ge': 'xxx'
            }
        }
        self.assertRaisesRegex(
            MindInsightException,
            "The parameter metric_attribute is invalid. "
            "It should be a dict and the value should be a float or a integer",
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )
