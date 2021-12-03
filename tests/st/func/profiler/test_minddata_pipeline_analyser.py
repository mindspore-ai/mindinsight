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
Function:
    Test profiler to watch the performance of training.
Usage:
    pytest tests/st/func/profiler
"""
import os

import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler.conftest import BASE_SUMMARY_DIR


class TestMinddataPipelineAnalyser:
    """Test minddata pipeline analyser module."""
    JOB_ID = 'JOB3'

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')

    def setup_method(self):
        """Create analyser."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', self.profiler, '1')


    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_query(self):
        """Test the function of querying minddata pipeline information."""
        expect_result = {
            'col_name': [
                'op_id', 'op_type', 'output_queue_average_size', 'output_queue_length',
                'output_queue_usage_rate', 'sample_interval', 'parent_id', 'children_id'
            ],
            'object': [
                [1, 'Shuffle', 20.0, 64, 0.3125, 10, 0, [2, 3]],
                [2, 'TFReader', 20.0, 64, 0.3125, 10, 1, None],
                [3, 'TFReader', 20.0, 64, 0.3125, 10, 1, None],
                [0, 'Batch', None, None, 0, 10, None, [1]]
            ],
            'size': 4
        }
        condition = {
            'sort_condition': {
                'name': 'output_queue_average_size',
                'type': 'descending'
            }
        }
        result = self._analyser.query(condition)
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_op_and_parent_op_info(self):
        """Test the function of the target operator and queue information."""
        expect_result = {
            'current_op': {
                'op_id': 1,
                'op_type': 'Shuffle',
                'num_workers': 1
            },
            'parent_op': {
                'op_id': 0,
                'op_type': 'Batch',
                'num_workers': 4
            },
            'queue_info': {
                'output_queue_size': [10, 20, 30],
                'output_queue_average_size': 20.0,
                'output_queue_length': 64,
                'output_queue_usage_rate': 0.3125,
                'sample_interval': 10
            }
        }
        result = self._analyser.get_op_and_parent_op_info(1)
        assert expect_result == result
