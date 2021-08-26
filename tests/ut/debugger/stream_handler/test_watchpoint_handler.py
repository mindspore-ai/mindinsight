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
    Test query debugger watchpoint handler.
Usage:
    pytest tests/ut/debugger
"""
import json
import os
from unittest import mock, TestCase

import pytest
from google.protobuf import json_format

from mindinsight.debugger.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.stream_cache.watchpoint import Watchpoint
from mindinsight.debugger.stream_handler import MultiCardGraphHandler
from mindinsight.debugger.stream_handler.watchpoint_handler import WatchpointHandler, \
    WatchpointHitHandler, validate_watch_condition, validate_watch_condition_params
from tests.ut.debugger.configurations import init_graph_handler, mock_tensor_proto, \
    mock_tensor_history, get_node_basic_infos, \
    init_watchpoint_hit_handler
from tests.utils.tools import compare_result_with_file


class TestWatchpointHandler:
    """Test WatchpointHandler."""

    @classmethod
    def setup_class(cls):
        """Init WatchpointHandler for watchpoint unittest."""
        cls.results_dir = os.path.join(os.path.dirname(__file__),
                                       '../expected_results/watchpoint')
        cls.graph_results_dir = os.path.join(os.path.dirname(__file__),
                                             '../expected_results/graph')
        cls.multi_graph_stream = MultiCardGraphHandler()
        cls.graph_stream = init_graph_handler()
        cls.multi_graph_stream.register_graph_handler(0, cls.graph_stream)
        cls.conditionmgr = None
        cls.handler = None

    def setup_method(self):
        """Init watchpoint for each unittest."""
        self.conditionmgr = ConditionMgr()
        self.handler = WatchpointHandler()
        self._create_watchpoint()

    def _create_watchpoint(self):
        """Test create_watchpoint."""
        watchpoints = [
            ({'id': 'tensor_too_small', 'params': [{'name': 'max_lt', 'value': 1.0}]}, None, None, 1),
            ({'id': 'tensor_too_small', 'params': [{'name': 'min_lt', 'value': 1.0}]}, ["Default"], None, 2),
            ({'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
             ["Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92"],
             None, 3)
        ]
        for watch_condition, watch_nodes, watch_point_id, expect_new_id in watchpoints:
            watch_nodes = get_node_basic_infos(watch_nodes)
            watch_point_id = self.handler.create_watchpoint(self.conditionmgr, watch_condition, {0: watch_nodes},
                                                            watch_point_id)
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
        watch_nodes = get_node_basic_infos(watch_nodes)
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.update_watchpoint(watch_point_id, watch_nodes, watched)
        TestCase().assertIn(f"DEBUG:debugger.debugger:Update watchpoint {expect_updated_id} in cache.",
                            log_content.output)

    def test_get_pending_commands(self):
        """Test get with filter_condition is True."""
        result_file = 'watchpoint_handler_get_0.json'
        file_path = os.path.join(self.results_dir, result_file)
        with open(file_path, 'r') as file_handler:
            contents = json.load(file_handler)
        protos = self.handler.get_pending_commands(self.multi_graph_stream)
        for proto in protos:
            msg_dict = json_format.MessageToDict(proto)
            msg_dict['watch_nodes_num'] = len(msg_dict.pop('watchNodes', []))
            assert msg_dict in contents

    @pytest.mark.parametrize("filter_condition, result_file", [
        (None, 'watchpoint_handler_get_1.json')
    ])
    def test_get_without_filter(self, filter_condition, result_file):
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
        assert err.value.message == f"ValueError. Invalid watchpoint id: {watchpoint_id}"

    @pytest.mark.parametrize("graph_file, watch_point_id", [
        ('graph_handler_get_3_single_node.json', 4)
    ])
    def test_set_watch_nodes(self, graph_file, watch_point_id):
        """Test set_watch_nodes."""
        path = os.path.join(self.graph_results_dir, graph_file)
        with open(path, 'r') as file_handler:
            graph = json.load(file_handler)
        self.handler.set_watch_nodes(graph, self.graph_stream, watch_point_id)

    @pytest.mark.parametrize(
        "watch_point_id, expect_deleted_ids", [
            (3, 3), (None, 2)
        ])
    def test_delete_watchpoint(self, watch_point_id, expect_deleted_ids):
        """Test delete_watchpoint."""
        self.handler.sync_set_cmd({})
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.delete_watchpoint(watch_point_id)
        TestCase().assertIn(
            f"DEBUG:debugger.debugger:Delete watchpoint {expect_deleted_ids} in cache.",
            log_content.output)

    @pytest.mark.parametrize(
        "watch_point_id, expect_deleted_ids", [
            (3, 3), (2, 2)
        ])
    def test_delete_watchpoint_in_cache(self, watch_point_id,
                                        expect_deleted_ids):
        """Test delete_watchpoint."""
        for _ in range(watch_point_id):
            self.handler.create_watchpoint(self.conditionmgr,
                                           {'id': 'tensor_too_small', 'params': [{'name': 'max_lt', 'value': 1.0}]})
        with TestCase().assertLogs(logger=log, level='DEBUG') as log_content:
            self.handler.delete_watchpoint(watch_point_id)
        TestCase().assertIn(
            f"DEBUG:debugger.debugger:Cancel create watchpoint {expect_deleted_ids} in cache.",
            log_content.output)


class TestWatchpointHitHandler:
    """Test WatchpointHitHandler."""
    watchpoint1 = Watchpoint(
        watch_condition={'condition': 'MAX_GT', 'param': 1},
        watchpoint_id=1
    )
    value1 = {
        'tensor_proto': mock_tensor_proto(),
        'watchpoint': watchpoint1,
        'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op96',
        'graph_name': 'kernel_graph_1',
    }
    watchpoint2 = Watchpoint(
        watch_condition={'condition': 'MIN_LT', 'param': 1},
        watchpoint_id=2
    )
    value2 = {
        'tensor_proto': mock_tensor_proto(),
        'watchpoint': watchpoint2,
        'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92',
        'graph_name': 'kernel_graph_0',
    }
    values = [value1, value2]

    @classmethod
    def setup_class(cls):
        """Setup."""
        cls.handler = init_watchpoint_hit_handler(cls.values)
        cls.tensor_hist = mock_tensor_history()
        cls.results_dir = os.path.join(os.path.dirname(__file__),
                                       '../expected_results/watchpoint')

    @mock.patch('mindinsight.debugger.stream_cache.watchpoint.WatchpointHit')
    def test_put(self, mock_hit):
        """Test put."""
        for value in self.values:
            mock_hit.return_value = mock.MagicMock(
                tensor_proto=value.get('tensor_proto'),
                watchpoint=value.get('watchpoint'),
                node_name=value.get('node_name')
            )
            WatchpointHitHandler().put(value)

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

    @pytest.mark.parametrize("group_condition, result_file", [
        ({'limit': 5}, "watchpoint_hit_handler_group_by_None.json"),
        ({'limit': 5, 'graph_id': 'kernel_graph_0'}, "watchpoint_hit_handler_group_by_graph.json"),
        ({'limit': 5, 'watchpoint_id': 2}, "watchpoint_hit_handler_group_by_watchpoint.json"),
        ({'limit': 1, 'focused_node': {'graph_name': 'kernel_graph_1',
                                       'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU'
                                                    '/gradReLU/ReluGradV2-op96'}},
         "watchpoint_hit_group_focused_node_0.json"),
        ({'limit': 1, 'watchpoint_id': 1,
          'focused_node': {'graph_name': 'kernel_graph_1',
                           'node_name': 'Gradients/Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU'
                                        '/ReluGradV2-op96'}},
         "watchpoint_hit_group_focused_node_1.json")
    ])
    def test_group_by(self, group_condition, result_file):
        """Test group watchpointhits by group_condition"""
        reply = self.handler.group_by(group_condition)
        file_path = os.path.join(self.results_dir, result_file)
        compare_result_with_file(reply, file_path)


def test_validate_watch_condition_type_error():
    """Test validate_watch_condition."""
    watch_condition = []
    conditionmgr = ConditionMgr()
    with pytest.raises(DebuggerParamTypeError) as err:
        validate_watch_condition(conditionmgr, watch_condition)
    assert err.value.error_code == '5054B080'

    watch_condition = {'watch_condition': {'condition': 'MAXIMUM'}}
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition(conditionmgr, watch_condition)
    assert err.value.error_code == '5054B081'


def test_validate_watch_condition_params_except():
    """Test validate_watch_condition_params."""
    watch_condition = {'id': 'weight_overflow', 'params': [{'name': 'param', 'value': 0}]}
    conditionmgr = ConditionMgr()
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition_params(conditionmgr, watch_condition)
    assert err.value.error_code == '5054B081'

    watch_condition = {'id': 'tensor_overflow', 'params': [{'name': 'param', 'value': '0'}]}
    with pytest.raises(DebuggerParamValueError) as err:
        validate_watch_condition_params(conditionmgr, watch_condition)
    assert err.value.error_code == '5054B081'
