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

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from . import PROFILER_DIR
from ....utils.tools import compare_result_with_file

class TestTimelineAnalyser:
    """Test timeline analyser module."""

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.profiler = PROFILER_DIR
        cls.device_id = 0
        cls.ascend_display_filename = 'ascend_timeline_display_{}.json'
        cls.gpu_display_filename = 'gpu_timeline_display_{}.json'
        cls.ascend_timeline_summary_filename = 'ascend_timeline_summary_{}.json'
        cls.gpu_timeline_summary_filename = 'gpu_timeline_summary_{}.json'

    def setup_method(self):
        """Create analyser."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'timeline', self.profiler, self.device_id)


    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_display_timeline(self):
        """Test the function of get timeline data for UI display."""
        gpu_file_path = os.path.join(
            self.profiler,
            self.gpu_display_filename.format(self.device_id)
        )
        ascend_file_path = os.path.join(
            self.profiler,
            self.ascend_display_filename.format(self.device_id)
        )

        result = self._analyser.get_display_timeline("gpu")
        compare_result_with_file(result, gpu_file_path)

        result = self._analyser.get_display_timeline("ascend")
        compare_result_with_file(result, ascend_file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_timeline_summary(self):
        """Test the function of get timeline data for UI display."""
        gpu_file_path = os.path.join(
            self.profiler,
            self.gpu_timeline_summary_filename.format(self.device_id)
        )
        ascend_file_path = os.path.join(
            self.profiler,
            self.ascend_timeline_summary_filename.format(self.device_id)
        )

        result = self._analyser.get_timeline_summary("gpu")
        compare_result_with_file(result, gpu_file_path)

        result = self._analyser.get_timeline_summary("ascend")
        compare_result_with_file(result, ascend_file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_timeline_summary_file_not_exist(self):
        """Test the function of get timeline data for UI display."""
        device_id = 1
        analyser = AnalyserFactory.instance().get_analyser(
            'timeline', self.profiler, device_id)
        analyser.get_timeline_summary("gpu")

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_timeline_display_file_not_exist(self):
        """Test the function of get timeline data for UI display."""
        device_id = 1
        analyser = AnalyserFactory.instance().get_analyser(
            'timeline', self.profiler, device_id)
        analyser.get_display_timeline("gpu")
