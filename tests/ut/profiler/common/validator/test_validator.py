# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Test the validator module."""
import pytest

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerParamTypeErrorException, ProfilerDeviceIdException, \
    ProfilerGroupConditionException, ProfilerSortConditionException, \
    ProfilerFilterConditionException, ProfilerOpTypeException
from mindinsight.profiler.common.validator.validate import \
    validate_minddata_pipeline_condition, validate_condition


class TestMinddataPipelineCondition:
    """Test the method of `validate_minddata_pipeline_condition`."""
    def test_validate_minddata_pipeline_condition_1(self):
        """Test the method exceptions."""
        with pytest.raises(ProfilerParamTypeErrorException) as exc_info:
            validate_minddata_pipeline_condition([])
        assert exc_info.value.error_code == '50546082'
        assert exc_info.value.message == 'Param type error. Invalid condition ' \
                                         'type, it should be dict.'

    def test_validate_minddata_pipeline_condition_2(self):
        """Test the method exceptions."""
        condition = {'device_id': 0}
        with pytest.raises(ProfilerDeviceIdException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546182'
        assert exc_info.value.message == 'The device_id in search_condition error, ' \
                                         'Invalid device_id type, it should be str.'

    def test_validate_minddata_pipeline_condition_3(self):
        """Test the method exceptions."""
        condition = {'group_condition': 0}
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The group condition must be dict.'

        condition = {
            'group_condition': {
                'limit': '1'
            }
        }
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The limit must be int.'

        condition = {
            'group_condition': {
                'limit': '1'
            }
        }
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The limit must be int.'

    def test_validate_minddata_pipeline_condition_4(self):
        """Test the method exceptions."""
        condition = {
            'group_condition': {
                'limit': 0
            }
        }
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The limit must in [1, 100].'

        condition = {
            'group_condition': {
                'offset': '0'
            }
        }
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The offset must be int.'

        condition = {
            'group_condition': {
                'offset': 1000001
            }
        }
        with pytest.raises(ProfilerGroupConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546184'
        assert exc_info.value.message == 'The group_condition in search_condition error, ' \
                                         'The offset must le 1000000.'

    def test_validate_minddata_pipeline_condition_5(self):
        """Test the method exceptions."""
        condition = {'sort_condition': 0}
        with pytest.raises(ProfilerSortConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546185'
        assert exc_info.value.message == 'The sort_condition in search_condition error, ' \
                                         'The sort condition must be dict.'

        condition = {
            'sort_condition': {
                'name': 0
            }
        }
        with pytest.raises(ProfilerSortConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546185'
        assert exc_info.value.message == 'The sort_condition in search_condition error, ' \
                                         'Wrong sorted name type.'

        condition = {
            'sort_condition': {
                'name': 'xxx'
            }
        }
        with pytest.raises(ProfilerSortConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546185'
        assert exc_info.value.message.startswith(
            'The sort_condition in search_condition error, The sorted_name must be in'
        )

        condition = {
            'sort_condition': {
                'name': 'output_queue_usage_rate',
                'type': 'xxx'
            }
        }
        with pytest.raises(ProfilerSortConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546185'
        assert exc_info.value.message == 'The sort_condition in search_condition error, ' \
                                         'The sorted type must be ascending or descending.'

    def test_validate_minddata_pipeline_condition_6(self):
        """Test the method exceptions."""
        condition = {
            'filter_condition': '0'
        }
        with pytest.raises(ProfilerFilterConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546186'
        assert exc_info.value.message == 'The filter_condition in search_condition error, ' \
                                         'The filter condition must be dict.'

        condition = {
            'filter_condition': {
                'xxx': 0
            }
        }
        with pytest.raises(ProfilerFilterConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546186'
        assert exc_info.value.message == 'The filter_condition in search_condition error, ' \
                                         'The key xxx of filter_condition is not support.'

        condition = {
            'filter_condition': {
                'is_display_op_detail': 0
            }
        }
        with pytest.raises(ProfilerFilterConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546186'
        assert exc_info.value.message == 'The filter_condition in search_condition error, ' \
                                         'The condition must be bool.'

    def test_validate_minddata_pipeline_condition_7(self):
        """Test the method exceptions."""
        condition = {
            'filter_condition': {
                'op_id': 0
            }
        }
        with pytest.raises(ProfilerFilterConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546186'
        assert exc_info.value.message == 'The filter_condition in search_condition error, ' \
                                         'The filter condition value must be dict.'

        condition = {
            'filter_condition': {
                'op_id': {
                    'in': ['0']
                }
            }
        }
        with pytest.raises(ProfilerFilterConditionException) as exc_info:
            validate_minddata_pipeline_condition(condition)
        assert exc_info.value.error_code == '50546186'
        assert exc_info.value.message == 'The filter_condition in search_condition error, ' \
                                         'The item in filter value must be int.'


class TestValidateCondition:
    """Test the function of validate condition."""
    def test_validate_condition_normal(self):
        """Test the validate condition of normal input."""
        op_type_list = ['aicpu_type', 'aicpu_detail', 'aicore_type', 'aicore_detail',
                        'gpu_op_type', 'gpu_op_info', 'gpu_cuda_activity']
        sort_name_list = ['op_type', 'serial_number', 'op_type', 'op_name',
                          'op_type', 'op_side', 'name']
        for idx, op_type in enumerate(op_type_list):
            condition = {
                'device_id': '0',
                'op_type': op_type,
                'filter_condition': {
                    'op_id': 0
                },
                'group_condition': {
                    'limit': 1,
                    'offset': 1
                },
                'sort_condition': {
                    'name': sort_name_list[idx],
                    'type': 'ascending'
                }
            }
            validate_condition(condition)

    def test_validate_condition_param_type_error_exception(self):
        """Test the exception of parameter type error."""
        condition = "not a dict"
        exception_message = 'Param type error. Invalid search_condition type, it should be dict.'
        with pytest.raises(ProfilerParamTypeErrorException) as exc_info:
            validate_condition(condition)
        assert exc_info.value.error_code == '50546082'
        assert exc_info.value.message == exception_message

    def test_validate_condition_op_type_exception(self):
        """Test the exception of profiler operation type."""
        condition_list = [{'op_type': "xxx"}, {}]
        exception_message = "The op_type in search_condition error, The op_type must in " \
                            "['aicpu_type','aicpu_detail', 'aicore_type', 'aicore_detail', "\
                            "'gpu_op_type', 'gpu_op_info', 'gpu_cuda_activity', 'cpu_op_type', 'cpu_op_info']"
        for condition in condition_list:
            with pytest.raises(ProfilerOpTypeException) as exc_info:
                validate_condition(condition)
            assert exc_info.value.error_code == '50546183'
            assert exc_info.value.message == exception_message

    def test_validate_condition_group_exception(self):
        """Test the exception of group condition related."""
        condition_list = [
            {
                'op_type': 'aicpu_type',
                'group_condition': 0
            },
            {
                'op_type': 'aicpu_type',
                'group_condition': {'limit': True}
            },
            {
                'op_type': 'aicpu_type',
                'group_condition': {'limit': 0}
            },
            {
                'op_type': 'aicpu_type',
                'group_condition': {'offset': True}
            },
            {
                'op_type': 'aicpu_type',
                'group_condition': {'offset': -1}
            },
            {
                'op_type': 'aicpu_type',
                'group_condition': {'offset': 10000000}
            },
        ]
        exception_message_list = [
            "The group condition must be dict.",
            "The limit must be int.",
            "The limit must in [1, 100].",
            "The offset must be int.",
            "The offset must ge 0.",
            "The offset must le 1000000."
        ]
        exception_message_list = [
            'The group_condition in search_condition error, ' + message
            for message in exception_message_list
        ]
        for idx, condition in enumerate(condition_list):
            with pytest.raises(ProfilerGroupConditionException) as exc_info:
                validate_condition(condition)
            assert exc_info.value.error_code == '50546184'
            assert exc_info.value.message == exception_message_list[idx]
