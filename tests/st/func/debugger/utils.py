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
from pathlib import Path

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
    debugger_tmp_dir = tempfile.mkdtemp(suffix='debugger_tmp')
    build_dump_structue(debugger_tmp_dir, 'Ascend/async', step_num=3, graph_id=1)
    build_dump_structue(debugger_tmp_dir, 'Ascend/sync', step_num=4, graph_id=0)
    build_dump_structue(debugger_tmp_dir, 'GPU/sync', step_num=3, graph_id=0)
    return debugger_tmp_dir


def build_dump_structue(base_dir, dump_name, step_num, graph_id):
    """Build the dump file structure."""
    dump_dir = os.path.join(base_dir, dump_name)
    gen = DumpStructureGenerator(dump_dir)
    gen.generate(rank_num=2,
                 root_graphs={graph_id: {}},
                 history={},
                 dump_steps={graph_id: list(range(step_num))})


def build_multi_net_dump_structure(dump_name=None):
    """Build the multi-net dump file structure."""
    debugger_tmp_dir = tempfile.mkdtemp(suffix='debugger_tmp')
    dump_dir = os.path.join(debugger_tmp_dir, dump_name) if dump_name else debugger_tmp_dir
    gen = DumpStructureGenerator(dump_dir)
    gen.generate(rank_num=2)
    return debugger_tmp_dir


def write_graph(model, dst_graph_file, graph_name=None, root_name=None):
    """Write graph file."""
    src_graph_proto = model.graph
    if graph_name:
        src_graph_proto.name = graph_name
    if root_name:
        src_graph_proto.root_name = root_name
    dst_graph_str = model.SerializeToString()
    with open(dst_graph_file, 'wb') as file_handler:
        file_handler.write(dst_graph_str)


class DumpStructureGenerator:
    """Generate Dump structure."""

    def __init__(self, dump_dir, sync=True):
        self._dump_dir = Path(dump_dir)
        self._dump_mode = 'sync' if sync else 'async'

    def clean(self):
        """Clean cache."""
        if self._dump_dir.is_dir():
            shutil.rmtree(self._dump_dir)

    def generate(self, root_graphs=None, rank_num=1, history=None, dump_steps=None):
        """Generate dump structure."""
        for rank_id in range(rank_num):
            rank_dir = self._dump_dir / f'rank_{rank_id}'
            rank_dir.mkdir(parents=True)
            self.generate_dump_metadata(rank_dir, self._dump_mode)
            self.generate_graphs(rank_dir, root_graphs)
            self.generate_execution(rank_dir, history)
            self.generate_dump_steps(rank_dir, dump_steps)

    @staticmethod
    def generate_dump_metadata(rank_dir, dump_mode):
        """Generate .dump_metadata dir."""
        temp_metadata_dir = os.path.join(os.path.dirname(__file__), 'dump_files',
                                         'Ascend', dump_mode, 'rank_0', '.dump_metadata')
        shutil.copytree(temp_metadata_dir, rank_dir / '.dump_metadata')

    @staticmethod
    def generate_graphs(rank_dir, root_graphs):
        """Generate graph dir."""
        if root_graphs is None:
            root_graphs = {0: {'graph_name': 'kernel_graph_0',
                               'sub_graph_names': ['kernel_graph_1', 'kernel_graph_2']},
                           3: {'graph_name': 'kernel_graph_3'}}
        graph_dir = rank_dir / 'graphs'
        graph_dir.mkdir()
        with open(GRAPH_PROTO_FILE, 'rb') as file_handler:
            content = file_handler.read()
        model = ms_graph_pb2.ModelProto()
        model.graph.ParseFromString(content)
        # if graph_num is greater than 1, all graphs except last one are belong to root graph 0.
        for graph_id, root_graph in root_graphs.items():
            graph_file = graph_dir / f'ms_output_trace_code_graph_{graph_id}.pb'
            if root_graph:
                write_graph(model, graph_file, root_graph.get('graph_name'), str(graph_id))
                for sub_graph_name in root_graph.get('sub_graph_names', []):
                    sub_graph_id = sub_graph_name.split('_')[-1]
                    graph_file = graph_dir / f'ms_output_trace_code_graph_{sub_graph_id}.pb'
                    write_graph(model, graph_file, sub_graph_name, str(graph_id))
            else:
                write_graph(model, graph_file)

    @staticmethod
    def generate_execution(rank_dir, history):
        """Generate execution directory."""
        if history is None:
            history = {0: [0, 2, 4],
                       3: [1, 3, 5, 6]}
        exec_dir = rank_dir / 'execution_order'
        exec_dir.mkdir()
        for graph_id, exec_counts in history.items():
            file = exec_dir / f'ms_global_execution_order_graph_{graph_id}.csv'
            with open(file, 'w') as handle:
                for count in exec_counts:
                    handle.write(str(count) + '\n')

    @staticmethod
    def generate_dump_steps(rank_dir, dump_steps=None):
        """Generate dump steps."""
        if dump_steps is None:
            dump_steps = {0: [0, 4], 3: [1, 6]}
        net_dir = rank_dir / 'Lenet'
        net_dir.mkdir()
        for graph_id, steps in dump_steps.items():
            graph_dir = net_dir / str(graph_id)
            graph_dir.mkdir()
            for step in steps:
                step_dir = graph_dir / str(step)
                step_dir.mkdir()
