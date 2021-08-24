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
    Test profiler to watch the performance of training.
Usage:
    pytest tests/st/func/profiler
"""
import os
import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler import PROFILER_DIR
from tests.utils.tools import compare_result_with_file


class TestTimelineAnalyser:
    """Test flops analyser module."""
    def setup_method(self):
        """Create analyser."""
        self.profiler = PROFILER_DIR
        self.device_id = 0
        self._analyser = AnalyserFactory.instance().get_analyser(
            'flops', self.profiler, self.device_id)

    @pytest.mark.parametrize(
        "filename",
        ['flops_summary_{}.json']
    )
    def test_get_flops_summary(self, filename):
        """Test the function of get flops summary data for UI display."""
        file_path = os.path.join(
            self.profiler,
            filename.format(self.device_id)
        )

        result = self._analyser.get_flops_summary()
        compare_result_with_file(result, file_path)

    @pytest.mark.parametrize(
        "filename",
        ['flops_scope_{}.json']
    )
    def test_get_flops_scope(self, filename):
        """Test the function of get scope-level flops data for UI display."""
        file_path = os.path.join(
            self.profiler,
            filename.format(self.device_id)
        )

        result = self._analyser.get_flops_scope()
        compare_result_with_file(result, file_path)
