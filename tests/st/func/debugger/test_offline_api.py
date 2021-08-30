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
"""Test DataLoader of offline debugger."""
import os
import time
from unittest import mock

import pytest

from mindinsight.debugger.debugger_services.debugger_offline_server import DebuggerOfflineManager
from mindinsight.conf import settings
from tests.st.func.debugger.utils import check_offline_dbg_server_state, get_request_result, \
    build_dump_file_structure, send_and_compare_result
from tests.st.func.debugger.debugger_services import mock_dbg_services


class TestAscendDebugger:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.save_results = False
        cls.debugger_tmp_dir, cls.dump_files_dir = build_dump_file_structure()
        settings.SUMMARY_BASE_DIR = cls.dump_files_dir
        cls.dump_dir = "./GPU/sync"
        cls.base_url = '/v1/mindinsight/debugger/sessions/'
        cls.expect_file_dir = 'offline_debugger'

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'mode': 'all'}, 'retrieve_all.json'),
        ({'mode': 'node', 'params': {'name': 'Default'}}, 'retrieve_scope_node.json'),
        ({'mode': 'node', 'params': {'name': 'Default/optimizer-Momentum/Parameter[18]_7'}},
         'retrieve_aggregation_scope_node.json'),
        ({'mode': 'node', 'params': {
            'name': 'Default/TransData-op99',
            'single_node': True}}, 'retrieve_single_node.json')
    ])
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_retrieve_when_train_begin(self, mock_method, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        session_id = self.create_session(mock_method, app_client)
        url = os.path.join(os.path.join(self.base_url, session_id), 'retrieve')
        check_offline_dbg_server_state(app_client, session_id)
        send_and_compare_result(app_client, url, body_data, expect_file, full_url=True,
                                expect_file_dir=self.expect_file_dir)
        self.stop_session(mock_method, app_client, session_id)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_create_and_delete_watchpoint(self, mock_method, app_client):
        """Test create and delete watchpoint."""
        conditions = [
            {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
            {'id': 'tensor_too_small', 'params': [{'name': 'max_lt', 'value': -1.0}]},
            {'id': 'tensor_too_large', 'params': [{'name': 'min_gt', 'value': 1e+32}]},
            {'id': 'tensor_too_small', 'params': [{'name': 'min_lt', 'value': -1e+32}]},
            {'id': 'tensor_too_large', 'params': [{'name': 'mean_gt', 'value': 0}]},
            {'id': 'tensor_too_small', 'params': [{'name': 'mean_lt', 'value': 0}]}
        ]
        session_id = self.create_session(mock_method, app_client)
        check_offline_dbg_server_state(app_client, session_id)
        for idx, condition in enumerate(conditions):
            self.create_watchpoint(app_client, session_id, condition, idx + 1)
        # delete 4-th watchpoint
        url = os.path.join(os.path.join(self.base_url, session_id), 'delete-watchpoint')
        body_data = {'watch_point_id': 4}
        get_request_result(app_client, url, body_data, full_url=True)
        # test watchpoint list
        url = os.path.join(os.path.join(self.base_url, session_id), 'retrieve')
        body_data = {'mode': 'watchpoint'}
        expect_file = 'create_and_delete_watchpoint.json'
        send_and_compare_result(app_client, url, body_data, expect_file, full_url=True)
        self.stop_session(mock_method, app_client, session_id)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_update_watchpoint(self, mock_method, app_client):
        """Test retrieve when train_begin."""
        watch_point_id = 1
        leaf_node_name = "Default/optimizer-Momentum/ApplyMomentum[8]_1/ApplyMomentum-op56"
        session_id = self.create_session(mock_method, app_client)
        check_offline_dbg_server_state(app_client, session_id)
        condition = {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]}
        self.create_watchpoint(app_client, session_id, condition, watch_point_id)
        # update watchpoint watchpoint list
        url = os.path.join(os.path.join(self.base_url, session_id), 'update-watchpoint')
        body_data = {'watch_point_id': watch_point_id,
                     'watch_nodes': [leaf_node_name],
                     'mode': 1}
        get_request_result(app_client, url, body_data, full_url=True)
        # get updated nodes
        url = os.path.join(os.path.join(self.base_url, session_id), 'search')
        body_data = {'name': leaf_node_name, 'watch_point_id': watch_point_id}
        expect_file = 'search_unwatched_leaf_node.json'
        send_and_compare_result(app_client, url, body_data, expect_file, method='get', full_url=True,
                                expect_file_dir=self.expect_file_dir)
        self.stop_session(mock_method, app_client, session_id)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_retrieve_tensor_history(self, mock_method, app_client):
        """Test retrieve tensor value."""
        node_name = 'Default/TransData-op99'
        session_id = self.create_session(mock_method, app_client)
        # prepare tensor value
        self.run_one_step(app_client, session_id)
        check_offline_dbg_server_state(app_client, session_id)
        tensor_history_url = os.path.join(os.path.join(self.base_url, session_id), 'tensor-history')
        body_data = {'name': node_name, 'rank_id': 0}
        expect_file = 'retrieve_empty_tensor_history.json'
        send_and_compare_result(app_client, tensor_history_url, body_data, expect_file, full_url=True,
                                expect_file_dir=self.expect_file_dir)
        # check full tensor history from poll data
        self.check_poll_data(app_client, session_id, node_name)
        expect_file = 'retrieve_full_tensor_history.json'
        send_and_compare_result(app_client, tensor_history_url, body_data, expect_file, full_url=True,
                                expect_file_dir=self.expect_file_dir)
        self.stop_session(mock_method, app_client, session_id)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_retrieve_tensor_value(self, mock_method, app_client):
        """Test compare tensor value."""
        node_name = 'Default/TransData-op99'
        session_id = self.create_session(mock_method, app_client)
        # prepare tensor value
        self.run_one_step(app_client, session_id)
        self.send_tensor_history(app_client, session_id, node_name)
        # check full tensor history from poll data
        self.check_poll_data(app_client, session_id, node_name)
        url = os.path.join(os.path.join(self.base_url, session_id), 'tensors')
        body_data = {
            'name': node_name + ':0',
            'detail': 'data'
        }
        get_request_result(app_client, url, body_data, method='GET', full_url=True)
        # sleep 0.01 second to  wait the tensor update.
        self.check_poll_data(app_client, session_id, node_name)
        time.sleep(0.1)
        expect_file = 'retrieve_tensor_value.json'
        send_and_compare_result(app_client, url, body_data, expect_file, method='get', full_url=True,
                                expect_file_dir=self.expect_file_dir)
        self.stop_session(mock_method, app_client, session_id)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'tensor_name': 'Default/optimizer-Momentum/ApplyMomentum[8]_1/ApplyMomentum-op25:0',
          'graph_name': 'kernel_graph_0'},
         'retrieve_tensor_graph-0.json')
    ])
    @mock.patch.object(DebuggerOfflineManager, '_get_dbg_service_module')
    def test_retrieve_tensor_graph(self, mock_method, app_client, body_data, expect_file):
        """Test retrieve tensor graph."""
        node_name = 'Default/optimizer-Momentum/ApplyMomentum[8]_1/ApplyMomentum-op25'
        session_id = self.create_session(mock_method, app_client)
        self.run_one_step(app_client, session_id)
        self.send_tensor_history(app_client, session_id, node_name)
        check_offline_dbg_server_state(app_client, session_id)
        url = os.path.join(os.path.join(self.base_url, session_id), 'tensor-graphs')
        get_request_result(app_client, url, body_data, method='GET', full_url=True)
        time.sleep(0.1)
        send_and_compare_result(app_client, url, body_data, expect_file, method='GET', full_url=True,
                                expect_file_dir=self.expect_file_dir)
        self.stop_session(mock_method, app_client, session_id)

    def create_session(self, mock_method, app_client):
        mock_method.return_value = mock_dbg_services
        session_id = get_request_result(app_client=app_client, url='/v1/mindinsight/debugger/sessions',
                                        body_data={
                                            "session_type": "OFFLINE",
                                            "dump_dir": self.dump_dir,
                                        },
                                        method='post', full_url=True)
        return session_id

    def stop_session(self, mock_method, app_client, session_id):
        mock_method.return_value = mock_dbg_services
        url = os.path.join(os.path.join(self.base_url, session_id), 'delete')
        session_id = get_request_result(app_client=app_client, url=url, body_data={}, method='post', full_url=True)
        return session_id

    def create_watchpoint(self, app_client, session_id, condition, expect_id):
        """Create watchpoint."""
        url = os.path.join(os.path.join(self.base_url, session_id), 'create-watchpoint')
        body_data = {'condition': condition,
                     'watch_nodes': ['Default/optimizer-Momentum/ApplyMomentum[8]_1/ApplyMomentum-op25']}
        res = get_request_result(app_client, url, body_data, full_url=True)
        assert res.get('id') == expect_id

    def run_one_step(self, app_client, session_id):
        """Run one step"""
        check_offline_dbg_server_state(app_client, session_id)
        url = os.path.join(os.path.join(self.base_url, session_id), 'control')
        body_data = {'mode': 'continue',
                     'steps': 1}
        get_request_result(app_client, url, body_data, full_url=True)

    def send_tensor_history(self, app_client, session_id, node_name):
        """Send tensor history"""
        check_offline_dbg_server_state(app_client, session_id)
        tensor_history_url = os.path.join(os.path.join(self.base_url, session_id), 'tensor-history')
        body_data = {'name': node_name, 'rank_id': 0}
        get_request_result(app_client, tensor_history_url, body_data, full_url=True)

    def check_poll_data(self, app_client, session_id, node_name):
        """Check poll data"""
        url = os.path.join(os.path.join(self.base_url, session_id), 'poll-data')
        res = get_request_result(
            app_client=app_client, url=url, body_data={'pos': 0}, method='get', full_url=True)
        assert res.get('receive_tensor', {}).get('node_name') == node_name, 'Node name unmatched.'
