# Copyright 2022 Huawei Technologies Co., Ltd
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
"""Test the analyser module."""
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.ut.profiler import PROFILER_DIR

OPERATOR_COL_NAMES = ["step", "op_side", "op_type", "op_name", "duration", "op_shape"]
CUDA_COL_NAMES = ["step", "op_type", "op_name", "op_full_name", "duration", "block_dim", "grid_dim"]


class TestGpuOpTypeInfoAnalyser:
    """Test the class of `GpuOpTypeInfoAnalyser`."""
    def __init__(self):
        """Initialization before test case execution."""
        self._analyser = None

    def test_query_success_1(self):
        """Test the success of the querying function."""
        op_info = "gpu_op_type_info"
        self._analyser = AnalyserFactory.instance().get_analyser(
            op_info, PROFILER_DIR, '0'
        )
        expect_result = {
            "col_name": OPERATOR_COL_NAMES,
            "object": [[1, "gpu", "Add", "Add-op6", 75.616, ["[32, 1]", "[32, 1]"]]],
            "size": 1,
            "all_type": ["InitDataSetQueue", "GetNext", "Add"],
            "filter_type": {"GetNext": [153.52, 80.224, 50.752, 72.768, 59.936, 81.344, 67.232, 52.064, 0]}
        }
        condition = {"op_type": "gpu_op_type_info",
                     "device_id": "0",
                     "filter_condition":
                         {
                             "op_type": {"partial_match_str_in": ["Add"]},
                             "dispaly_op_type": ["GetNext"],
                             "step_filter": ["1"],
                         },
                     "sort_condition": {"name": "duration", "type": "descending"},
                     "group_condition": {"offset": 0, "limit": 5}
                     }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_2(self):
        """Test the success of the querying function."""
        op_info = "gpu_cuda_type_info"
        self._analyser = AnalyserFactory.instance().get_analyser(
            op_info, PROFILER_DIR, '0'
        )
        expect_result = {"col_name": CUDA_COL_NAMES,
                         "object":
                             [[1, "cuLaunchKernel",
                               "ElewiseArithKernel<float, AddFunc<float> >(int, float const*, float const*, float*)",
                               "Default/network-Net/Add-op6", 3.904, "256,1,1", "1,1,1"]
                              ],
                         "size": 1,
                         "all_type": [
                             "ElewiseArithKernel<float, AddFunc<float> >(int, float const*, float const*, float*)"],
                         "filter_type": {
                             "ElewiseArithKernel<float, AddFunc<float> >(int, float const*, float const*, float*)":
                                 [3.904, 3.232, 3.04, 3.04, 3.072, 3.072, 3.232, 3.04, 3.072]}
                         }

        condition = {"op_type": "gpu_cuda_type_info",
                     "device_id": "0",
                     "filter_condition":
                         {
                             "step_filter": ["1"],
                         },
                     "sort_condition": {"name": "duration", "type": "descending"},
                     "group_condition": {"offset": 0, "limit": 5}
                     }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)
