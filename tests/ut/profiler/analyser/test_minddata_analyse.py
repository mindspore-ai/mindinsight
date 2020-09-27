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
from unittest import TestCase

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory

from ...profiler import BASE_SUMMARY_DIR


class TestMinddataAnalyser(TestCase):
    """Test minddata  analyser module."""

    def setUp(self) -> None:
        """Initialization before test case execution."""
        self.summary_dir = os.path.join(BASE_SUMMARY_DIR, "normal_run")
        self.profiler = os.path.join(self.summary_dir, "profiler")
        self._analyser = AnalyserFactory.instance().get_analyser(
            'minddata', self.profiler, '1')

    def test_analyse_get_next_info_queue(self):
        """Test analysing the get_next operation info for info_type="queue" """
        expect_result = {
            "info": {"queue": [3, 2, 1]},
            "size": 3,
            "summary": {"queue_summary": {"empty_queue": 0}}
        }
        result, _ = self._analyser.analyse_get_next_info(info_type="queue")
        self.assertDictEqual(expect_result, result)

    def test_analyse_device_queue_info_queue(self):
        """Test analysing the device_queue operation info for info_type="queue" """
        expect_result = {
            "info": {"queue": [0]},
            "size": 1,
            "summary": {"queue_summary": {"empty_queue": 1, "full_queue": 0}}
        }
        result, _ = self._analyser.analyse_device_queue_info(info_type="queue")
        self.assertDictEqual(expect_result, result)
