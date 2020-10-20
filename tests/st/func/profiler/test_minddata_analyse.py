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
Fuction:
    Test profiler to watch the performance of training.
Usage:
    pytest tests/st/func/profiler
"""
import os
import pytest

from mindinsight.profiler.analyser.minddata_analyser import MinddataAnalyser
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory

from .conftest import BASE_SUMMARY_DIR_RUN_2


class TestMinddataAnalyser:
    """Test minddata  analyser module."""

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR_RUN_2, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')

    def setup_method(self):
        """Create analyser."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'minddata', self.profiler, '1')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_analyse_queue_summary(self):
        """Test analysing the queue summary info."""
        expect_result = {
            "data_process": {"status": "normal"},
            "device_queue_info": {"summary": {"empty_batch_count": 1, "full_batch_count": 0, "total_batch": 1}},
            "device_queue_op": {"status": "normal"},
            "get_next": {"status": "normal"},
            "get_next_queue_info": {"summary": {"empty_batch_count": 0, "total_batch": 3}},
            "data_transmission": {"status": "normal"}
        }

        get_next_queue_info, _ = self._analyser.analyse_get_next_info(info_type="queue")
        device_queue_info, _ = self._analyser.analyse_device_queue_info(info_type="queue")
        result = MinddataAnalyser.analyse_queue_summary(get_next_queue_info, device_queue_info)
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_analyse_get_next_info(self):
        """Test analysing the get_next operation info for info_type="time" """
        expect_result = {
            "info": {"get_next": [0.001, 0, 0.001]},
            "size": 3,
            "summary": {"time_summary": {"avg_cost": "0.0006666666666666666"}}
        }

        time_info = {
            "size": 0,
            "info": [],
            "summary": {"time_summary": {}},
            "advise": {}
        }

        _, time_info = self._analyser.analyse_get_next_info(info_type="time")
        assert expect_result == time_info

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_analyse_device_queue_info(self):
        """Test analysing the device_queue operation info for info_type="time" """
        expect_result = {
            "info": {"total_cost": [4], "push_cost": [4], "get_cost": [0]},
            "size": 1,
            "summary": {"time_summary": {"avg_cost": 4, "get_cost": 0, "push_cost": 4}}
        }

        time_info = {
            "size": 0,
            "info": [],
            "summary": {"time_summary": {}},
            "advise": {}
        }

        _, time_info = self._analyser.analyse_device_queue_info(info_type="time")
        assert expect_result == time_info
