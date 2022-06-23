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
    'col_name': [
        'op_name', 'op_type', 'avg_execution_time', 'FLOPs', 'FLOPS', 'FLOPS_Utilization',
        'subgraph', 'full_op_name', 'op_info'
    ],
    'object': [
        [
            'GatherV2-op55', 'GatherV2', 42220.212, 333.0, 333.0, 33.0, 'Default',
            'Default/network-TrainStepWrap/network-VirtualDatasetCellTriple/'
            '_backbone-NetWithLossClass/network-WideDeepModel/GatherV2-op55',
            {
                'input_0': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_FLOAT32',
                    'shape': '184696,8'
                },
                'input_1': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_INT32',
                    'shape': '128000,39'
                },
                'output_0': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_FLOAT32',
                    'shape': '128000,39,8'
                }
            }
        ],
        [
            'GatherV2-op33', 'GatherV2', 935.229, 333.0, 333.0, 33.0, 'Default',
            'Default/network-TrainStepWrap/network-VirtualDatasetCellTriple/'
            '_backbone-NetWithLossClass/network-WideDeepModel/GatherV2-op33',
            {
                'input_0': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_FLOAT32',
                    'shape': '184696,1'
                },
                'input_1': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_INT32',
                    'shape': '16000,39'
                },
                'output_0': {
                    'format': 'DefaultFormat',
                    'data_type': 'NUMBER_TYPE_FLOAT32',
                    'shape': '16000,39,1'
                }
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
            'col_name': ['op_type', 'execution_time', 'execution_frequency', 'percent'],
            'object': [
                ['UnsortedSegmentSum', 44607.826, 2, 35.28],
                ['GatherV2', 43155.441, 2, 34.13],
                ['Slice', 20376.315, 16, 16.12],
                ['Concat', 5808.454, 4, 4.59],
                ['Split', 2714.277, 2, 2.15],
                ['MatMul', 1936.681, 15, 1.53],
                ['Mul', 1902.949, 32, 1.51],
                ['StridedSliceGrad', 1506.834, 2, 1.19],
                ['TransData', 1115.158, 30, 0.88],
                ['ReluGrad', 854.069, 5, 0.68],
                ['Cast', 484.685, 15, 0.38],
                ['ReLU', 483.282, 5, 0.38],
                ['RealDiv', 422.807, 15, 0.33],
                ['StridedSlice', 345.569, 2, 0.27],
                ['Adam', 285.936, 11, 0.23],
                ['BiasAdd', 189.663, 5, 0.15],
                ['BiasAddGrad', 71.681, 5, 0.06],
                ['Tile', 44.158, 4, 0.03],
                ['ReduceSum', 30.765, 5, 0.02],
                ['ApplyFtrl', 25.454, 2, 0.02],
                ['AtomicAddrClean', 19.369, 8, 0.02],
                ['AddN', 12.836, 1, 0.01],
                ['Square', 9.799, 1, 0.01],
                ['SigmoidCrossEntropyWithLogitsGrad', 9.582, 2, 0.01],
                ['TensorAdd', 9.218, 3, 0.01],
                ['SigmoidCrossEntropyWithLogits', 4.809, 1, 0.0],
                ['ReduceMean', 4.535, 1, 0.0],
                ['Assign', 2.477, 2, 0.0],
                ['AssignAdd', 1.688, 1, 0.0]
            ],
            'size': 29
        }
        condition = {
            'sort_condition': {
                'name': 'execution_time',
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
            'col_name': ['op_type', 'execution_time', 'execution_frequency', 'percent'],
            'object': [
                ['MatMul', 1936.681, 15, 1.53],
                ['Mul', 1902.949, 32, 1.51]
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
                'name': 'execution_time',
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
                    'in': ['GatherV2']
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
