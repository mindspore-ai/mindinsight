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
"""Test GraphRunOperator for offline debugger."""
import json
import os
import shutil
from unittest import mock

import pytest

from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager
from mindinsight.debugger.stream_operator.graph_runs_operator import GraphRunsOperator
from tests.st.func.debugger.conftest import DEBUGGER_EXPECTED_RESULTS
from tests.st.func.debugger.debugger_services import mock_dbg_services
from tests.st.func.debugger.utils import build_multi_net_dump_structure, DumpStructureGenerator
from tests.utils.tools import compare_result_with_file


class TestGraphRunsOperator:
    """Test GraphRunsOperator."""

    @classmethod
    def setup_class(cls):
        """Prepare dump structure."""
        cls.debug = False
        cls.debugger_tmp_dir = build_multi_net_dump_structure()
        cls.cache_store = cls.get_cache_store(cls.debugger_tmp_dir)

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @staticmethod
    def get_cache_store(dump_dir):
        """Get initialized cache store."""
        cache_store = DebuggerCache()
        with mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module', return_value=mock_dbg_services):
            offline_manager = DebuggerOfflineManager(cache_store, dump_dir)
            offline_manager.initialize()
        return cache_store

    @pytest.mark.level
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_graph_runs(self):
        """Test load graph history."""
        res = GraphRunsOperator(self.cache_store).get_graph_runs(0)
        real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, 'offline_debugger', 'get_graph_runs.json')
        if self.debug:
            json.dump(res, open(real_path, 'w'))
        compare_result_with_file(res, real_path)

    def test_graph_history_mismatch(self):
        """Test get graph run when graph history mismatch."""
        path = os.path.join(self.debugger_tmp_dir, 'mismatch')
        gen = DumpStructureGenerator(path)
        history = {0: [0, 2, 4],
                   3: [1, 3, 5, 6]}
        steps = {0: [0, 1]}
        gen.generate(history=history, dump_steps=steps)
        cache_store = self.get_cache_store(path)
        res = GraphRunsOperator(cache_store).get_graph_runs(0)
        assert res == {'graph_runs': []}
