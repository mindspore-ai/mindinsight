# Copyright 2023 Huawei Technologies Co., Ltd
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

import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler import PROFILER_DIR


class TestTimelineAnalyser:
    """Test timeline analyser module."""

    def __init__(self):
        self._analyser = None

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.profiler = PROFILER_DIR

    def setup_method(self):
        """Create analyser."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'msprof_timeline', self.profiler, None)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_timeline_option(self):
        """Test the function of get timeline option data for UI display."""

        result = self._analyser.get_option()
        for k, v in result.items():
            result[k] = sorted(v)
        assert result == {'rank_list': [0, 1], 'model_list': [0, 2]}

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_summary_timeline(self):
        """Test the function of get summary timeline data for UI display."""

        result = self._analyser.get_merged_timeline(None, None, 'summary', True)
        process_names = []
        thread_names = []
        for res in result:
            name = res.get('name')
            if res.get('ph') == 'M' and name == 'process_name':
                process_names.append(res.get('args').get('name'))
            elif res.get('ph') == 'M' and name == 'thread_name':
                thread_names.append(res.get('args').get('name'))
        process_names.sort()
        thread_names.sort()
        assert process_names == ['Overlap Analysis rank0', 'Overlap Analysis rank1',
                                 'Step Trace rank0', 'Step Trace rank1']
        assert thread_names == ['Communication', 'Communication', 'Communication(Not OverLapped)',
                                'Communication(Not OverLapped)', 'Computing', 'Computing', 'Free', 'Free',
                                'iterations', 'iterations']

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_detail_timeline(self):
        """Test the function of get detail timeline data for UI display."""

        result = self._analyser.get_merged_timeline(None, None, 'detail', True)
        process_names = []
        thread_names = []
        for res in result:
            name = res.get('name')
            if res.get('ph') == 'M' and name == 'process_name':
                process_names.append(res.get('args').get('name'))
            elif res.get('ph') == 'M' and name == 'thread_name':
                thread_names.append(res.get('args').get('name'))
        process_names.sort()
        thread_names.sort()
        assert process_names == ['Ascend Hardware rank0', 'Ascend Hardware rank1', 'HCCL rank0', 'HCCL rank1',
                                 'Overlap Analysis rank0', 'Overlap Analysis rank1',
                                 'Step Trace rank0', 'Step Trace rank1']
        assert thread_names == ['Communication', 'Communication', 'Communication Kernel', 'Communication Kernel',
                                'Communication(Not OverLapped)', 'Communication(Not OverLapped)', 'Computing',
                                'Computing', 'Free', 'Free', 'Plane 0', 'Plane 0', 'Plane 1', 'Plane 1',
                                'Plane 2', 'Plane 2', 'Plane 3', 'Plane 3', 'Stream 1', 'Stream 10', 'Stream 10',
                                'Stream 12', 'Stream 12', 'Stream 13', 'Stream 2', 'Stream 3', 'Stream 4', 'Stream 4',
                                'Stream 8', 'Stream 9', 'iterations', 'iterations']
