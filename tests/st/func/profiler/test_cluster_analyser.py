# Copyright 2021 Huawei Technologies Co., Ltd
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
    Test cluster profiler to watch the performance of training.
Usage:
    pytest tests/st/func/profiler
"""
import os
import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler.conftest import BASE_SUMMARY_DIR_RUN_2


class TestClusterAnalyser:
    """Test cluster analyser module."""
    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR_RUN_2, 'normal_run')

    def setup_method(self):
        """Create analyser."""
        self._analyser_cluster_step_trace = AnalyserFactory.instance().get_analyser(
            'cluster_step_trace', self.summary_dir, '1')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_query_cluster_step_trace(self):
        """Test the function of querying cluster step trace information."""
        condition = {
            'filter_condition': {
                'step_id': 1
            }
        }
        expect_result = {
            "total_step_num": '1',
            "step_trace": [{"step_trace_info": [0.0, 23.66808, 0.04097],
                            "rank_id": 1,
                            "profiler_dir": "profiler"
                            }],
            "size": 1

        }
        result = self._analyser_cluster_step_trace.query(condition)
        assert expect_result == result
