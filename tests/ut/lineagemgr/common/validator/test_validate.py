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

from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError, LineageParamValueError
from mindinsight.lineagemgr.common.validator.model_parameter import SearchModelConditionParameter
from mindinsight.lineagemgr.common.validator.validate import \
    validate_search_model_condition, validate_condition, validate_train_id
from mindinsight.utils.exceptions import MindInsightException, ParamValueError


class TestValidateSearchModelCondition(TestCase):
    """Test the mothod of validate_search_model_condition."""
    def test_validate_search_model_condition_param_type_error(self):
        """Test the method of validate_search_model_condition with LineageParamTypeError."""
        condition = {
            'summary_dir': 'xxx'
        }
        self._assert_raise_of_lineage_param_type_error(
            'The search_condition element summary_dir should be dict.',
            condition
        )

    def test_validate_search_model_condition_param_value_error(self):
        """Test the mothod of validate_search_model_condition with LineageParamValueError."""
        condition = {
            'xxx': 'xxx'
        }
        self._assert_raise_of_lineage_param_value_error(
            'The search attribute not supported.',
            condition
        )

        condition = {
            'learning_rate': {
                'xxx': 'xxx'
            }
        }
        self._assert_raise_of_lineage_param_value_error(
            "The compare condition should be in",
            condition
        )

        condition = {
            1: {
                "ge": 8.0
            }
        }
        self._assert_raise_of_lineage_param_value_error(
            "The search attribute not supported.",
            condition
        )

        condition = {
            'metric_': {
                "ge": 8.0
            }
        }
        self._assert_raise_of_lineage_param_value_error(
            "The search attribute not supported.",
            condition
        )

    def test_validate_search_model_condition_mindinsight_exception_1(self):
        """Test the mothod of validate_search_model_condition with MindinsightException."""
        condition = {
            "offset": 100001
        }
        self._assert_raise_of_mindinsight_exception(
            "Invalid input offset. 0 <= offset <= 100000",
            condition
        )

        condition = {
            'summary_dir': {
                'eq': 111
            },
            'limit': 10
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter summary_dir is invalid. It should be a dict and "
            "the value should be a string",
            condition
        )

        condition = {
            'learning_rate': {
                'in': 1.0
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The value of `in` operation must be list or tuple.",
            condition
        )

        condition = {
            'learning_rate': {
                'lt': True
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter learning_rate is invalid. It should be a dict and "
            "the value should be a float or a integer",
            condition
        )

    def test_validate_search_model_condition_mindinsight_exception_2(self):
        """Test the mothod of validate_search_model_condition with MindinsightException."""
        condition = {
            'learning_rate': {
                'gt': [1.0]
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter learning_rate is invalid. It should be a dict and "
            "the value should be a float or a integer",
            condition
        )

        condition = {
            'loss_function': {
                'ge': 1
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter loss_function is invalid. "
            "Its operation should be `eq`, `in` or `not_in`.",
            condition
        )

        condition = {
            'train_dataset_count': {
                'in': 2
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The value of `in` operation must be list or tuple.",
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
        self._assert_raise_of_mindinsight_exception(
            "The parameter network is invalid. "
            "Its operation should be `eq`, `in` or `not_in`.",
            condition
        )

    def test_validate_search_model_condition_mindinsight_exception_3(self):
        """Test the mothod of validate_search_model_condition with MindinsightException."""
        condition = {
            'batch_size': {
                'lt': 2,
                'gt': 'xxx'
            },
            'model_size': {
                'eq': 222
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter batch_size is invalid. It should be a non-negative integer.",
            condition
        )

        condition = {
            'test_dataset_count': {
                'lt': -2
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter test_dataset_count is invalid. It should be a dict "
            "and the value should be a integer between 0",
            condition
        )

        condition = {
            'epoch': {
                'lt': False
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter epoch is invalid. It should be a positive integer.",
            condition
        )

        condition = {
            "learning_rate": {
                "ge": ""
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter learning_rate is invalid. It should be a dict and "
            "the value should be a float or a integer",
            condition
        )

    def test_validate_search_model_condition_mindinsight_exception_4(self):
        """Test the mothod of validate_search_model_condition with MindinsightException."""
        condition = {
            "train_dataset_count": {
                "ge": 8.0
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter train_dataset_count is invalid. It should be a dict "
            "and the value should be a integer between 0",
            condition
        )

        condition = {
            'metric/attribute': {
                'ge': 'xxx'
            }
        }
        self._assert_raise_of_mindinsight_exception(
            "The parameter metric/attribute is invalid. "
            "It should be a dict and the value should be a float or a integer",
            condition
        )

    def _assert_raise(self, exception, msg, condition):
        """
        Assert raise by unittest.

        Args:
            exception (Type): Exception class expected to be raised.
            msg (msg): Expected error message.
            condition (dict): The parameter of search condition.
        """
        self.assertRaisesRegex(
            exception,
            msg,
            validate_search_model_condition,
            SearchModelConditionParameter,
            condition
        )

    def _assert_raise_of_mindinsight_exception(self, msg, condition):
        """
        Assert raise of MindinsightException by unittest.

        Args:
            msg (msg): Expected error message.
            condition (dict): The parameter of search condition.
        """
        self._assert_raise(MindInsightException, msg, condition)

    def _assert_raise_of_lineage_param_value_error(self, msg, condition):
        """
        Assert raise of LineageParamValueError by unittest.

        Args:
            msg (msg): Expected error message.
            condition (dict): The parameter of search condition.
        """
        self._assert_raise(LineageParamValueError, msg, condition)

    def _assert_raise_of_lineage_param_type_error(self, msg, condition):
        """
        Assert raise of LineageParamTypeError by unittest.

        Args:
            msg (msg): Expected error message.
            condition (dict): The parameter of search condition.
        """
        self._assert_raise(LineageParamTypeError, msg, condition)

    def test_validate_condition(self):
        """Test the method of validate_condition."""
        condition = [1, 2, 3]
        self._assert_raise_2(LineageParamTypeError, "Invalid search_condition type, it should be dict.", condition)

        condition = {
            'limit': False
        }
        self._assert_raise_2(LineageParamTypeError, "The limit must be int.", condition)

        condition = {
            'offset': False
        }
        self._assert_raise_2(LineageParamTypeError, "The offset must be int.", condition)

        condition = {
            'sorted_type': 'ascending'
        }
        msg = "The sorted_name must exist when sorted_type exists."
        self._assert_raise_2(LineageParamValueError, msg, condition)

        condition = {
            'sorted_type': 'invalid',
            'sorted_name': 'tag'
        }
        msg = "The sorted_type must be ascending or descending."
        self._assert_raise_2(LineageParamValueError, msg, condition)

    def _assert_raise_2(self, exception, msg, condition):
        """
        Assert raise by unittest.

        Args:
            exception (Type): Exception class expected to be raised.
            msg (msg): Expected error message.
            condition (dict): The parameter of search condition.
        """
        self.assertRaisesRegex(
            exception,
            msg,
            validate_condition,
            condition
        )

    def test_validate_train_id(self):
        """Test the test_validate_train_id function."""
        path = 'invalid'
        self.assertRaisesRegex(
            ParamValueError,
            "Summary dir should be relative path starting with './'.",
            validate_train_id,
            path
        )

        path = './a/b/c'
        self.assertRaisesRegex(
            ParamValueError,
            "Summary dir should be relative path starting with './'.",
            validate_train_id,
            path
        )
