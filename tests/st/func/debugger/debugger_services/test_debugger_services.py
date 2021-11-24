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
    Test query debugger services.
Usage:
    pytest tests/st/func/debugger
"""

import os
import shutil
from unittest import mock

import pytest

from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_services.debugger_server_factory import \
    DebuggerServerFactory, DebuggerServerContext
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager
from tests.st.func.debugger.utils import build_dump_file_structure
from tests.st.func.debugger.debugger_services import mock_dbg_services


class TestDebuggerServerFactory:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.debugger_tmp_dir = build_dump_file_structure()
        cls._dbg_dir = os.path.join(cls.debugger_tmp_dir, 'Ascend/sync')
        cls._dbg_server_factory = DebuggerServerFactory()

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
    def test_get_dbg_online_server(self):
        """Get debugger online server"""
        context = DebuggerServerContext(dbg_mode='online')
        server_obj = self._dbg_server_factory.get_debugger_server(DebuggerCache(), context)
        server_obj.start()
        server_obj.stop()

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @mock.patch.object(DebuggerOfflineManager, 'get_dbg_service_module')
    def test_get_dbg_offline_server(self, mock_method):
        """Get debugger offline server"""
        mock_method.return_value = mock_dbg_services
        context = DebuggerServerContext(dbg_mode='offline', dbg_dir=self._dbg_dir)
        server_obj = self._dbg_server_factory.get_debugger_server(DebuggerCache(), context)
        server_obj.start()
        server_obj.stop()
