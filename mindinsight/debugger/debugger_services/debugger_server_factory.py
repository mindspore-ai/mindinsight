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
"""Debugger server factory."""
import threading

from mindinsight.debugger.common.utils import DebuggerServerMode
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineServer
from mindinsight.debugger.debugger_services.debugger_online_server import DebuggerOnlineServer


class DebuggerServerFactory:
    """Create debugger server according to debugger mode."""

    _lock = threading.Lock()
    _instance = None

    def __init__(self):
        self._server_map = {
            DebuggerServerMode.ONLINE.value: DebuggerOnlineServer,
            DebuggerServerMode.OFFLINE.value: DebuggerOfflineServer
        }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def get_debugger_server(self, cache_store, context):
        """
        Get debugger server according to debugger_context and cache_store.

        Args:
            cache_store (DebuggerCacheStore): Cache store for debugger server.
            context (DebuggerServerContext): Context for initialize debugger server.

        Returns:
            DebuggerServerBase, Debugger server object.
        """
        dbg_server = None
        dbg_server_class = self._server_map.get(context.dbg_mode)
        if dbg_server_class:
            dbg_server = dbg_server_class(cache_store, context)
        return dbg_server


class DebuggerServerContext:
    """
    Debugger server context.

    Args:
        dbg_mode (str): The debugger mode. Optional: `online` or `offline`.
        train_job (str): The relative directory of debugger dump data for one training.
            Used only when dbg_mode is `offline.`
        dbg_dir (str): The base directory of debugger dump data for one training.
            Used only when dbg_mode is `offline.`
        hostname (str): The hostname used for online debugger server.
            Used only when dbg_mode is `online.`
    """
    def __init__(self, dbg_mode, train_job=None, dbg_dir=None, hostname=None):
        self._dbg_mode = dbg_mode
        self._train_job = train_job
        self._dbg_dir = dbg_dir
        self.hostname = hostname

    @property
    def dbg_mode(self):
        """Property of debugger mode."""
        return self._dbg_mode

    @property
    def dbg_dir(self):
        """Property of debugger mode."""
        return self._dbg_dir

    @property
    def train_job(self):
        """The property of train job."""
        return self._train_job
