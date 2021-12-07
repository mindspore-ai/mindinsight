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
# ==============================================================================
"""DebuggerEngine."""

from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager


class DebuggerEngine:
    """Debugger Engine object."""

    def __init__(self, data_loader, mem_limit):
        """Initialization."""
        self._data_loader = data_loader
        DebuggerOfflineManager.check_toolkit(self._data_loader)
        self._dbg_services_module = DebuggerOfflineManager.get_dbg_service_module()
        self._dbg_service = DebuggerOfflineManager.get_dbg_service(self.dbg_services_module,
                                                                   data_loader,
                                                                   mem_limit)

    @property
    def data_loader(self):
        """DataLoader object."""
        return self._data_loader

    @property
    def dbg_services_module(self):
        """Get dbg_services module in MindSpore."""
        return self._dbg_services_module

    @property
    def dbg_service(self):
        """Get initialized DbgServices object."""
        return self._dbg_service
