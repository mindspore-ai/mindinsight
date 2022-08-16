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
"""
Function:
    Test query the offline debugger api of node.
Usage:
    pytest tests/st/func/debugger/api/test_node.py
"""

import os
import shutil
from unittest import mock

import pytest

from mindinsight.debugger import DumpAnalyzer
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager
from tests.st.func.debugger.utils import build_multi_net_dump_structure
from tests.st.func.debugger.debugger_services import mock_dbg_services


class TestNode:
    """Test debugger on Ascend and GPU backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.debugger_tmp_dir = build_multi_net_dump_structure(create_tensor=True)
        with mock.patch.object(DebuggerOfflineManager, 'get_dbg_service_module', return_value=mock_dbg_services):
            dump_analyzer = DumpAnalyzer(cls.debugger_tmp_dir)
            cls.node = dump_analyzer.select_nodes('Conv2D-op1')[0]

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_input_tensors(self):
        """Test the method get_input_tensors."""
        input_tensors = self.node.get_input_tensors()
        assert input_tensors

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_output_tensors(self):
        """Test the method get_output_tensors."""
        output_tensors = self.node.get_output_tensors()
        assert output_tensors

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_graph_name(self):
        """Test the graph_name property."""
        graph_name = self.node.graph_name
        assert graph_name

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_name(self):
        """Test the name property."""
        name = self.node.name
        assert name

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_rank(self):
        """Test the property rank."""
        rank_id = self.node.rank
        assert isinstance(rank_id, int)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_root_graph_id(self):
        """Test the root_graph_id property."""
        root_graph_id = self.node.root_graph_id
        assert isinstance(root_graph_id, int)
