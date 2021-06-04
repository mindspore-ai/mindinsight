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
"""Debugger Online server."""
from concurrent import futures

import grpc
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.conf import settings
from mindinsight.debugger.debugger_services.debugger_grpc_server import DebuggerGrpcServer
from mindinsight.debugger.debugger_services.debugger_server_base import DebuggerServerBase
from mindinsight.debugger.proto import debug_grpc_pb2_grpc as grpc_server_base


def get_debugger_hostname():
    """Get hostname for online debugger server."""
    grpc_port = settings.DEBUGGER_PORT if hasattr(settings, 'DEBUGGER_PORT') else 50051
    host = settings.HOST if hasattr(settings, 'HOST') else '[::]'
    hostname = "{}:{}".format(host, grpc_port)
    return hostname


class DebuggerOnlineServer(DebuggerServerBase):
    """Debugger Online Server."""

    def __init__(self, cache_store, context):
        super(DebuggerOnlineServer, self).__init__(cache_store, context)
        self._grpc_server_manager = self.get_grpc_server_manager()

    def run(self):
        self._grpc_server_manager.start()
        log.info("Start grpc server %s", self._context.hostname)
        self._grpc_server_manager.wait_for_termination()

    def get_grpc_server_manager(self):
        """Get grpc server instance according to hostname."""
        if self._context.hostname is None:
            self._context.hostname = get_debugger_hostname()
        grpc_server = DebuggerGrpcServer(self._cache_store)
        grpc_server_manager = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server_base.add_EventListenerServicer_to_server(grpc_server, grpc_server_manager)
        grpc_server_manager.add_insecure_port(self._context.hostname)
        return grpc_server_manager

    def stop(self):
        self._grpc_server_manager.stop(grace=None)
        self.join()
