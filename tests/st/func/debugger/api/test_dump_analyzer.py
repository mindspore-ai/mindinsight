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
    Test query dump analyzer.
Usage:
    pytest tests/st/func/debugger
"""

import os
import shutil
import tempfile
from unittest import mock

import pytest

from mindinsight.debugger import DumpAnalyzer, Watchpoint, TensorTooLargeCondition, TensorTooSmallCondition, \
    TensorUnchangedCondition, TensorRangeCondition, TensorOverflowCondition, OperatorOverflowCondition, \
    TensorAllZeroCondition, TensorChangeBelowThresholdCondition, TensorChangeAboveThresholdCondition
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager
from tests.st.func.debugger.utils import build_multi_net_dump_structure
from tests.st.func.debugger.debugger_services import mock_dbg_services


class TestDumpAnalyzer:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.debugger_tmp_dir = build_multi_net_dump_structure(create_statistic=True)
        with mock.patch.object(DebuggerOfflineManager, 'get_dbg_service_module', return_value=mock_dbg_services):
            cls.dump_analyzer = DumpAnalyzer(cls.debugger_tmp_dir)

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_select_nodes(self):
        """Get debugger online server"""
        nodes = self.dump_analyzer.select_nodes('conv')
        assert len(nodes) == 128

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_select_tensors(self):
        """Get debugger online server"""
        tensors = self.dump_analyzer.select_tensors('o', iterations=1)
        assert len(tensors) == 286
        assert tensors[0].value() is not None

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_select_tensor_statistics(self):
        """Test select tensor_statistics with specified rank and iterations."""
        tensor_statistics = self.dump_analyzer.select_tensor_statistics(ranks=0, iterations=1)
        assert len(tensor_statistics) == 1
        assert len(tensor_statistics[0]) == 1
        assert len(tensor_statistics[0][1]) == 3

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_summary_statistics(self):
        """Test summary_statistic, for statistics from statistic.csv."""
        tensor_statistics = self.dump_analyzer.select_tensor_statistics(ranks=0, iterations=1)
        with tempfile.TemporaryDirectory(dir='/tmp') as tmp_dir:
            self.dump_analyzer.summary_statistics(tensor_statistics, 65500, tmp_dir)
            statistic_file = os.path.join(tmp_dir, 'statistics_summary.csv')
            os.path.isfile(statistic_file)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_iterations(self):
        """Test get iterations."""
        assert self.dump_analyzer.get_iterations(ranks=0) == [0, 1, 4, 6]

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_affected_nodes(self):
        """Test get iterations."""
        tensors = self.dump_analyzer.select_tensors('Conv', iterations=0, case_sensitive=True)
        assert len(tensors) == 72

    @pytest.mark.parametrize("watchpoint", [
        TensorTooLargeCondition(abs_mean_gt=0.0),
        TensorTooSmallCondition(max_lt=-1, min_lt=1),
        TensorUnchangedCondition(0, 1),
        TensorRangeCondition(range_percentage_gt=0, range_start_inclusive=0, range_end_inclusive=4),
        TensorOverflowCondition(),
        OperatorOverflowCondition(),
        TensorAllZeroCondition(0),
        TensorChangeBelowThresholdCondition(0.0),
        TensorChangeAboveThresholdCondition(0.0)
    ])
    def test_watchpoint(self, watchpoint):
        """Test watchpoint."""
        tensors = self.dump_analyzer.select_tensors('Conv2DBackpropFilter', iterations=0, case_sensitive=True, ranks=0)
        watchpoint = Watchpoint(tensors, watchpoint)
        hits = self.dump_analyzer.check_watchpoints([watchpoint])
        assert len(hits) == 6
