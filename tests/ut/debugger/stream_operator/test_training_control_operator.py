# Copyright 2020 Huawei Technologies Co., Ltd
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
    Test debugger training control operator.
Usage:
    pytest tests/ut/debugger/stream_operator/test_training_control_operator.py
"""
from unittest import mock

import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.proto.debug_grpc_pb2 import RunCMD
from mindinsight.debugger.stream_handler import GraphHandler, MetadataHandler, MultiCardGraphHandler
from mindinsight.debugger.stream_operator.training_control_operator import TrainingControlOperator


class TestTrainingControlOperator:
    """Test debugger server."""

    @classmethod
    def setup_class(cls):
        """Initialize for test class."""
        cls._server = None

    def setup_method(self):
        """Prepare debugger server object."""
        cache_store = DebuggerCache()
        cache_store.initialize()
        self._server = TrainingControlOperator(cache_store)

    @mock.patch.object(MultiCardGraphHandler, 'get_graph_handler_by_rank_id')
    @mock.patch.object(GraphHandler, 'get_node_type')
    def test_validate_leaf_name(self, *args):
        """Test validate leaf name."""
        args[0].return_value = 'name_scope'
        with pytest.raises(DebuggerParamValueError, match='Invalid leaf node name.'):
            self._server._validate_continue_node_name(node_name='mock_node_name', graph_name='mock_graph_name',
                                                      rank_id=0)

    @pytest.mark.parametrize('mode, cur_state, state', [
        ('continue', 'waiting', 'sending'),
        ('pause', 'running', 'sending'),
        ('terminate', 'waiting', 'sending')])
    def test_control(self, mode, cur_state, state):
        """Test control request."""
        with mock.patch.object(MetadataHandler, 'state', cur_state):
            res = self._server.control(mode=mode, params={})
            assert res == {'metadata': {'enable_recheck': False, 'state': state}}

    def test_construct_run_event(self):
        """Test construct run event."""
        res = self._server._construct_run_event({'level': 'node'})
        assert res.run_cmd == RunCMD(run_level='node', node_name='')

    @pytest.mark.parametrize('mode, state', [
        ('reset', 'waiting')])
    def test_control_reset_step(self, mode, state):
        """Test control request, in 'reset' mode."""
        with mock.patch.object(MetadataHandler, 'max_step_num', 10), \
            mock.patch.object(MetadataHandler, 'debugger_type', 'offline'):
            res = self._server.control(mode=mode, params={'steps': 9})
            assert res == {'metadata': {'enable_recheck': True, 'state': state, 'step': 9}}
