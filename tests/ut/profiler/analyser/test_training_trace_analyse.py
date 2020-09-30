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
import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.exceptions.exceptions import StepNumNotSupportedException
from tests.ut.profiler import BASE_SUMMARY_DIR


class TestTrainingTraceAnalyser:
    """Test trainning_trace analyser module."""

    @classmethod
    def setup_class(cls):
        """Initialization before test case execution."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, "normal_run")
        cls.profiler = os.path.join(cls.summary_dir, "profiler")

    def setup_method(self):
        """Setup before each test."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'step_trace', self.profiler, '1')

    def test_analyse_get_training_trace_graph(self):
        """Test analysing the get_training_trace_graph info """
        expect_result = {
            "size": 1,
            "point_info": {"fp_start": "Default/EndOfSequence-op131",
                           "bp_end": "Default/AssignAdd-op138"
                           },

            "summary": {"fp_and_bp": 0.0,
                        "fp_and_bp_percent": "0%",
                        "iteration_interval": 0.0,
                        "iteration_interval_percent": "0%",
                        "tail": 0.0,
                        "tail_percent": "0%",
                        "total_steps": 1,
                        "total_time": 0.0,
                        }
        }

        result = self._analyser.query({
            'filter_condition': {
                'mode': 'step',
                'step_id': 0
            }})
        result['summary'] = self._analyser.summary
        result['point_info'] = self._analyser.point_info
        del result["training_trace_graph"]
        assert expect_result == result

    def test_analyse_get_training_trace_time_info(self):
        """Test analysing the get_training_trace_time info """
        expect_result = {
            "size": 1,
            "info": {"fp_and_bp": [23.6681]}
        }
        proc_name = 'fp_and_bp'
        result = self._analyser.query({
            'filter_condition': {
                'mode': 'proc',
                'proc_name': proc_name
            }})
        assert expect_result == result

    def test_analyse_get_training_trace_graph_with_wrong_id(self):
        with pytest.raises(StepNumNotSupportedException) as exc:
            self._analyser.query({
                'filter_condition': {
                    'mode': 'step',
                    'step_id': 10
                }})
        assert exc.value.message == 'The step num must be in [0, 1]'
