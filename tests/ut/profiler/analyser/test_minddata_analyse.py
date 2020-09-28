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
    pytest tests/ut/profiler
"""
import os

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory

from tests.ut.profiler import BASE_SUMMARY_DIR


class TestMinddataAnalyser:
    """Test minddata  analyser module."""

    @classmethod
    def setup_class(cls):
        """Initialization before test case execution."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, "normal_run")
        cls.profiler = os.path.join(cls.summary_dir, "profiler")

    def setup_method(self):
        """Setup before each test."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'minddata', self.profiler, '1')

    def test_analyse_get_next_info_all(self):
        """Test analysing the get_next operation info for info_type="queue" """
        expect_queue_result = {
            "info": {"queue": [3, 2, 1]},
            "size": 3,
            "summary": {"queue_summary": {"empty_queue": 0}}
        }

        expect_time_result = {
            "info": {"get_next": [0.001, 0, 0.001]},
            "size": 3,
            "summary": {"time_summary": {"avg_cost": "0.0006666666666666666"}}
        }

        queue_result, time_result = self._analyser.analyse_get_next_info(info_type="all")
        assert expect_queue_result == queue_result
        assert expect_time_result == time_result

    def test_analyse_device_queue_info_all(self):
        """Test analysing the device_queue operation info for info_type="queue" """
        expect_queue_result = {
            "info": {"queue": [0]},
            "size": 1,
            "summary": {"queue_summary": {"empty_queue": 1, "full_queue": 0}}
        }

        expect_time_result = {
            "info": {"total_cost": [4], "push_cost": [4], "get_cost": [0]},
            "size": 1,
            "summary": {"time_summary": {"avg_cost": 4, "get_cost": 0, "push_cost": 4}}
        }

        queue_result, time_result = self._analyser.analyse_device_queue_info(info_type="all")
        assert expect_queue_result == queue_result
        assert expect_time_result == time_result
