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
from unittest import mock

import pytest

from mindinsight.profiler import Profiler
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.parser.framework_parser import FrameworkParser
from tests.st.func.profiler.conftest import BASE_SUMMARY_DIR
from tests.ut.profiler import RAW_DATA_BASE


OP_GATHER_V2_INFO = {
    'col_name': [
        'op_name', 'op_type', 'avg_execution_time (ms)', 'subgraph', 'full_op_name',
        'op_info'
    ],
    'object': [
        [
            'GatherV2-op55', 'GatherV2', 42.220212142857136, 'Default',
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
            'GatherV2-op33', 'GatherV2', 0.9352293333333332, 'Default',
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


@pytest.mark.usefixtures('create_summary_dir')
class TestOpAnalyser:
    """Test AICORE and AICPU analyser module."""
    JOB_ID = 'JOB3'

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.generate_parsed_files()

    def setup_method(self):
        """Create analyser."""
        self._analyser_aicore_type = AnalyserFactory.instance().get_analyser(
            'aicore_type', self.profiler, '1')
        self._analyser_aicore_detail = AnalyserFactory.instance().get_analyser(
            'aicore_detail', self.profiler, '1')

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
    def test_query_aicore_type_1(self):
        """Test the function of querying AICORE operator type infomation."""
        expect_result = {
            'col_name': ['op_type', 'execution_time (ms)', 'execution_frequency', 'percent'],
            'object': [
                ['UnsortedSegmentSum', 44.607826, 2, 35.28],
                ['GatherV2', 43.155441, 2, 34.13],
                ['Slice', 20.376315, 16, 16.12],
                ['Concat', 5.808454, 4, 4.59],
                ['Split', 2.714277, 2, 2.15],
                ['MatMul', 1.936681, 15, 1.53],
                ['Mul', 1.902949, 32, 1.51],
                ['StridedSliceGrad', 1.506834, 2, 1.19],
                ['TransData', 1.115158, 30, 0.88],
                ['ReluGrad', 0.854069, 5, 0.68],
                ['Cast', 0.484685, 15, 0.38],
                ['ReLU', 0.483282, 5, 0.38],
                ['RealDiv', 0.422807, 15, 0.33],
                ['StridedSlice', 0.345569, 2, 0.27],
                ['Adam', 0.285936, 11, 0.23],
                ['BiasAdd', 0.189663, 5, 0.15],
                ['BiasAddGrad', 0.071681, 5, 0.06],
                ['Tile', 0.044158, 4, 0.03],
                ['ReduceSum', 0.030765, 5, 0.02],
                ['ApplyFtrl', 0.025454, 2, 0.02],
                ['AtomicAddrClean', 0.019369, 8, 0.02],
                ['AddN', 0.012836, 1, 0.01],
                ['Square', 0.009799, 1, 0.01],
                ['SigmoidCrossEntropyWithLogitsGrad', 0.009582, 2, 0.01],
                ['TensorAdd', 0.009218, 3, 0.01],
                ['SigmoidCrossEntropyWithLogits', 0.004809, 1, 0.0],
                ['ReduceMean', 0.004535, 1, 0.0],
                ['Assign', 0.002477, 2, 0.0],
                ['AssignAdd', 0.001688, 1, 0.0]
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
        """Test the function of querying AICORE operator type infomation."""
        expect_result = {
            'col_name': ['op_type', 'execution_time (ms)', 'execution_frequency', 'percent'],
            'object': [
                ['MatMul', 1.936681, 15, 1.53],
                ['Mul', 1.902949, 32, 1.51]
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
        """Test the function of querying AICORE operator detail infomation."""
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
