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
    Test debugger offline server.
Usage:
    pytest tests/ut/debugger/test_debugger_offline_server.py
"""

import os
import shutil
import tempfile
import time

from pathlib import Path
from unittest.mock import MagicMock
import pytest
import numpy as np

from mindinsight.debugger.debugger_services import debugger_offline_server
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager, convert_watchpointhit
from tests.ut.debugger.configurations import WatchpointHit


class DataLoader:
    """The Mocked DataLoader object."""

    def __init__(self, base_dir):
        self._debugger_base_dir = Path(base_dir).absolute()
        self._net_name = "Lenet"

    def get_dump_dir(self):
        """Get graph_name directory of the data."""
        return str(self._debugger_base_dir)

    def get_net_name(self):
        """Get net_name of the data."""
        return self._net_name


def init_offline_server(dbg_dir):
    """Init the offline server."""
    cache_store = MagicMock()
    server = DebuggerOfflineManager(cache_store, dbg_dir)
    return server


class TestDebuggerServer:
    """Test debugger server."""

    @classmethod
    def setup_class(cls):
        """Initialize for test class."""
        debugger_offline_server.import_module = MagicMock()
        debugger_offline_server.DataLoader = DataLoader
        cls.debugger_tmp_dir = tempfile.mkdtemp(suffix='debugger_tmp')
        cls.dump_files_dir = os.path.join(cls.debugger_tmp_dir, 'dump_dir')
        cls.iteration_0 = os.path.join(cls.dump_files_dir, 'rank_0', 'Lenet', '0', '0')
        os.makedirs(cls.iteration_0, exist_ok=True)
        cls._server = init_offline_server(cls.dump_files_dir)

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.parametrize('hit', [WatchpointHit('Default/Add-op3', 0, 0, 0, [], 0, 0, 0)])
    def test_find_timestamp(self, hit):
        """Test find timestamp of the tensor file."""
        t = int(time.time()*1000000)
        watchpointhit = convert_watchpointhit(hit)
        node_name = watchpointhit['name'].split('/')[-1]
        node_type = node_name.split('-')[0]
        tmp_file_name = f'{node_type}.{node_name}.520.2.{t}.output.0.1×10.npy'
        abs_file_name = os.path.join(self.iteration_0, tmp_file_name)
        x = np.random.rand(1, 10)
        np.save(abs_file_name, x)
        res = self._server.find_timestamp(watchpointhit, 0)
        assert res == t
