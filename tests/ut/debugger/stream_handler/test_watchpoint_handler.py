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

from google.protobuf import json_format
import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.stream_cache.watchpoint import Watchpoint
from mindinsight.debugger.stream_handler.watchpoint_handler import WatchpointHandler, \
    WatchpointHitHandler, validate_watch_condition, validate_watch_condition_params

from tests.ut.debugger.configurations import init_graph_handler, mock_tensor_proto, \
    mock_tensor_history, get_node_basic_infos, get_watch_nodes_by_search, \
    init_watchpoint_hit_handler
from tests.utils.tools import compare_result_with_file


class TestWatchpointHandler:
    """Test WatchpointHandler."""
    @classmethod
    def setup_class(cls):
        """Init WatchpointHandler for watchpoint unittest."""
        cls.handler = WatchpointHandler()
        cls.results_dir = os.path.join(os.path.dirname(__file__),
                                       '../expected_results/watchpoint')
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
    def test_create_watchpoint(self, watch_condition, watch_nodes,
                               watch_point_id, expect_new_id):
        """Test create_watchpoint."""
        watch_nodes = get_node_basic_infos(watch_nodes)
        watch_point_id = self.handler.create_watchpoint(watch_condition, watch_nodes, watch_point_id)
        assert watch_point_id == expect_new_id

    @pytest.mark.parametrize(
        "watch_point_id, watch_nodes, watched, expect_updated_id", [
            (3, ["Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92"], 1, 3),
            (3, [], 1, 3)
        ])
    def test_update_watchpoint_add(self, watch_point_id, watch_nodes, watched, expect_updated_id):
        """Test update_watchpoint on addition."""
        watch_nodes = get_node_basic_infos(watch_nodes)
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.update_watchpoint(watch_point_id, watch_nodes, watched)
        TestCase().assertIn(f"DEBUG:debugger.debugger:Update watchpoint {expect_updated_id} in cache.",
                            log_content.output)

    @pytest.mark.parametrize(
        "watch_point_id, watch_nodes, watched, expect_updated_id", [
            (2, ["Default"], 0, 2),
            (2, [], 0, 2),
        ])
    def test_update_watchpoint_delete(self, watch_point_id, watch_nodes, watched, expect_updated_id):
        """Test update_watchpoint on deletion."""
        watch_nodes = get_watch_nodes_by_search(watch_nodes)
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.update_watchpoint(watch_point_id, watch_nodes, watched)
        TestCase().assertIn(f"DEBUG:debugger.debugger:Update watchpoint {expect_updated_id} in cache.",
                            log_content.output)

    @pytest.mark.parametrize("filter_condition, result_file", [
        (True, 'watchpoint_handler_get_0.json')
    ])
    def test_get_filter_true(self, filter_condition, result_file):
        """Test get with filter_condition is True."""
        file_path = os.path.join(self.results_dir, result_file)
        with open(file_path, 'r') as f:
            contents = json.load(f)

        reply = self.handler.get(filter_condition)
        protos = reply.get('watch_points')
        for proto in protos:
            msg_dict = json_format.MessageToDict(proto)
            assert msg_dict in contents

    @pytest.mark.parametrize("filter_condition, result_file", [
        (False, 'watchpoint_handler_get_1.json')
    ])
    def test_get_filter_false(self, filter_condition, result_file):
        """Test get with filer_condition is False."""
        file_path = os.path.join(self.results_dir, result_file)
        reply = self.handler.get(filter_condition)
        watch_points = reply.get('watch_points')
        compare_result_with_file(watch_points, file_path)

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
    def test_set_watch_nodes(self, graph_file, watch_point_id):
        """Test set_watch_nodes."""
        path = os.path.join(self.graph_results_dir, graph_file)
        with open(path, 'r') as f:
            graph = json.load(f)
        self.handler.set_watch_nodes(graph, self.graph_stream, watch_point_id)

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
    watchpoint = Watchpoint(
        watch_condition={'condition': 'MAX_GT', 'param': 1},
        watchpoint_id=1
    )
    value = {
        'tensor_proto': mock_tensor_proto(),
        'watchpoint': watchpoint,
        'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92',
        'finished': True,
        'slot': 0
    }

    @classmethod
    def setup_class(cls):
        """Setup."""
        cls.handler = init_watchpoint_hit_handler(cls.value)
        cls.tensor_hist = mock_tensor_history()
        cls.results_dir = os.path.join(os.path.dirname(__file__),
                                       '../expected_results/watchpoint')

    @mock.patch('mindinsight.debugger.stream_cache.watchpoint.WatchpointHit')
    def test_put(self, mock_hit):
        """Test put."""
        mock_hit.return_value = mock.MagicMock(
            tensor_proto=self.value.get('tensor_proto'),
            watchpoint=self.value.get('watchpoint'),
            node_name=self.value.get('node_name')
        )
        WatchpointHitHandler().put(self.value)

    @pytest.mark.parametrize("filter_condition, result_file", [
        (None, "watchpoint_hit_handler_get_0.json"),
        ("Default/network-WithLossCell/_backbone-LeNet5/conv1-Conv2d/Cast-op190",
         "watchpoint_hit_handler_get_1.json")
    ])
    def test_get(self, filter_condition, result_file):
        """Test get."""
        reply = self.handler.get(filter_condition)
        file_path = os.path.join(self.results_dir, result_file)
        compare_result_with_file(reply, file_path)

    def test_update_tensor_history(self):
        """Test update_tensor_history."""
        self.handler.update_tensor_history(self.tensor_hist)
        for tensor_info in self.tensor_hist.get('tensor_history'):
            assert tensor_info['is_hit'] is False


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
