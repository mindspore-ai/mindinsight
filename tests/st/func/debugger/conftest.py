# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
Description: This file is used for some common util.
"""
import os
from unittest.mock import Mock

import pytest
from flask import Response

from mindinsight.conf import settings
from mindinsight.datavisual.utils import tools
from mindinsight.debugger.session_manager import SessionManager
from mindinsight.debugger.stream_handler.graph_handler import GraphHandler
from mindinsight.domain.graph.proto import ms_graph_pb2

GRAPH_PROTO_FILE = os.path.join(
    os.path.dirname(__file__), '../../../utils/resource/graph_pb/lenet.pb'
)

DEBUGGER_BASE_URL = '/v1/mindinsight/debugger/sessions/0/'
DEBUGGER_TEST_BASE_DIR = os.path.dirname(__file__)
DEBUGGER_EXPECTED_RESULTS = os.path.join(DEBUGGER_TEST_BASE_DIR, 'expect_results')


def init_graph_handler():
    """Init graph proto."""
    with open(GRAPH_PROTO_FILE, 'rb') as file_handler:
        content = file_handler.read()

    graph = ms_graph_pb2.GraphProto()
    graph.ParseFromString(content)

    graph_handler = GraphHandler()
    graph_handler.put(graph)

    return graph_handler


@pytest.fixture(scope='session')
def app_client():
    """This fixture is flask server."""
    packages = ["mindinsight.backend.debugger"]
    settings.ENABLE_DEBUGGER = True

    mock_obj = Mock(return_value=packages)
    tools.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    client = APP.test_client()
    original_val = settings.ENABLE_RECOMMENDED_WATCHPOINTS
    settings.ENABLE_RECOMMENDED_WATCHPOINTS = False
    try:
        yield client
    finally:
        settings.ENABLE_RECOMMENDED_WATCHPOINTS = original_val
    SessionManager.get_instance().exit()
