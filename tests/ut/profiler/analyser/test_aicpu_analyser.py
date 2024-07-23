# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
    pytest tests/ut/func/profiler
"""
import os

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.ut.profiler import BASE_SUMMARY_DIR


class TestAicpuAnalyser:
    """Test AICPU analyser module."""
    def __init__(self):
        """Member init."""
        self._analyser_aicpu_type = None
        self._analyser_aicpu_detail = None

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')

    def setup_method(self):
        """Create analyser."""
        self._analyser_aicpu_type = AnalyserFactory.instance().get_analyser(
            'aicpu_type', self.profiler, '1')
        self._analyser_aicpu_detail = AnalyserFactory.instance().get_analyser(
            'aicpu_detail', self.profiler, '1')

    def test_query_aicpu_type(self):
        """Test the function of querying AICPU operator type information."""
        expect_result = {
            'col_name': ['kernel_type', 'execution_time', 'execution_frequency', 'percent'],
            'object': [
                ['InitData', 7906.0, 1, 89.84],
            ],
            'size': 1
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'partial_match_str_in': ['init']
                }
            }
        }
        result = self._analyser_aicpu_type.query(condition)
        assert expect_result == result

    def test_query_aicpu_detail(self):
        """Test the function of querying AICPU operator detail information."""
        expect_result = {
            'col_name': ['kernel_name', 'kernel_type', 'total_time',
                         'dispatch_time', 'execution_frequency'],
            'size': 1
        }

        condition = {
            'filter_condition': {
                'kernel_type': {
                    'partial_match_str_in': ['get']
                }
            }
        }
        result = self._analyser_aicpu_detail.query(condition)
        del result["object"]
        assert expect_result == result
