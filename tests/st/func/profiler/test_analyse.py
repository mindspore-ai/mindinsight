# Copyright 2019 Huawei Technologies Co., Ltd
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
from unittest import mock, TestCase

import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.exceptions.exceptions import StepNumNotSupportedException, \
    ProfilerParamValueErrorException
from mindinsight.profiler.profiling import Profiler, FrameworkParser
from tests.st.func.profiler import RAW_DATA_BASE
from tests.st.func.profiler.conftest import BASE_SUMMARY_DIR


@pytest.mark.usefixtures('create_summary_dir')
class TestProfilerAnalyse(TestCase):
    """Test Converter module."""
    JOB_ID = 'JOB3'

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.step_trace_file = 'step_trace_raw_1_detail_time.csv'
        cls.generate_parsed_files()

    def setUp(self):
        """Setup before each test."""
        self.step_trace_analyser = AnalyserFactory.instance().get_analyser(
            'step_trace', self.profiler, '1')

    @classmethod
    def generate_parsed_files(cls):
        """Test parse raw info about profiler."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')
        FrameworkParser._raw_data_dir = RAW_DATA_BASE
        if not os.path.exists(cls.summary_dir):
            os.makedirs(cls.summary_dir)
        Profiler._base_profiling_container_path = os.path.join(RAW_DATA_BASE, 'container')
        with mock.patch('mindinsight.profiler.profiling.PROFILING_LOG_BASE_PATH', RAW_DATA_BASE):
            profiler = Profiler(subgraph='all', is_detail=True, is_show_op_path=False,
                                output_path=cls.summary_dir, job_id=cls.JOB_ID)
            profiler.analyse()

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_step_trace_file_exist(self):
        """Test the step trace file has been generated"""
        output_files = os.listdir(self.profiler)
        assert self.step_trace_file in output_files

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_step_trace_point_info(self):
        """Test the step trace file has been generated"""
        point_info = self.step_trace_analyser.point_info
        assert point_info == {
            'fp_start': 'Default/Cast-op6',
            'bp_end': 'Default/TransData-op7'
        }

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_graph_api(self):
        """Test step trace restful api."""
        condition = {
            'filter_condition': {
                'mode': 'step',
                'step_id': 0
            }
        }
        analyser = self.step_trace_analyser
        res = analyser.query(condition)
        assert res['size'] == 322
        assert len(res['training_trace_graph']) == 13
        assert res['training_trace_graph'][-1] == [
            {'name': '', 'start': 0.2038, 'duration': 118.1667},
            {'name': 'stream_540_parallel_0', 'start': 118.3705, 'duration': 49.281},
            {'name': '', 'start': 167.6515, 'duration': 37.7294}]

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_graph_api_error(self):
        """Test graph  api without mode."""
        condition = {
            'filter_condition': {
                'step_id': -1
            }}
        self.assertRaisesRegex(
            StepNumNotSupportedException,
            'The step num must be in',
            self.step_trace_analyser.query,
            condition
        )

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_target_info_api(self):
        """Test step trace restful api."""
        condition = {
            'filter_condition': {
                'mode': 'proc',
                'step_id': None
            }
        }
        analyser = AnalyserFactory.instance().get_analyser('step_trace', self.profiler, '1')
        for proc_name in ['iteration_interval', 'fp_and_bp', 'tail']:
            condition['filter_condition']['proc_name'] = proc_name
            res = analyser.query(condition)
            assert res['size'] == 322
            assert len(res['info'][proc_name]) == res['size']

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_summary_for_step_trace(self):
        """Test summary for step trace."""
        analyser = AnalyserFactory.instance().get_analyser('step_trace', self.profiler, '1')
        summary = analyser.summary
        assert summary == {
            'total_time': 205.3809,
            'iteration_interval': 0.2038,
            'iteration_interval_percent': '0.1%',
            'fp_and_bp': 118.054,
            'fp_and_bp_percent': '57.48%',
            'tail': 87.1231,
            'tail_percent': '42.42%',
            'total_steps': 322}

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_target_info_api_error(self):
        """Test graph  api without mode."""
        condition = {
            'filter_condition': {
                'proc_name': 'fake name'
            }}
        self.assertRaisesRegex(
            ProfilerParamValueErrorException,
            'Param value error',
            self.step_trace_analyser.query,
            condition
        )
