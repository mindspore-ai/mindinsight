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
"""Mocked MindSpore debugger client."""
from threading import Thread
from time import sleep

import grpc
import numpy as np

import mindinsight
from mindinsight.debugger.proto.debug_grpc_pb2 import Metadata, WatchpointHit, Chunk, EventReply
from mindinsight.debugger.proto.debug_grpc_pb2_grpc import EventListenerStub
from mindinsight.domain.graph.proto import ms_graph_pb2
from mindinsight.domain.graph.proto.ms_graph_pb2 import TensorProto, DataType
from tests.st.func.debugger.conftest import GRAPH_PROTO_FILE


class MockDebuggerClient:
    """Mocked Debugger client."""

    def __init__(self, hostname='localhost:50051', backend='Ascend', graph_num=1, ms_version=None):
        channel = grpc.insecure_channel(hostname)
        self.stub = EventListenerStub(channel)
        self.flag = True
        self._step = 0
        self._watchpoint_id = 0
        self._leaf_node = []
        self._cur_node = ''
        self._backend = backend
        self._graph_num = graph_num
        self._ms_version = ms_version if ms_version else mindinsight.__version__

    def _clean(self):
        """Clean cache."""
        self._step = 0
        self._watchpoint_id = 0
        self._leaf_node = []
        self._cur_node = ''

    def get_thread_instance(self):
        """Get debugger client thread."""
        return MockDebuggerClientThread(self)

    def next_node(self, name=None):
        """Update the current node to next node."""
        if not self._cur_node:
            self._cur_node = self._leaf_node[0]
            return
        cur_index = self._leaf_node.index(self._cur_node)
        # if name is not None, go to the specified node.
        if not name:
            next_index = cur_index + 1
        else:
            next_index = self._leaf_node.index(name)
        # update step
        if next_index <= cur_index or next_index == len(self._leaf_node):
            self._step += 1
        # update current node
        if next_index == len(self._leaf_node):
            self._cur_node = self._leaf_node[0]
        else:
            self._cur_node = self._leaf_node[next_index]

    def command_loop(self):
        """Wait for the command."""
        total_steps = 100
        wait_flag = True
        while self.flag and wait_flag:
            if self._step > total_steps:
                sleep(0.5)
                self.send_metadata_cmd(training_done=True)
                return
            wait_flag = self._wait_cmd()

    def _wait_cmd(self):
        """Wait for command and deal with command."""
        metadata = self.get_metadata_cmd()
        response = self.stub.WaitCMD(metadata)
        assert response.status == EventReply.Status.OK
        if response.HasField('run_cmd'):
            self._deal_with_run_cmd(response)
        elif response.HasField('view_cmd'):
            for tensor in response.view_cmd.tensors:
                self.send_tensor_cmd(in_tensor=tensor)
        elif response.HasField('set_cmd'):
            self._watchpoint_id += 1
        elif response.HasField('exit'):
            self._watchpoint_id = 0
            self._step = 0
            return False
        return True

    def _deal_with_run_cmd(self, response):
        self._step += response.run_cmd.run_steps
        if response.run_cmd.run_level == 'node':
            self.next_node(response.run_cmd.node_name)
        if self._watchpoint_id > 0:
            self.send_watchpoint_hit()

    def get_metadata_cmd(self, training_done=False):
        """Construct metadata message."""
        metadata = Metadata()
        metadata.device_name = '0'
        metadata.cur_step = self._step
        metadata.cur_node = self._cur_node
        metadata.backend = self._backend
        metadata.training_done = training_done
        metadata.ms_version = self._ms_version
        return metadata

    def send_metadata_cmd(self, training_done=False):
        """Send metadata command."""
        self._clean()
        metadata = self.get_metadata_cmd(training_done)
        response = self.stub.SendMetadata(metadata)
        assert response.status == EventReply.Status.OK
        if response.HasField('version_matched') and response.version_matched is False:
            self.command_loop()
        if training_done is False:
            self.send_graph_cmd()

    def send_graph_cmd(self):
        """Send graph to debugger server."""
        self._step = 1
        if self._graph_num > 1:
            chunks = []
            for i in range(self._graph_num):
                chunks.extend(self._get_graph_chunks('graph_' + str(i)))
            response = self.stub.SendMultiGraphs(self._generate_graph(chunks))
        else:
            chunks = self._get_graph_chunks()
            response = self.stub.SendGraph(self._generate_graph(chunks))
        assert response.status == EventReply.Status.OK
        # go to command loop
        self.command_loop()

    def _get_graph_chunks(self, graph_name='graph_0'):
        """Get graph chunks."""
        with open(GRAPH_PROTO_FILE, 'rb') as file_handle:
            content = file_handle.read()
        size = len(content)
        graph = ms_graph_pb2.GraphProto()
        graph.ParseFromString(content)
        graph.name = graph_name
        content = graph.SerializeToString()
        self._leaf_node = [node.full_name for node in graph.node]
        # the max limit of grpc data size is 4kb
        # split graph into 3kb per chunk
        chunk_size = 1024 * 1024 * 3
        chunks = []
        for index in range(0, size, chunk_size):
            sub_size = min(chunk_size, size - index)
            sub_chunk = Chunk(buffer=content[index: index + sub_size])
            chunks.append(sub_chunk)
        chunks[-1].finished = True
        return chunks

    @staticmethod
    def _generate_graph(chunks):
        """Construct graph generator."""
        for buffer in chunks:
            yield buffer

    def send_tensor_cmd(self, in_tensor=None):
        """Send tensor info with value."""
        response = self.stub.SendTensors(self.generate_tensor(in_tensor))
        assert response.status == EventReply.Status.OK

    @staticmethod
    def generate_tensor(in_tensor=None):
        """Generate tensor message."""
        tensor_content = np.asarray([1, 2, 3, 4, 5, 6]).astype(np.float32).tobytes()
        tensors = [TensorProto(), TensorProto()]
        tensors[0].CopyFrom(in_tensor)
        tensors[0].data_type = DataType.DT_FLOAT32
        tensors[0].dims.extend([2, 3])
        tensors[1].CopyFrom(tensors[0])
        tensors[0].tensor_content = tensor_content[:12]
        tensors[1].tensor_content = tensor_content[12:]
        tensors[0].finished = 0
        tensors[1].finished = 1
        for sub_tensor in tensors:
            yield sub_tensor

    def send_watchpoint_hit(self):
        """Send watchpoint hit value."""
        tensors = [TensorProto(node_name='Default/TransData-op99', slot='0'),
                   TensorProto(node_name='Default/optimizer-Momentum/ApplyMomentum-op25', slot='0')]
        response = self.stub.SendWatchpointHits(self._generate_hits(tensors))
        assert response.status == EventReply.Status.OK

    @staticmethod
    def _generate_hits(tensors):
        """Construct watchpoint hits."""
        for tensor in tensors:
            hit = WatchpointHit()
            hit.id = 1
            hit.tensor.CopyFrom(tensor)
            yield hit


class MockDebuggerClientThread:
    """Mocked debugger client thread."""
    def __init__(self, debugger_client):
        self._debugger_client = debugger_client
        self._debugger_client_thread = Thread(target=debugger_client.send_metadata_cmd)

    def __enter__(self, backend='Ascend'):
        self._debugger_client.flag = True
        self._debugger_client_thread.start()
        return self._debugger_client_thread

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._debugger_client_thread.join(timeout=2)
        self._debugger_client.flag = False
