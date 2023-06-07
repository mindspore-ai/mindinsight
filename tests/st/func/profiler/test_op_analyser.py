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
    pytest tests/st/func/profiler
"""
import os

import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler.conftest import BASE_SUMMARY_DIR

OP_GATHER_V2_INFO = {
    'col_name':
        ['op_name', 'op_type', 'avg_execution_time', 'execution_frequency',
         'FLOPs(cube)', 'FLOPS(cube)', 'FLOPs(vec)', 'FLOPS(vec)', 'full_op_name', 'op_info'],
    'object': [
        [
            'AssignAdd-op203', 'AssignAdd', 1.79, 3, '-', '-', '-', '-', 'Default/AssignAdd-op203',
            {'input_0': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]},
             'input_1': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]},
             'output_0': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]}
             }
        ],
        [
            'AssignAdd-op206', 'AssignAdd', 1.283, 3, '-', '-', '-', '-', 'Default/AssignAdd-op206',
            {'input_0': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]},
             'input_1': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]},
             'output_0': {'format': 'DEFAULT', 'data_type': 'INT32', 'shape': [1]}
             }
        ]
    ],
    'size': 2
}


class TestOpAnalyser:
    """Test AICORE and AICPU analyser module."""
    JOB_ID = 'JOB3'

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')

    def setup_method(self):
        """Create analyser."""
        self._analyser_aicore_type = AnalyserFactory.instance().get_analyser(
            'aicore_type', self.profiler, '1')
        self._analyser_aicore_detail = AnalyserFactory.instance().get_analyser(
            'aicore_detail', self.profiler, '1')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_query_aicore_type_1(self):
        """Test the function of querying AICORE operator type information."""
        expect_result = {
            'col_name':
                ['op_type', 'total_time', 'execution_frequency', 'percent'],
            'object': [
                ['MatMul', 2807.82, 25, 81.03],
                ['Cast', 104.32, 27, 3.01],
                ['TransData', 86.12, 9, 2.49],
                ['ApplyMomentumD', 56.68, 24, 1.64],
                ['MaxPoolGradWithArgmax', 51.6, 6, 1.49],
                ['AtomicAddrClean', 48.99, 30, 1.41],
                ['Conv2DBackpropFilterD', 45.68, 6, 1.32],
                ['Conv2D', 38.97, 6, 1.12],
                ['MaxPoolWithArgmax', 34.32, 6, 0.99],
                ['FusionOp_ReluGradV2_Cast', 32.87, 6, 0.95],
                ['SoftmaxCrossEntropyWithLogits', 28.7, 3, 0.83],
                ['BiasAddGrad', 26.73, 9, 0.77],
                ['ReluV2', 25.99, 6, 0.75],
                ['Conv2DBackpropInputD', 16.07, 3, 0.46],
                ['OneHotD', 15.89, 3, 0.46],
                ['ReluGrad', 11.54, 6, 0.33],
                ['Relu', 9.67, 6, 0.28],
                ['AssignAdd', 9.22, 6, 0.27],
                ['TensorMove', 5.31, 3, 0.15],
                ['Mul', 4.29, 3, 0.12],
                ['ReduceMeanD', 4.24, 3, 0.12],
                ['GetNext', 0.15, 3, 0.0],
                ['StreamRecv', 0.15, 3, 0.0],
                ['StreamSend', 0.03, 3, 0.0]],
            'size': 24
        }
        condition = {
            'sort_condition': {
                'name': 'total_time',
                'type': 'descending'
            }
        }
        result = self._analyser_aicore_type.query(condition)
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_query_aicore_type_2(self):
        """Test the function of querying AICORE operator type information."""
        expect_result = {
            'col_name':
                ['op_type', 'total_time', 'execution_frequency', 'percent'],
            'object': [
                ['MatMul', 2807.82, 25, 81.03],
                ['Mul', 4.29, 3, 0.12]
            ],
            'size': 2
        }
        condition = {
            'filter_condition': {
                'op_type': {
                    'partial_match_str_in': ['Mul']
                }
            },
            'sort_condition': {
                'name': 'total_time',
                'type': 'descending'
            }
        }
        result = self._analyser_aicore_type.query(condition)
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_query_aicore_detail_1(self):
        """Test the function of querying AICORE operator detail information."""
        expect_result = OP_GATHER_V2_INFO
        condition = {
            'filter_condition': {
                'op_type': {
                    'in': ['AssignAdd']
                }
            },
            'sort_condition': {
                'name': 'avg_execution_time',
                'type': 'descending'
            },
            'group_condition': {
                'limit': 10,
                'offset': 0
            }
        }
        result = self._analyser_aicore_detail.query(condition)
        assert expect_result == result
