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
    Test query debugger restful api.
Usage:
    pytest tests/st/func/debugger/test_restful_api.py
"""
import os

import pytest

from tests.st.func.debugger.conftest import DEBUGGER_BASE_URL
from tests.st.func.debugger.mock_ms_client import MockDebuggerClient
from tests.st.func.debugger.utils import check_waiting_state, get_request_result, \
    send_and_compare_result


class TestAscendDebugger:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls._debugger_client = MockDebuggerClient(backend='Ascend')

    @staticmethod
    def _send_terminate_cmd(app_client):
        """Send terminate command to debugger client."""
        url = os.path.join(DEBUGGER_BASE_URL, 'control')
        body_data = {'mode': 'terminate'}
        send_and_compare_result(app_client, url, body_data)

    @staticmethod
    def _create_watchpoint(app_client, condition, expect_id):
        """Create watchpoint."""
        url = 'create_watchpoint'
        body_data = {'condition': condition,
                     'watch_nodes': ['Default/optimizer-Momentum/Parameter[18]_7',
                                     'Default/TransData-op99']}
        res = get_request_result(app_client, url, body_data)
        assert res.get('id') == expect_id

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_before_train_begin(self, app_client):
        """Test retrieve all."""
        url = 'retrieve'
        body_data = {'mode': 'all'}
        expect_file = 'before_train_begin.json'
        send_and_compare_result(app_client, url, body_data, expect_file)

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
            'single_node': True}}, 'retrieve_single_node.json'),
        ({'mode': 'watchpoint_hit'}, 'retrieve_empty_watchpoint_hit_list')
    ])
    def test_retrieve_when_train_begin(self, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        url = 'retrieve'
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            send_and_compare_result(app_client, url, body_data, expect_file)
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_create_and_delete_watchpoint(self, app_client):
        """Test create and delete watchpoint."""
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            conditions = [
                {'condition': 'MAX_GT', 'param': 1.0},
                {'condition': 'MAX_LT', 'param': -1.0},
                {'condition': 'MIN_GT', 'param': 1e+32},
                {'condition': 'MIN_LT', 'param': -1e+32},
                {'condition': 'MAX_MIN_GT', 'param': 0},
                {'condition': 'MAX_MIN_LT', 'param': 0},
                {'condition': 'MEAN_GT', 'param': 0},
                {'condition': 'MEAN_LT', 'param': 0},
                {'condition': 'INF'},
                {'condition': 'OVERFLOW'},
            ]
            for idx, condition in enumerate(conditions):
                self._create_watchpoint(app_client, condition, idx + 1)
            # delete 4-th watchpoint
            url = 'delete_watchpoint'
            body_data = {'watch_point_id': 4}
            get_request_result(app_client, url, body_data)
            # test watchpoint list
            url = 'retrieve'
            body_data = {'mode': 'watchpoint'}
            expect_file = 'create_and_delete_watchpoint.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_update_watchpoint(self, app_client):
        """Test retrieve when train_begin."""
        watch_point_id = 1
        leaf_node_name = 'Default/optimizer-Momentum/Parameter[18]_7/moments.fc3.bias'
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            condition = {'condition': 'INF'}
            self._create_watchpoint(app_client, condition, watch_point_id)
            # update watchpoint watchpoint list
            url = 'update_watchpoint'
            body_data = {'watch_point_id': watch_point_id,
                         'watch_nodes': [leaf_node_name],
                         'mode': 0}
            get_request_result(app_client, url, body_data)
            # get updated nodes
            url = 'search'
            body_data = {'name': leaf_node_name, 'watch_point_id': watch_point_id}
            expect_file = 'search_unwatched_leaf_node.json'
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_watchpoint_hit(self, app_client):
        """Test retrieve watchpoint hit."""
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            self._create_watchpoint(app_client, condition={'condition': 'INF'}, expect_id=1)
            # send run command to get watchpoint hit
            url = 'control'
            body_data = {'mode': 'continue',
                         'steps': 2}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'running'}}
            # wait for server has received watchpoint hit
            flag = check_waiting_state(app_client)
            assert flag is True
            # check watchpoint hit list
            url = 'retrieve'
            body_data = {'mode': 'watchpoint_hit'}
            expect_file = 'retrieve_watchpoint_hit.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            # check single watchpoint hit
            body_data = {
                'mode': 'watchpoint_hit',
                'params': {
                    'name': 'Default/TransData-op99',
                    'single_node': True,
                    'watch_point_id': 1
                    }
            }
            expect_file = 'retrieve_single_watchpoint_hit.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_retrieve_tensor_value(self, app_client):
        """Test retrieve tensor value."""
        node_name = 'Default/TransData-op99'
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            # prepare tensor value
            url = 'retrieve_tensor_history'
            body_data = {'name': node_name}
            expect_file = 'retrieve_empty_tensor_history.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            # check full tensor history from poll data
            res = get_request_result(
                app_client=app_client, url='poll_data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name
            expect_file = 'retrieve_full_tensor_history.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            # check tensor value
            url = 'tensors'
            body_data = {
                'name': node_name + ':0',
                'detail': 'data',
                'shape': '[1, 1:3]'
            }
            expect_file = 'retrieve_tensor_value.json'
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_compare_tensor_value(self, app_client):
        """Test compare tensor value."""
        node_name = 'Default/args0'
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            # prepare tensor values
            url = 'control'
            body_data = {'mode': 'continue',
                         'steps': 2}
            get_request_result(app_client, url, body_data)
            flag = check_waiting_state(app_client)
            assert flag is True
            get_request_result(
                app_client=app_client, url='retrieve_tensor_history', body_data={'name': node_name})
            res = get_request_result(
                app_client=app_client, url='poll_data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name
            # get compare results
            url = 'tensor-comparisons'
            body_data = {
                'name': node_name + ':0',
                'detail': 'data',
                'shape': '[:, :]',
                'tolerance': 1
            }
            expect_file = 'compare_tensors.json'
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'ascend': True}, 'retrieve_node_by_bfs_ascend.json'),
        ({'name': 'Default/args0', 'ascend': False}, 'retrieve_node_by_bfs.json')
    ])
    def test_retrieve_bfs_node(self, app_client, body_data, expect_file):
        """Test retrieve bfs node."""
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            # prepare tensor values
            url = 'retrieve_node_by_bfs'
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_next_node_on_gpu(self, app_client):
        """Test get next node on GPU."""
        gpu_debugger_client = MockDebuggerClient(backend='GPU')
        with gpu_debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            # send run command to get watchpoint hit
            url = 'control'
            body_data = {'mode': 'continue',
                         'level': 'node',
                         'name': 'Default/TransData-op99'}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'running'}}
            # get metadata
            flag = check_waiting_state(app_client)
            assert flag is True
            url = 'retrieve'
            body_data = {'mode': 'all'}
            expect_file = 'retrieve_next_node_on_gpu.json'
            send_and_compare_result(app_client, url, body_data, expect_file)
            self._send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_pause(self, app_client):
        """Test pause the training."""
        with self._debugger_client.get_thread_instance():
            flag = check_waiting_state(app_client)
            assert flag is True
            # send run command to execute to next node
            url = 'control'
            body_data = {'mode': 'continue',
                         'steps': -1}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'running'}}
            # send pause command
            url = 'control'
            body_data = {'mode': 'pause'}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'waiting'}}
            self._send_terminate_cmd(app_client)
