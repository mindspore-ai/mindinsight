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
"""Test WatchpointHandler."""
import json
import os
from unittest import mock, TestCase

import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.stream_cache.watchpoint import Watchpoint
from mindinsight.debugger.stream_handler.watchpoint_handler import WatchpointHandler, \
    WatchpointHitHandler, validate_watch_condition, validate_watch_condition_params

from tests.ut.debugger.configurations import init_graph_handler, mock_tensor_proto, \
    mock_tensor_history


class TestWatchpointHandler:
    """Test WatchpointHandler."""
    @classmethod
    def setup_class(cls):
        """Init WatchpointHandler for watchpoint unittest."""
        cls.handler = WatchpointHandler()
        cls.graph_results_dir = os.path.join(os.path.dirname(__file__),
                                             '../expected_results/graph')
        cls.graph_stream = init_graph_handler()

    @pytest.mark.parametrize(
        "watch_condition, watch_nodes, watch_point_id, expect_new_id", [
            ({'condition': 'INF'}, None, None, 1),
            ({'condition': 'INF'}, ["Default"], None, 2),
            ({'condition': 'MAX_GT', 'param': 1},
             ["Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92"], None, 3)
        ])
    @mock.patch.object(Watchpoint, 'add_nodes')
    def test_create_watchpoint(self, mock_add_nodes, watch_condition, watch_nodes,
                               watch_point_id, expect_new_id):
        """Test create_watchpoint."""
        mock_add_nodes.return_value = None
        watch_point_id = self.handler.create_watchpoint(watch_condition, watch_nodes, watch_point_id)
        assert watch_point_id == expect_new_id

    @pytest.mark.parametrize("filter_condition", [True, False])
    @mock.patch.object(Watchpoint, 'get_set_cmd')
    @mock.patch.object(Watchpoint, 'get_watch_condition_info')
    def test_get(self, mock_get_wp, mock_get_cmd, filter_condition):
        """Test get."""
        mock_get_wp.return_value = None
        mock_get_cmd.return_value = None
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.get(filter_condition)
        TestCase().assertIn(f"DEBUG:debugger.debugger:get the watch points with filter_condition:{filter_condition}",
                            log_content.output)

    def test_get_watchpoint_by_id_except(self):
        """Test get_watchpoint_by_id."""
        watchpoint_id = 4
        with pytest.raises(DebuggerParamValueError) as err:
            self.handler.get_watchpoint_by_id(watchpoint_id)
        assert err.value.error_code == '5054B081'
        assert err.value.message == f"ValueError. Invalid watchpoint id {watchpoint_id}"

    @pytest.mark.parametrize("graph_file, watch_point_id", [
        ('graph_handler_get_3_single_node.json', 4)
    ])
    @mock.patch.object(WatchpointHandler, '_set_watch_status_recursively')
    def test_set_watch_nodes(self, mock_set_recur, graph_file, watch_point_id):
        """Test set_watch_nodes."""
        path = os.path.join(self.graph_results_dir, graph_file)
        with open(path, 'r') as f:
            graph = json.load(f)
        instance = mock_set_recur.return_value
        self.handler.set_watch_nodes(graph, self.graph_stream, watch_point_id)
        assert instance.iscalled()

    @pytest.mark.parametrize(
        "watch_point_id, watch_nodes, watched, expect_updated_id", [
            (2, ["Default"], 0, 2),
            (3, ["Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92"], 1, 3)
        ])
    @mock.patch.object(Watchpoint, 'remove_nodes')
    @mock.patch.object(Watchpoint, 'add_nodes')
    def test_update_watchpoint(self, mock_add_nodes, mock_remove_nodes, watch_point_id, watch_nodes,
                               watched, expect_updated_id):
        """Test update_watchpoint."""
        mock_add_nodes.return_value = None
        mock_remove_nodes.return_value = None
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.update_watchpoint(watch_point_id, watch_nodes, watched)
        TestCase().assertIn(f"DEBUG:debugger.debugger:Update watchpoint {expect_updated_id} in cache.",
                            log_content.output)

    @pytest.mark.parametrize(
        "watch_point_id, expect_deleted_ids", [
            (3, 3), (2, 2)
        ])
    def test_delete_watchpoint(self, watch_point_id, expect_deleted_ids):
        """Test delete_watchpoint."""
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.delete_watchpoint(watch_point_id)
        TestCase().assertIn(f"DEBUG:debugger.debugger:Delete watchpoint {expect_deleted_ids} in cache.",
                            log_content.output)


class TestWatchpointHitHandler:
    """Test WatchpointHitHandler."""
    @classmethod
    def setup_class(cls):
        """Setup."""
        cls.handler = WatchpointHitHandler()
        cls.tensor_proto = mock_tensor_proto()
        cls.tensor_hist = mock_tensor_history()

    @mock.patch('mindinsight.debugger.stream_cache.watchpoint.WatchpointHit')
    def test_put(self, mock_hit):
        """Test put."""
        value = {
            'tensor_proto': self.tensor_proto,
            'watchpoint': {'id': 1, 'watch_condition': {'condition': 'INF'}},
            'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92'
        }
        mock_hit.return_value = mock.MagicMock(
            tensor_proto=value.get('tensor_proto'),
            watchpoint=value.get('watchpoint'),
            node_name=value.get('node_name')
        )
        self.handler.put(value)

    @pytest.mark.parametrize("filter_condition", [
        None, "Default/network-WithLossCell/_backbone-LeNet5/conv1-Conv2d/Cast-op190"
    ])
    @mock.patch.object(WatchpointHitHandler, 'get_watchpoint_hits')
    def test_get(self, mock_get, filter_condition):
        """Test get."""
        mock_get.return_value = {'watch_point_hits': []}
        self.handler.get(filter_condition)

    @mock.patch.object(WatchpointHitHandler, '_is_tensor_hit')
    def test_update_tensor_history(self, mock_hit):
        """Test update_tensor_history."""
        mock_hit.side_effect = [True, False]
        self.handler.update_tensor_history(self.tensor_hist)


def test_validate_watch_condition_type_error():
    """Test validate_watch_condition."""
    watch_condition = []
    with pytest.raises(DebuggerParamTypeError) as err:
        validate_watch_condition(watch_condition)
    assert err.value.error_code == '5054B080'

    watch_condition = {'watch_condition': {'condition': 'MAXIMUM'}}
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition(watch_condition)
    assert err.value.error_code == '5054B081'


def test_validate_watch_condition_params_except():
    """Test validate_watch_condition_params."""
    watch_condition = {'watch_condition': {'condition': 'NAN', 'param': 1}}
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition_params(watch_condition)
    assert err.value.error_code == '5054B081'

    watch_condition = {'watch_condition': {'condition': 'MAX_GT', 'param': '0'}}
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition_params(watch_condition)
    assert err.value.error_code == '5054B081'
