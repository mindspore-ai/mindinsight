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
Function:
    Test query debugger restful api.
Usage:
    pytest tests/st/func/debugger/test_restful_api.py
"""
import os
import time
from urllib.parse import quote

import pytest

from mindinsight.conf import settings
from mindinsight.debugger.common.utils import ServerStatus
from tests.st.func.debugger.conftest import DEBUGGER_BASE_URL
from tests.st.func.debugger.mock_ms_client import MockDebuggerClient
from tests.st.func.debugger.utils import check_state, get_request_result, \
    send_and_compare_result, send_and_save_result


def send_terminate_cmd(app_client):
    """Send terminate command to debugger client."""
    url = os.path.join(DEBUGGER_BASE_URL, 'control')
    body_data = {'mode': 'terminate'}
    send_and_compare_result(app_client, url, body_data)


class TestAscendDebugger:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.save_results = False
        cls._debugger_client = MockDebuggerClient(backend='Ascend')

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
            'single_node': True}}, 'retrieve_single_node.json')
    ])
    def test_retrieve_when_train_begin(self, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        url = 'retrieve'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)

    def test_get_conditions(self, app_client):
        """Test get conditions for ascend."""
        url = '/v1/mindinsight/debugger/sessions/0/condition-collections'
        body_data = {}
        expect_file = 'get_conditions_for_ascend.json'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='get', full_url=True)
            send_and_compare_result(app_client, url, body_data, expect_file, method='get', full_url=True)
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'mode': 'all'}, 'multi_retrieve_all.json'),
        ({'mode': 'node', 'params': {'name': 'Default', 'graph_name': 'graph_1'}}, 'retrieve_scope_node.json'),
        ({'mode': 'node', 'params': {'name': 'graph_0'}}, 'multi_retrieve_scope_node.json'),
        ({'mode': 'node', 'params': {'name': 'graph_0/Default/optimizer-Momentum/Parameter[18]_7'}},
         'multi_retrieve_aggregation_scope_node.json'),
        ({'mode': 'node', 'params': {
            'name': 'graph_0/Default/TransData-op99',
            'single_node': True}}, 'multi_retrieve_single_node.json'),
        ({'mode': 'node', 'params': {
            'name': 'Default/TransData-op99',
            'single_node': True, 'graph_name': 'graph_0'}}, 'retrieve_single_node.json')
    ])
    def test_multi_retrieve_when_train_begin(self, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        url = 'retrieve'
        debugger_client = MockDebuggerClient(backend='Ascend', graph_num=2)
        with debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_create_and_delete_watchpoint(self, app_client):
        """Test create and delete watchpoint."""
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            conditions = [
                {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
                {'id': 'tensor_too_small', 'params': [{'name': 'max_lt', 'value': -1.0}]},
                {'id': 'tensor_too_large', 'params': [{'name': 'min_gt', 'value': 1e+32}]},
                {'id': 'tensor_too_small', 'params': [{'name': 'min_lt', 'value': -1e+32}]},
                {'id': 'tensor_too_large', 'params': [{'name': 'mean_gt', 'value': 0}]},
                {'id': 'tensor_too_small', 'params': [{'name': 'mean_lt', 'value': 0}]}
            ]
            for idx, condition in enumerate(conditions):
                create_watchpoint(app_client, condition, idx + 1)
            # delete 4-th watchpoint
            url = 'delete-watchpoint'
            body_data = {'watch_point_id': 4}
            get_request_result(app_client, url, body_data)
            # test watchpoint list
            url = 'retrieve'
            body_data = {'mode': 'watchpoint'}
            expect_file = 'create_and_delete_watchpoint.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)

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
            check_state(app_client)
            condition = {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]}
            create_watchpoint(app_client, condition, watch_point_id)
            # update watchpoint watchpoint list
            url = 'update-watchpoint'
            body_data = {'watch_point_id': watch_point_id,
                         'watch_nodes': [leaf_node_name],
                         'mode': 1}
            get_request_result(app_client, url, body_data)
            # get updated nodes
            url = 'search'
            body_data = {'name': leaf_node_name, 'watch_point_id': watch_point_id}
            expect_file = 'search_unwatched_leaf_node.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='get')
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_retrieve_tensor_history(self, app_client):
        """Test retrieve tensor value."""
        node_name = 'Default/TransData-op99'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            # prepare tensor value
            url = 'tensor-history'
            body_data = {'name': node_name, 'rank_id': 0}
            expect_file = 'retrieve_empty_tensor_history.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            # check full tensor history from poll data
            res = get_request_result(
                app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name, 'Node name unmatched.'
            expect_file = 'retrieve_full_tensor_history.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)

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
            check_state(app_client)
            # prepare tensor value
            url = 'tensor-history'
            body_data = {'name': node_name, 'rank_id': 0}
            get_request_result(app_client, url, body_data, method='post')
            get_request_result(app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            url = 'tensors'
            body_data = {
                'name': node_name + ':0',
                'detail': 'data',
                'shape': quote('[1, 1:3]')
            }
            get_request_result(app_client, url, body_data, method='GET')
            # sleep 0.01 second to  wait the tensor update.
            time.sleep(0.01)
            res = get_request_result(
                app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name, 'Node name unmatched.'
            expect_file = 'retrieve_tensor_value.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='get')
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            send_terminate_cmd(app_client)

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
            check_state(app_client)
            # prepare tensor values
            url = 'control'
            body_data = {'mode': 'continue',
                         'steps': 2}
            get_request_result(app_client, url, body_data)
            check_state(app_client)
            get_request_result(
                app_client=app_client, url='tensor-history', body_data={'name': node_name, 'rank_id': 0})
            res = get_request_result(
                app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name, 'Node name unmatched.'
            # get compare results
            url = 'tensor-comparisons'
            body_data = {
                'name': node_name + ':0',
                'detail': 'data',
                'shape': quote('[:, :]'),
                'tolerance': 1,
                'rank_id': 0}
            get_request_result(app_client, url, body_data, method='GET')
            # sleep 0.01 second to  wait the tensor update.
            time.sleep(0.01)
            res = get_request_result(
                app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('node_name') == node_name, 'Node name unmatched.'
            expect_file = 'compare_tensors.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='get')
            send_and_compare_result(app_client, url, body_data, expect_file, method='get')
            send_terminate_cmd(app_client)


    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_pause(self, app_client):
        """Test pause the training."""
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            # send run command to execute to next node
            url = 'control'
            body_data = {'mode': 'continue',
                         'steps': -1}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'sending', 'enable_recheck': False}}
            # send pause command
            check_state(app_client, 'running')
            url = 'control'
            body_data = {'mode': 'pause'}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'sending', 'enable_recheck': False}}
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("url, body_data, enable_recheck", [
        ('create-watchpoint',
         {'condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
          'watch_nodes': ['Default']}, True),
        ('update-watchpoint',
         {'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum/Parameter[18]_7'],
          'mode': 1}, True),
        ('update-watchpoint',
         {'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum'],
          'mode': 1}, True),
        ('delete-watchpoint', {}, True)
    ])
    def test_recheck(self, app_client, url, body_data, enable_recheck):
        """Test recheck."""
        with self._debugger_client.get_thread_instance():
            create_watchpoint_and_wait(app_client)
            # create watchpoint
            res = get_request_result(app_client, url, body_data, method='post')
            assert res['metadata']['enable_recheck'] is enable_recheck
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_recommend_watchpoints(self, app_client):
        """Test generating recommended watchpoints."""
        original_value = settings.ENABLE_RECOMMENDED_WATCHPOINTS
        settings.ENABLE_RECOMMENDED_WATCHPOINTS = True
        try:
            with self._debugger_client.get_thread_instance():
                check_state(app_client)
                url = 'retrieve'
                body_data = {'mode': 'watchpoint'}
                expect_file = 'recommended_watchpoints_at_startup.json'
                send_and_compare_result(app_client, url, body_data, expect_file, method='post')
                send_terminate_cmd(app_client)
        finally:
            settings.ENABLE_RECOMMENDED_WATCHPOINTS = original_value

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'tensor_name': 'Default/TransData-op99:0', 'graph_name': 'graph_0'}, 'retrieve_tensor_graph-0.json'),
        ({'tensor_name': 'Default/optimizer-Momentum/Parameter[18]_7/moments.fc1.bias:0', 'graph_name': 'graph_0'},
         'retrieve_tensor_graph-1.json')
    ])
    def test_retrieve_tensor_graph(self, app_client, body_data, expect_file):
        """Test retrieve tensor graph."""
        url = 'tensor-graphs'
        with self._debugger_client.get_thread_instance():
            create_watchpoint_and_wait(app_client)
            get_request_result(app_client, url, body_data, method='GET')
            # sleep 0.01 second to  wait the tensor update.
            time.sleep(0.01)
            # check full tensor history from poll data
            res = get_request_result(
                app_client=app_client, url='poll-data', body_data={'pos': 0}, method='get')
            assert res.get('receive_tensor', {}).get('tensor_name') == body_data.get('tensor_name')
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='GET')
            send_and_compare_result(app_client, url, body_data, expect_file, method='GET')
            send_terminate_cmd(app_client)


class TestGPUDebugger:
    """Test debugger on Ascend backend."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.save_results = False
        cls._debugger_client = MockDebuggerClient(backend='GPU')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_next_node_on_gpu(self, app_client):
        """Test get next node on GPU."""
        gpu_debugger_client = MockDebuggerClient(backend='GPU')
        check_state(app_client, 'pending')
        with gpu_debugger_client.get_thread_instance():
            check_state(app_client)
            # send run command to get watchpoint hit
            url = 'control'
            body_data = {'mode': 'continue',
                         'level': 'node',
                         'name': 'Default/TransData-op99'}
            res = get_request_result(app_client, url, body_data)
            assert res == {'metadata': {'state': 'sending', 'enable_recheck': False}}
            # get metadata
            check_state(app_client)
            url = 'retrieve'
            body_data = {'mode': 'all'}
            expect_file = 'retrieve_next_node_on_gpu.json'
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("url, body_data, enable_recheck", [
        ('create-watchpoint',
         {'condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
          'watch_nodes': ['Default']}, True),
        ('create-watchpoint',
         {'condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
          'watch_nodes': ['Default/TransData-op99']}, True),
        ('update-watchpoint',
         {'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum/Parameter[18]_7'],
          'mode': 1}, True),
        ('update-watchpoint',
         {'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum'],
          'mode': 1}, True),
        ('update-watchpoint',
         [{'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum'],
           'mode': 1},
          {'watch_point_id': 1, 'watch_nodes': ['Default/optimizer-Momentum'],
           'mode': 0}
          ], True),
        ('update-watchpoint',
         [{'watch_point_id': 1, 'watch_nodes': ['Default/TransData-op99'],
           'mode': 1},
          {'watch_point_id': 1, 'watch_nodes': ['Default/TransData-op99'],
           'mode': 0}
          ], True),
        ('delete-watchpoint', {'watch_point_id': 1}, True)
    ])
    def test_recheck_state(self, app_client, url, body_data, enable_recheck):
        """Test update watchpoint and check the value of enable_recheck."""
        with self._debugger_client.get_thread_instance():
            create_watchpoint_and_wait(app_client)
            if not isinstance(body_data, list):
                body_data = [body_data]
            for sub_body_data in body_data:
                res = get_request_result(app_client, url, sub_body_data, method='post')
            assert res['metadata']['enable_recheck'] is enable_recheck
            send_terminate_cmd(app_client)

    def test_get_conditions(self, app_client):
        """Test get conditions for gpu."""
        url = '/v1/mindinsight/debugger/sessions/0/condition-collections'
        body_data = {}
        expect_file = 'get_conditions_for_gpu.json'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='get', full_url=True)
            send_and_compare_result(app_client, url, body_data, expect_file, method='get', full_url=True)
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_recheck(self, app_client):
        """Test recheck request."""
        with self._debugger_client.get_thread_instance():
            create_watchpoint_and_wait(app_client)
            # send recheck when disable to do recheck
            get_request_result(app_client, 'recheck', {}, method='post', expect_code=400)
            # send recheck when enable to do recheck
            create_watchpoint(app_client, {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]}, 2)
            res = get_request_result(app_client, 'recheck', {}, method='post')
            assert res['metadata']['enable_recheck'] is False

            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("filter_condition, expect_file", [
        ({'name': 'fc', 'node_category': 'weight'}, 'search_weight.json'),
        ({'name': 'fc', 'node_category': 'gradient'}, 'search_gradient.json'),
        ({'node_category': 'activation'}, 'search_activation.json')
    ])
    def test_search_by_category(self, app_client, filter_condition, expect_file):
        """Test recheck request."""
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            send_and_compare_result(app_client, 'search', filter_condition, expect_file,
                                    method='get')
            send_terminate_cmd(app_client)


class TestMultiGraphDebugger:
    """Test debugger on Ascend backend for multi_graph."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.save_results = False
        cls._debugger_client = MockDebuggerClient(backend='Ascend', graph_num=2)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'mode': 'all'}, 'multi_retrieve_all.json'),
        ({'mode': 'node', 'params': {'name': 'Default', 'graph_name': 'graph_1'}}, 'retrieve_scope_node.json'),
        ({'mode': 'node', 'params': {'name': 'graph_0'}}, 'multi_retrieve_scope_node.json'),
        ({'mode': 'node', 'params': {'name': 'graph_0/Default/optimizer-Momentum/Parameter[18]_7'}},
         'multi_retrieve_aggregation_scope_node.json'),
        ({'mode': 'node', 'params': {
            'name': 'graph_0/Default/TransData-op99',
            'single_node': True}}, 'multi_retrieve_single_node.json'),
        ({'mode': 'node', 'params': {
            'name': 'Default/TransData-op99',
            'single_node': True, 'graph_name': 'graph_0'}}, 'retrieve_single_node.json')
    ])
    def test_multi_retrieve_when_train_begin(self, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        url = 'retrieve'
        check_state(app_client, 'pending')
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)


    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("filter_condition, expect_file", [
        ({'name': '', 'node_category': 'weight'}, 'search_weight_multi_graph.json'),
        ({'node_category': 'activation'}, 'search_activation_multi_graph.json'),
        ({'node_category': 'gradient'}, 'search_gradient_multi_graph.json')
    ])
    def test_search_by_category_with_multi_graph(self, app_client, filter_condition, expect_file):
        """Test search by category request."""
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, 'search', filter_condition, expect_file, method='get')
            send_and_compare_result(app_client, 'search', filter_condition, expect_file, method='get')
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("filter_condition, expect_id", [
        ({'condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
          'watch_nodes': ['Default/optimizer-Momentum/Parameter[18]_7'],
          'graph_name': 'graph_0'}, 1),
        ({'condition': {'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
          'watch_nodes': ['graph_0/Default/optimizer-Momentum/ApplyMomentum[8]_1'],
          'graph_name': None}, 1)
    ])
    def test_create_watchpoint(self, app_client, filter_condition, expect_id):
        """Test create watchpoint with multiple graphs."""
        url = 'create-watchpoint'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            res = get_request_result(app_client, url, filter_condition)
            assert res.get('id') == expect_id
            send_terminate_cmd(app_client)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("params, expect_file", [
        ({'level': 'node'}, 'multi_next_node.json'),
        ({'level': 'node', 'node_name': 'graph_0/Default/TransData-op99'}, 'multi_next_node.json'),
        ({'level': 'node', 'node_name': 'Default/TransData-op99', 'graph_name': 'graph_0'},
         'multi_next_node.json')
    ])
    def test_continue_on_gpu(self, app_client, params, expect_file):
        """Test get next node on GPU."""
        gpu_debugger_client = MockDebuggerClient(backend='GPU', graph_num=2)
        original_value = settings.ENABLE_RECOMMENDED_WATCHPOINTS
        settings.ENABLE_RECOMMENDED_WATCHPOINTS = True
        try:
            with gpu_debugger_client.get_thread_instance():
                check_state(app_client)
                # send run command to get watchpoint hit
                url = 'control'
                body_data = {'mode': 'continue'}
                body_data.update(params)
                res = get_request_result(app_client, url, body_data)
                assert res == {'metadata': {'state': 'sending', 'enable_recheck': False}}
                # get metadata
                check_state(app_client)
                url = 'retrieve'
                body_data = {'mode': 'all'}
                if self.save_results:
                    send_and_save_result(app_client, url, body_data, expect_file)
                send_and_compare_result(app_client, url, body_data, expect_file)
                send_terminate_cmd(app_client)
        finally:
            settings.ENABLE_RECOMMENDED_WATCHPOINTS = original_value

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'tensor_name': 'Default/TransData-op99:0', 'graph_name': 'graph_0'}, 'retrieve_tensor_hits-0.json'),
        ({'tensor_name': 'Default/optimizer-Momentum/Parameter[18]_7/moments.fc1.bias:0', 'graph_name': 'graph_0'},
         'retrieve_tensor_hits-1.json')
    ])
    def test_retrieve_tensor_hits(self, app_client, body_data, expect_file):
        """Test retrieve tensor graph."""
        url = 'tensor-hits'
        with self._debugger_client.get_thread_instance():
            check_state(app_client)
            if self.save_results:
                send_and_save_result(app_client, url, body_data, expect_file, method='GET')
            send_and_compare_result(app_client, url, body_data, expect_file, method='GET')
            send_terminate_cmd(app_client)


def create_watchpoint(app_client, condition, expect_id):
    """Create watchpoint."""
    url = 'create-watchpoint'
    body_data = {'condition': condition,
                 'watch_nodes': ['Default/optimizer-Momentum/Parameter[18]_7',
                                 'Default/optimizer-Momentum/Parameter[18]_7/moments.fc3.bias',
                                 'Default/optimizer-Momentum/Parameter[18]_7/moments.fc1.bias',
                                 'Default/TransData-op99']}
    res = get_request_result(app_client, url, body_data)
    assert res.get('id') == expect_id


def create_watchpoint_and_wait(app_client):
    """Preparation for recheck."""
    check_state(app_client)
    create_watchpoint(app_client, condition={'id': 'tensor_too_large', 'params': [{'name': 'max_gt', 'value': 1.0}]},
                      expect_id=1)
    # send run command to get watchpoint hit
    url = 'control'
    body_data = {'mode': 'continue',
                 'steps': 2}
    res = get_request_result(app_client, url, body_data)
    assert res == {'metadata': {'state': 'sending', 'enable_recheck': False}}
    # wait for server has received watchpoint hit
    check_state(app_client)


class TestMismatchDebugger:
    """Test debugger when Mindinsight and Mindspore is mismatched."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls._debugger_client = MockDebuggerClient(backend='Ascend', ms_version='1.0.0')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("body_data, expect_file", [
        ({'mode': 'all'}, 'version_mismatch.json')
    ])
    def test_retrieve_when_version_mismatch(self, app_client, body_data, expect_file):
        """Test retrieve when train_begin."""
        url = 'retrieve'
        with self._debugger_client.get_thread_instance():
            check_state(app_client, ServerStatus.MISMATCH.value)
            send_and_compare_result(app_client, url, body_data, expect_file)
            send_terminate_cmd(app_client)
