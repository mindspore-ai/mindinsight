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
         'MFLOPs(10^6 cube)', 'GFLOPS(10^9 cube)', 'MFLOPs(10^6 vector)', 'GFLOPS(10^9 vector)', 'full_op_name',
         'op_info'],
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
                ['op_type', 'total_time', 'execution_frequency', 'total_percent', 'avg_time'],
            'object': [['MatMul', 2807.82, 25, 5760.0, 112.313],
                       ['Cast', 104.32, 27, 214.0, 3.864],
                       ['TransData', 86.12, 9, 177.0, 9.569],
                       ['ApplyMomentumD', 56.68, 24, 116.0, 2.362],
                       ['MaxPoolGradWithArgmax', 51.6, 6, 106.0, 8.6],
                       ['AtomicAddrClean', 48.99, 30, 101.0, 1.633],
                       ['Conv2DBackpropFilterD', 45.68, 6, 94.0, 7.613],
                       ['Conv2D', 38.97, 6, 80.0, 6.495],
                       ['MaxPoolWithArgmax', 34.32, 6, 70.0, 5.72],
                       ['FusionOp_ReluGradV2_Cast', 32.87, 6, 67.0, 5.478],
                       ['SoftmaxCrossEntropyWithLogits', 28.7, 3, 59.0, 9.567],
                       ['BiasAddGrad', 26.73, 9, 55.0, 2.97],
                       ['ReluV2', 25.99, 6, 53.0, 4.332],
                       ['Conv2DBackpropInputD', 16.07, 3, 33.0, 5.357],
                       ['OneHotD', 15.89, 3, 33.0, 5.297],
                       ['ReluGrad', 11.54, 6, 24.0, 1.923],
                       ['Relu', 9.67, 6, 20.0, 1.612],
                       ['AssignAdd', 9.22, 6, 19.0, 1.537],
                       ['TensorMove', 5.31, 3, 11.0, 1.77],
                       ['Mul', 4.29, 3, 9.0, 1.43],
                       ['ReduceMeanD', 4.24, 3, 9.0, 1.413],
                       ['GetNext', 0.15, 3, 0.0, 0.05],
                       ['StreamRecv', 0.15, 3, 0.0, 0.05],
                       ['StreamSend', 0.03, 3, 0.0, 0.01]],
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
                ['op_type', 'total_time', 'execution_frequency', 'total_percent', 'avg_time'],
            'object': [
                ['MatMul', 2807.82, 25, 5760.0, 112.313],
                ['Mul', 4.29, 3, 9.0, 1.43]
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
