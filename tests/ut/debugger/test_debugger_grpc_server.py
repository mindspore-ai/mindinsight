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
    Test debugger grpc server.
Usage:
    pytest tests/ut/debugger/test_debugger_grpc_server.py
"""
from unittest import mock
from unittest.mock import MagicMock

import numpy as np

from mindinsight.debugger.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.debugger.common.utils import get_ack_reply, ServerStatus
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_grpc_server import DebuggerGrpcServer
from mindinsight.debugger.proto.debug_grpc_pb2 import EventReply, SetCMD, Chunk, WatchpointHit
from mindinsight.debugger.proto.ms_graph_pb2 import TensorProto, DataType
from mindinsight.debugger.stream_handler import WatchpointHitHandler, GraphHandler, \
    WatchpointHandler
from tests.ut.debugger.configurations import GRAPH_PROTO_FILE


class MockDataGenerator:
    """Mocked Data generator."""

    @staticmethod
    def get_run_cmd(steps=0, level='step', node_name=''):
        """Get run command."""
        event = get_ack_reply()
        event.run_cmd.run_level = level
        if level == 'node':
            event.run_cmd.node_name = node_name
        else:
            event.run_cmd.run_steps = steps
        return event

    @staticmethod
    def get_exit_cmd():
        """Get exit command."""
        event = get_ack_reply()
        event.exit = True
        return event

    @staticmethod
    def get_set_cmd():
        """Get set command"""
        event = get_ack_reply()
        event.set_cmd.CopyFrom(SetCMD(id=1, watch_condition=1))
        return event

    @staticmethod
    def get_view_cmd():
        """Get set command"""
        view_event = get_ack_reply()
        ms_tensor = view_event.view_cmd.tensors.add()
        ms_tensor.node_name, ms_tensor.slot = 'mock_node_name', '0'
        event = {'view_cmd': view_event, 'node_name': 'mock_node_name', 'graph_name': 'mock_graph_name'}
        return event

    @staticmethod
    def get_graph_chunks():
        """Get graph chunks."""
        chunk_size = 1024
        with open(GRAPH_PROTO_FILE, 'rb') as file_handler:
            content = file_handler.read()
        chunks = [Chunk(buffer=content[0:chunk_size]), Chunk(buffer=content[chunk_size:])]
        return chunks

    @staticmethod
    def get_tensors():
        """Get tensors."""
        tensor_content = np.asarray([1, 2, 3, 4, 5, 6]).astype(np.float32).tobytes()
        tensor_pre = TensorProto(
            node_name='mock_node_name',
            slot='0',
            data_type=DataType.DT_FLOAT32,
            dims=[2, 3],
            tensor_content=tensor_content[:12],
            finished=0
        )
        tensor_succ = TensorProto()
        tensor_succ.CopyFrom(tensor_pre)
        tensor_succ.tensor_content = tensor_content[12:]
        tensor_succ.finished = 1
        return [tensor_pre, tensor_succ]

    @staticmethod
    def get_watchpoint_hit():
        """Get watchpoint hit."""
        res = WatchpointHit(id=1)
        res.tensor.node_name = 'mock_node_name'
        res.tensor.slot = '0'
        return res


class TestDebuggerGrpcServer:
    """Test debugger grpc server."""

    @classmethod
    def setup_class(cls):
        """Initialize for test class."""
        cls._server = None

    def setup_method(self):
        """Initialize for each testcase."""
        cache_store = DebuggerCache()
        self._server = DebuggerGrpcServer(cache_store, condition_mgr=ConditionMgr())

    def test_waitcmd_with_pending_status(self):
        """Test wait command interface when status is pending."""
        res = self._server.WaitCMD(MagicMock(), MagicMock())
        assert res.status == EventReply.Status.FAILED

    @mock.patch.object(WatchpointHitHandler, 'empty', False)
    @mock.patch.object(WatchpointHitHandler, 'put')
    @mock.patch.object(DebuggerGrpcServer, '_deal_with_old_command')
    def test_waitcmd_with_old_command(self, *args):
        """Test wait command interface with old command."""
        old_command = MockDataGenerator.get_run_cmd(steps=1)
        args[0].return_value = old_command
        setattr(self._server, '_status', ServerStatus.WAITING)
        setattr(self._server, '_received_view_cmd', {'node_name': 'mock_node_name'})
        setattr(self._server, '_received_hit', [MagicMock()])
        res = self._server.WaitCMD(MagicMock(cur_step=1, cur_node=''), MagicMock())
        assert res == old_command

    @mock.patch.object(DebuggerGrpcServer, '_deal_with_old_command', return_value=None)
    @mock.patch.object(DebuggerGrpcServer, '_wait_for_next_command')
    def test_waitcmd_with_next_command(self, *args):
        """Test wait for next command."""
        old_command = MockDataGenerator.get_run_cmd(steps=1)
        args[0].return_value = old_command
        setattr(self._server, '_status', ServerStatus.WAITING)
        res = self._server.WaitCMD(MagicMock(cur_step=1, cur_node=''), MagicMock())
        assert res == old_command

    @mock.patch.object(DebuggerGrpcServer, '_deal_with_old_command', return_value=None)
    @mock.patch.object(DebuggerGrpcServer, '_wait_for_next_command')
    def test_waitcmd_with_next_command_is_none(self, *args):
        """Test wait command interface with next command is None."""
        args[0].return_value = None
        setattr(self._server, '_status', ServerStatus.RECEIVE_GRAPH)
        res = self._server.WaitCMD(MagicMock(cur_step=1, cur_node=''), MagicMock())
        assert res == get_ack_reply(1)

    @mock.patch.object(DebuggerCache, 'get_command', return_value=(0, None))
    @mock.patch.object(DebuggerCache, 'has_command')
    def test_deal_with_old_command_with_continue_steps(self, *args):
        """Test deal with old command with continue steps."""
        args[0].side_effect = [True, False]
        setattr(self._server, '_old_run_cmd', {'left_step_count': 1})
        res = self._server._deal_with_old_command()
        assert res == MockDataGenerator.get_run_cmd(steps=1)

    @mock.patch.object(DebuggerCache, 'get_command')
    @mock.patch.object(DebuggerCache, 'has_command', return_value=True)
    def test_deal_with_old_command_with_exit_cmd(self, *args):
        """Test deal with exit command."""
        cmd = MockDataGenerator.get_exit_cmd()
        args[1].return_value = ('0', cmd)
        res = self._server._deal_with_old_command()
        assert res == cmd

    @mock.patch.object(DebuggerCache, 'get_command')
    @mock.patch.object(DebuggerCache, 'has_command', return_value=True)
    def test_deal_with_old_command_with_view_cmd(self, *args):
        """Test deal with view command."""
        cmd = MockDataGenerator.get_view_cmd()
        args[1].return_value = ('0', cmd.copy())
        res = self._server._deal_with_old_command()
        assert res == cmd.pop('view_cmd')
        expect_received_view_cmd = {'node_info': cmd, 'wait_for_tensor': True}
        assert getattr(self._server, '_received_view_cmd') == expect_received_view_cmd

    @mock.patch.object(DebuggerCache, 'get_command')
    def test_wait_for_run_command(self, *args):
        """Test wait for run command."""
        cmd = MockDataGenerator.get_run_cmd(steps=2)
        args[0].return_value = ('0', cmd)
        setattr(self._server, '_status', ServerStatus.WAITING)
        res = self._server._wait_for_next_command()
        assert res == MockDataGenerator.get_run_cmd(steps=1)
        assert getattr(self._server, '_old_run_cmd') == {'left_step_count': 1}

    @mock.patch.object(DebuggerCache, 'get_command')
    def test_wait_for_pause_and_run_command(self, *args):
        """Test wait for run command."""
        pause_cmd = MockDataGenerator.get_run_cmd(steps=0)
        empty_view_cmd = MockDataGenerator.get_view_cmd()
        empty_view_cmd.pop('view_cmd')
        run_cmd = MockDataGenerator.get_run_cmd(steps=2)
        args[0].side_effect = [('0', pause_cmd), ('0', empty_view_cmd), ('0', run_cmd)]
        setattr(self._server, '_status', ServerStatus.WAITING)
        res = self._server._wait_for_next_command()
        assert res == run_cmd
        assert getattr(self._server, '_old_run_cmd') == {'left_step_count': 1}

    def test_send_matadata(self):
        """Test SendMatadata interface."""
        res = self._server.SendMetadata(MagicMock(training_done=False), MagicMock())
        assert res == get_ack_reply()

    def test_send_matadata_with_training_done(self):
        """Test SendMatadata interface."""
        res = self._server.SendMetadata(MagicMock(training_done=True), MagicMock())
        assert res == get_ack_reply()

    def test_send_graph(self):
        """Test SendGraph interface."""
        res = self._server.SendGraph(MockDataGenerator.get_graph_chunks(), MagicMock())
        assert res == get_ack_reply()

    def test_send_tensors(self):
        """Test SendTensors interface."""
        res = self._server.SendTensors(MockDataGenerator.get_tensors(), MagicMock())
        assert res == get_ack_reply()

    @mock.patch.object(WatchpointHandler, 'get_watchpoint_by_id')
    @mock.patch.object(GraphHandler, 'get_graph_id_by_full_name', return_value='mock_graph_name')
    @mock.patch.object(GraphHandler, 'get_node_name_by_full_name')
    def test_send_watchpoint_hit(self, *args):
        """Test SendWatchpointHits interface."""
        args[0].side_effect = [None, 'mock_full_name']
        watchpoint_hit = MockDataGenerator.get_watchpoint_hit()
        res = self._server.SendWatchpointHits([watchpoint_hit, watchpoint_hit], MagicMock())
        assert res == get_ack_reply()
