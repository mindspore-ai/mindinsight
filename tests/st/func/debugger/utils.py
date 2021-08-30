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
"""Test debugger server utils."""
import json
import os
import shutil
import tempfile
import time

from mindinsight.domain.graph.proto import ms_graph_pb2
from tests.st.func.debugger.conftest import DEBUGGER_EXPECTED_RESULTS, DEBUGGER_BASE_URL, GRAPH_PROTO_FILE
from tests.utils.tools import compare_result_with_file, get_url


def check_state(app_client, server_state='waiting'):
    """Check if the Server is ready."""
    url = 'retrieve'
    body_data = {'mode': 'all'}
    max_try_times = 30
    count = 0
    flag = False
    while count < max_try_times:
        res = get_request_result(app_client, url, body_data)
        state = res.get('metadata', {}).get('state')
        if state == server_state:
            flag = True
            break
        count += 1
        time.sleep(0.1)
    assert flag is True


def check_offline_dbg_server_state(app_client, session_id, server_state='waiting'):
    """Check if the Server is ready."""
    url = os.path.join(os.path.join('/v1/mindinsight/debugger/sessions/', session_id), 'retrieve')
    body_data = {'mode': 'all'}
    max_try_times = 30
    count = 0
    flag = False
    while count < max_try_times:
        res = get_request_result(app_client, url, body_data, full_url=True)
        state = res.get('metadata', {}).get('state')
        if state == server_state:
            flag = True
            break
        count += 1
        time.sleep(0.1)
    assert flag is True


def get_request_result(app_client, url, body_data, method='post', expect_code=200, full_url=False):
    """Get request result."""
    if not full_url:
        real_url = os.path.join(DEBUGGER_BASE_URL, url)
    else:
        real_url = url
    if method == 'post':
        response = app_client.post(real_url, data=json.dumps(body_data))
    else:
        real_url = get_url(real_url, body_data)
        response = app_client.get(real_url)
    assert response.status_code == expect_code
    res = response.get_json()
    return res


def send_and_compare_result(app_client, url, body_data, expect_file=None, method='post', full_url=False,
                            expect_file_dir='restful_results'):
    """Send and compare result."""
    res = get_request_result(app_client, url, body_data, method=method, full_url=full_url)
    delete_random_items(res)
    if expect_file:
        real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, expect_file_dir, expect_file)
        compare_result_with_file(res, real_path)


def send_and_save_result(app_client, url, body_data, file_path, method='post', full_url=False,
                         expect_file_dir='restful_results'):
    """Send and save result."""
    res = get_request_result(app_client, url, body_data, method=method, full_url=full_url)
    delete_random_items(res)
    real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, expect_file_dir, file_path)
    json.dump(res, open(real_path, 'w'))


def delete_random_items(res):
    """delete the random items in metadata."""
    if isinstance(res, dict):
        if res.get('metadata'):
            if res['metadata'].get('ip'):
                res['metadata'].pop('ip')
            if res['metadata'].get('pos'):
                res['metadata'].pop('pos')
            if res['metadata'].get('debugger_version') and res['metadata']['debugger_version'].get('mi'):
                res['metadata']['debugger_version'].pop('mi')
                res['metadata']['debugger_version'].pop('ms')
        if res.get('devices'):
            for device in res.get('devices'):
                if device.get('server_ip'):
                    device.pop('server_ip')


def build_dump_file_structure():
    """Build the dump file structure."""
    async_file_structure = {
        "Ascend/async/rank_0": 3,
        "Ascend/async/rank_1": 3
    }

    sync_file_structure = {
        "Ascend/sync/rank_0": 4,
        "Ascend/sync/rank_1": 4,
        "GPU/sync/rank_0": 3,
        "GPU/sync/rank_1": 3
    }

    debugger_tmp_dir = tempfile.mkdtemp(suffix='debugger_tmp')
    dump_files_dir = os.path.join(debugger_tmp_dir, 'dump_files')
    shutil.copytree(os.path.join(os.path.dirname(__file__), 'dump_files'), dump_files_dir)

    for sub_dir, steps in async_file_structure.items():
        for step in range(0, steps):
            os.makedirs(os.path.join(os.path.join(dump_files_dir, sub_dir, 'Lenet/1'), str(step)), exist_ok=True)

    for sub_dir, steps in sync_file_structure.items():
        for step in range(0, steps):
            os.makedirs(os.path.join(os.path.join(dump_files_dir, sub_dir, 'Lenet/0'), str(step)),
                        exist_ok=True)
        graph_dir_path = os.path.join(os.path.join(dump_files_dir, sub_dir), 'graphs')
        os.makedirs(graph_dir_path, exist_ok=True)
        graph_path = os.path.join(graph_dir_path, 'ms_output_trace_code_graph_0.pb')
        with open(GRAPH_PROTO_FILE, 'rb') as file_handler:
            content = file_handler.read()

        model = ms_graph_pb2.ModelProto()
        model.graph.ParseFromString(content)
        model_str = model.SerializeToString()
        with open(graph_path, 'wb') as file_handler:
            file_handler.write(model_str)

    return debugger_tmp_dir, dump_files_dir
