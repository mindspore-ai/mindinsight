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
import threading

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager


class DebuggerEngine:
    """Provide singleton Debugger Engine object."""
    _lock = threading.Lock()
    _instance = None

    @classmethod
    def get_instance(cls, data_loader=None, mem_limit=None):
        """Get the singleton instance."""
        if data_loader and cls._instance is not None:
            msg = "DebuggerEngine has already been created. If you want to create a new object, " \
                  "please call DebuggerEngine.clear() first."
            raise DebuggerParamValueError(msg)

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if data_loader is not None:
                        cls._instance = cls(data_loader=data_loader, mem_limit=mem_limit)
                    else:
                        msg = "First call to DebuggerEngine.get_instance must pass valid parameter."
                        raise DebuggerParamValueError(msg)
        return cls._instance

    @classmethod
    def clear(cls):
        """Clear class instance."""
        if cls._instance is not None:
            with cls._lock:
                if cls._instance is not None:
                    del cls._instance
                    cls._instance = None

    def __init__(self, data_loader, mem_limit):
        """Initialization."""
        self.data_loader = data_loader
        self.dbg_services_module = DebuggerOfflineManager.get_dbg_service_module()
        self.dbg_service = DebuggerOfflineManager.get_dbg_service(self.dbg_services_module,
                                                                  data_loader,
                                                                  mem_limit)
