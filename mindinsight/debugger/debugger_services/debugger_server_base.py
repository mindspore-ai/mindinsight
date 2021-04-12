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
"""DebuggerServerBase."""
import threading
from abc import abstractmethod
from functools import wraps

from mindinsight.debugger.common.exceptions.exceptions import DebuggerServerRunningError
from mindinsight.debugger.common.log import LOGGER as log


def debugger_server_wrap(func):
    """Wrapper for catch exception."""
    @wraps(func)
    def record_log(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            log.exception(err)
            raise DebuggerServerRunningError(str(err))
    return record_log


class DebuggerServerBase(threading.Thread):
    """
    Debugger Server Base.

    Args:
        cache_store (DebuggerCacheStore): Cache store for debugger server.
        context (DebuggerServerContext): Context for initialize debugger server.
    """

    def __init__(self, cache_store, context):
        super(DebuggerServerBase, self).__init__()
        self._cache_store = cache_store
        self._context = context

    @abstractmethod
    @debugger_server_wrap
    def run(self):
        """Function that should be called when thread started."""

    @abstractmethod
    @debugger_server_wrap
    def stop(self):
        """Stop debugger server."""
