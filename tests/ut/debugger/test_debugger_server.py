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
    Test debugger server.
Usage:
    pytest tests/ut/debugger/test_debugger_server.py
"""
import signal
from threading import Thread
from unittest import mock
from unittest.mock import MagicMock

import grpc
import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerCompareTensorError, DebuggerCreateWatchPointError, DebuggerDeleteWatchPointError
from mindinsight.debugger.common.utils import Streams, ServerStatus
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_services.debugger_server_factory import DebuggerServerContext
from mindinsight.debugger.debugger_session import DebuggerSession as DebuggerServer
from mindinsight.debugger.stream_handler import GraphHandler, WatchpointHandler, MetadataHandler, \
    TensorHandler, MultiCardGraphHandler, MultiCardWatchpointHitHandler, WatchpointHitHandler
from mindinsight.debugger.stream_operator import watchpoint_operator
from tests.ut.debugger.configurations import compare_debugger_result_with_file, mock_tensor_history


class TestDebuggerServer:
    """Test debugger server."""

    @classmethod
    def setup_class(cls):
        """Initialize for test class."""
        cls._server = None

    def setup_method(self):
        """Prepare debugger server object."""
        context = DebuggerServerContext(dbg_mode='online')
        self._server = DebuggerServer(context)

    @mock.patch.object(signal, 'signal')
    @mock.patch.object(Thread, 'join')
    @mock.patch.object(Thread, 'start')
    @mock.patch.object(grpc, 'server')
    def test_stop_server(self, *args):
        """Test stop debugger server."""
        mock_grpc_server_manager = MagicMock()
        args[0].return_value = mock_grpc_server_manager
        self._server.start()
        self._server._stop_handler(MagicMock(), MagicMock())
        assert self._server.back_server is not None

    @mock.patch.object(DebuggerCache, 'get_data')
    def test_poll_data(self, *args):
        """Test poll data request."""
        mock_data = {'pos': 'mock_data'}
        args[0].return_value = mock_data
        res = self._server.poll_data('0')
        assert res == mock_data

    def test_poll_data_with_exept(self):
        """Test poll data with wrong input."""
        with pytest.raises(DebuggerParamValueError, match='Pos should be string.'):
            self._server.poll_data(1)

    @mock.patch.object(GraphHandler, 'search_nodes')
    def test_search(self, *args):
        """Test search node."""
        graph_stream = self._server.cache_store.get_stream_handler(Streams.GRAPH)
        setattr(graph_stream, '_graph_handlers', {0: GraphHandler()})
        mock_graph = {'nodes': ['mock_nodes']}
        args[0].return_value = mock_graph
        res = self._server.search({'name': 'mock_name'})
        assert res == mock_graph

    def test_tensor_comparision_with_wrong_status(self):
        """Test tensor comparison with wrong status."""
        with pytest.raises(
                DebuggerCompareTensorError,
                match='Failed to compare tensors as the MindSpore is not in waiting state.'):
            self._server.tensor_comparisons(name='mock_node_name:0', shape='[:, :]')

    @mock.patch.object(MultiCardGraphHandler, 'get_graph_handler_by_rank_id')
    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    @mock.patch.object(GraphHandler, 'get_node_type')
    @mock.patch.object(GraphHandler, 'get_graph_id_by_name')
    @mock.patch.object(GraphHandler, 'validate_graph_name')
    @mock.patch.object(GraphHandler, 'get_full_name', return_value='mock_node_name')
    def test_tensor_comparision_with_wrong_type(self, *args):
        """Test tensor comparison with wrong type."""
        args[1].return_value = 'name_scope'
        with pytest.raises(DebuggerParamValueError, match='The node type must be parameter'):
            self._server.tensor_comparisons(name='mock_node_name:0', shape='[:, :]')

    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    @mock.patch.object(GraphHandler, 'get_graph_id_by_name')
    @mock.patch.object(GraphHandler, 'validate_graph_name')
    @mock.patch.object(GraphHandler, 'get_node_type', return_value='Parameter')
    @mock.patch.object(GraphHandler, 'get_full_name', return_value='mock_node_name')
    @mock.patch.object(TensorHandler, 'get_tensors_diff')
    def test_tensor_comparision(self, *args):
        """Test tensor comparison"""
        graph_stream = self._server.cache_store.get_stream_handler(Streams.GRAPH)
        setattr(graph_stream, '_graph_handlers', {0: GraphHandler()})
        mock_diff_res = {'tensor_value': {}}
        args[0].return_value = mock_diff_res
        res = self._server.tensor_comparisons('mock_node_name:0', '[:, :]')
        assert res == mock_diff_res

    def test_retrieve_with_pending(self):
        """Test retrieve request in pending status."""
        res = self._server.retrieve(mode='all')
        assert res.get('metadata', {}).get('state') == 'pending'

    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    def test_retrieve_all(self):
        """Test retrieve request."""
        res = self._server.retrieve(mode='all')
        compare_debugger_result_with_file(res, 'debugger_server/retrieve_all.json')

    def test_retrieve_with_invalid_mode(self):
        """Test retrieve with invalid mode."""
        with pytest.raises(DebuggerParamValueError, match='Invalid mode.'):
            self._server.retrieve(mode='invalid_mode')

    @mock.patch.object(GraphHandler, 'get')
    @mock.patch.object(GraphHandler, 'get_node_type', return_value='name_scope')
    @mock.patch.object(GraphHandler, 'get_full_name', return_value='mock_node_name')
    def test_retrieve_node(self, *args):
        """Test retrieve node information."""
        graph_stream = self._server.cache_store.get_stream_handler(Streams.GRAPH)
        setattr(graph_stream, '_graph_handlers', {0: GraphHandler()})
        mock_graph = {'graph': {}}
        args[2].return_value = mock_graph
        res = self._server._retrieve_node({'name': 'mock_node_name'})
        assert res == mock_graph

    def test_retrieve_tensor_history_with_pending(self):
        """Test retrieve request in pending status."""
        res = self._server.retrieve_tensor_history('mock_node_name')
        assert res.get('metadata', {}).get('state') == 'pending'

    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    @mock.patch.object(GraphHandler, 'get_tensor_history')
    @mock.patch.object(GraphHandler, 'get_node_type', return_value='Parameter')
    def test_retrieve_tensor_history(self, *args):
        """Test retrieve tensor history."""
        graph_stream = self._server.cache_store.get_stream_handler(Streams.GRAPH)
        setattr(graph_stream, '_graph_handlers', {0: GraphHandler()})
        args[1].return_value = mock_tensor_history()
        res = self._server.retrieve_tensor_history('mock_node_name')
        compare_debugger_result_with_file(res, 'debugger_server/retrieve_tensor_history.json')

    @mock.patch.object(TensorHandler, 'get')
    @mock.patch.object(DebuggerServer, '_get_tensor_name_and_type_by_ui_name')
    def test_retrieve_tensor_value(self, *args):
        """Test retrieve tensor value."""
        mock_tensor_value = {'tensor_value': {'name': 'mock_name:0'}}
        args[0].return_value = ('Parameter', 'mock_node_name', 'mock_graph_name')
        args[1].return_value = mock_tensor_value
        res = self._server.retrieve_tensor_value('mock_name:0', 'data', '[:, :]')
        assert res == mock_tensor_value

    @mock.patch.object(WatchpointHandler, 'get')
    def test_retrieve_watchpoints(self, *args):
        """Test retrieve watchpoints."""
        mock_watchpoint = {'watch_points': {}}
        args[0].return_value = mock_watchpoint
        res = self._server._retrieve_watchpoint({})
        assert res == mock_watchpoint

    @mock.patch.object(DebuggerServer, '_retrieve_node')
    def test_retrieve_watchpoint(self, *args):
        """Test retrieve single watchpoint."""
        mock_watchpoint = {'nodes': {}}
        args[0].return_value = mock_watchpoint
        res = self._server._retrieve_watchpoint({'watch_point_id': 1})
        assert res == mock_watchpoint

    def test_create_watchpoint_with_wrong_state(self):
        """Test create watchpoint with wrong state."""
        with pytest.raises(DebuggerCreateWatchPointError, match='Failed to create watchpoint'):
            self._server.create_watchpoint({'watch_condition': {'id': 'inf'}})

    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    @mock.patch.object(GraphHandler, 'get_node_basic_info', return_value=MagicMock())
    @mock.patch.object(GraphHandler, 'get_node_type', return_value='aggregation_scope')
    @mock.patch.object(watchpoint_operator, 'get_basic_node_info', return_value=MagicMock())
    @mock.patch.object(WatchpointHandler, 'create_watchpoint')
    def test_create_watchpoint(self, *args):
        """Test create watchpoint."""
        args[0].return_value = 1
        self._server.cache_store.get_stream_handler((Streams.METADATA)).backend = 'GPU'
        res = self._server.create_watchpoint(
            {'watch_condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
             'watch_nodes': ['watch_node_name']})
        assert res == {'id': 1, 'metadata': {'enable_recheck': False, 'state': 'waiting'}}

    @mock.patch.object(MultiCardGraphHandler, 'get_graph_handler_by_rank_id')
    @mock.patch.object(MetadataHandler, 'state', 'waiting')
    @mock.patch.object(GraphHandler, 'validate_graph_name', return_value='kernel_graph_0')
    @mock.patch.object(GraphHandler, 'get_node_basic_info')
    @mock.patch.object(GraphHandler, 'search_nodes')
    @mock.patch.object(WatchpointHandler, 'validate_watchpoint_id')
    @mock.patch.object(WatchpointHandler, 'update_watchpoint')
    def test_update_watchpoint(self, *args):
        """Test update watchpoint."""
        args[2].return_value = {'nodes': [{'name': 'mock_name', 'nodes': []}]}
        res = self._server.update_watchpoint(
            {'watch_point_id': 1,
             'watch_nodes': ['search_name'],
             'mode': 1,
             'search_pattern': {'name': 'search_name'},
             'graph_name': 'kernel_graph_0'})
        assert res == {'metadata': {'enable_recheck': False, 'state': 'waiting'}}

    def test_delete_watchpoint_with_wrong_state(self):
        """Test delete watchpoint with wrong state."""
        with pytest.raises(DebuggerDeleteWatchPointError, match='Failed to delete watchpoint'):
            self._server.delete_watchpoint(watch_point_id=1)

    @mock.patch.object(MetadataHandler, 'enable_recheck', True)
    @mock.patch.object(WatchpointHandler, 'is_recheckable', return_value=True)
    @mock.patch.object(WatchpointHandler, 'delete_watchpoint')
    def test_delete_watchpoint(self, *args):
        """Test delete watchpoint with wrong state."""
        self._server.cache_store.get_stream_handler(Streams.METADATA).state = 'waiting'
        args[0].return_value = None
        res = self._server.delete_watchpoint(1)
        assert res == {'metadata': {'enable_recheck': True, 'state': 'waiting'}}

    @mock.patch.object(MetadataHandler, 'state', ServerStatus.WAITING.value)
    @mock.patch.object(WatchpointHitHandler, 'group_by')
    @mock.patch.object(MultiCardWatchpointHitHandler, 'get_hit_handler_by_rank_id')
    @mock.patch.object(MultiCardWatchpointHitHandler, 'check_rank_id')
    @mock.patch.object(MultiCardGraphHandler, 'validate_rank_id')
    def test_search_watchpoint_hits(self, *args):
        """Test retrieve single watchpoint."""
        args[0].return_value = True
        args[1].return_value = True
        args[2].return_value = WatchpointHitHandler()
        args[3].return_value = {'watch_point_hits': 'mocked_watch_point_hits'}
        res = self._server.search_watchpoint_hits({'rank_id': 0})
        assert res == {'watch_point_hits': 'mocked_watch_point_hits', 'outdated': False}

    @mock.patch.object(MetadataHandler, 'state', ServerStatus.WAITING.value)
    @mock.patch.object(MultiCardGraphHandler, 'validate_rank_id')
    def test_search_watchpoint_hits_error_rank_id(self, *args):
        """Test retrieve single watchpoint."""
        args[0].return_value = False
        rank_id = 1
        with pytest.raises(DebuggerParamValueError, match="Parameter <rank_id> {} is not valid.".format(rank_id)):
            self._server.search_watchpoint_hits({'rank_id': rank_id})

    @mock.patch.object(MetadataHandler, 'state', ServerStatus.WAITING.value)
    @mock.patch.object(MultiCardWatchpointHitHandler, 'check_rank_id')
    @mock.patch.object(MultiCardGraphHandler, 'validate_rank_id')
    def test_search_watchpoint_hits_no_hits(self, *args):
        """Test retrieve single watchpoint."""
        args[0].return_value = True
        args[1].return_value = False
        res = self._server.search_watchpoint_hits({'rank_id': 0})
        assert res == {'outdated': False}
