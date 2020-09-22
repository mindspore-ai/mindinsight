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
"""Test the validator module."""
import pytest

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerParamTypeErrorException, ProfilerGroupConditionException, \
    ProfilerFilterConditionException, ProfilerOpTypeException
from mindinsight.profiler.common.validator.validate import \
    validate_minddata_pipeline_condition, validate_condition, validate_and_set_job_id_env


class TestValidate:
    """Test the function of validate."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
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

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_validate_condition_exception(self):
        """Test the exception of validate condition."""
        condition = "not a dict"
        exception_message = 'Param type error. Invalid search_condition type, it should be dict.'
        with pytest.raises(ProfilerParamTypeErrorException) as exc_info:
            validate_condition(condition)
        assert exc_info.value.error_code == '50546082'
        assert exc_info.value.message == exception_message

        # test the ProfilerOpTypeException
        condition_list = [{'op_type': "xxx"}, {}]
        exception_message = "The op_type in search_condition error, The op_type must in " \
                            "['aicpu_type','aicpu_detail', 'aicore_type', 'aicore_detail', "\
                            "'gpu_op_type', 'gpu_op_info', 'gpu_cuda_activity']"
        for condition in condition_list:
            with pytest.raises(ProfilerOpTypeException) as exc_info:
                validate_condition(condition)
            assert exc_info.value.error_code == '50546183'
            assert exc_info.value.message == exception_message

        # test the ProfilerGroupConditionException
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

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_validate_minddata_pipeline_condition(self):
        """Test the validate minddata pipeline condition of normal input."""
        filter_condition_list = [
            {
                'op_id': {
                    'in': [1, 2]
                }
            },
            {
                'op_type': {
                    'in': ['add', 'conv2d']
                }
            },
            {
                'is_display_op_detail': True
            }
        ]
        for filter_condition in filter_condition_list:
            condition = {
                'device_id': '0',
                'op_type': 'aicpu_type',
                'filter_condition': filter_condition,
                'group_condition': {
                    'limit': 1,
                    'offset': 1
                },
                'sort_condition': {
                    'name': 'op_type',
                    'type': 'ascending'
                }
            }
            validate_minddata_pipeline_condition(condition)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_validate_minddata_pipeline_condition_exception(self):
        """Test the exception of validate minddata pipeline condition."""
        condition_list = [
            {
                'filter_condition': {
                    'op_id': 0
                }
            },
            {
                'filter_condition': {
                    'op_id': {
                        'in': ['0']
                    }
                }
            }
        ]
        exception_message_list = [
            'The filter_condition in search_condition error, '
            'The filter condition value must be dict.',
            'The filter_condition in search_condition error, '
            'The item in filter value must be int.'
        ]

        for idx, condition in enumerate(condition_list):
            with pytest.raises(ProfilerFilterConditionException) as exc_info:
                validate_minddata_pipeline_condition(condition)
            assert exc_info.value.error_code == '50546186'
            assert exc_info.value.message == exception_message_list[idx]

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_validate_and_set_job_id_env(self):
        """Test the validate and set job id env."""
        job_id = '256'
        validate_and_set_job_id_env(job_id)
