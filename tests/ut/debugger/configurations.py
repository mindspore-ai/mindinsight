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
"""Common configurations for debugger unit testing."""
import json
import os

from google.protobuf import json_format

from mindinsight.debugger.proto import ms_graph_pb2
from mindinsight.debugger.stream_handler.graph_handler import GraphHandler

graph_proto_file = os.path.join(
    os.path.dirname(__file__), '../../utils/resource/graph_pb/lenet.pb'
)


def get_graph_proto():
    """Get graph proto."""
    with open(graph_proto_file, 'rb') as f:
        content = f.read()

    graph = ms_graph_pb2.GraphProto()
    graph.ParseFromString(content)

    return graph


def init_graph_handler():
    """Init graph proto."""
    graph = get_graph_proto()
    graph_handler = GraphHandler()
    graph_handler.put(graph)

    return graph_handler


def mock_tensor_proto():
    """Mock tensor proto."""
    tensor_dict = {
        "node_name":
            "Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/gradReLU/ReluGradV2-op92",
        "slot": "0"
    }
    tensor_proto = json_format.Parse(json.dumps(tensor_dict), ms_graph_pb2.TensorProto())

    return tensor_proto


def mock_tensor_history():
    """Mock tensor history."""
    tensor_history = {
        "tensor_history": [
            {"name": "Default/TransData-op99:0",
             "full_name": "Default/TransData-op99:0",
             "node_type": "TransData",
             "type": "output",
             "step": 0,
             "dtype": "DT_FLOAT32",
             "shape": [2, 3],
             "has_prev_step": False,
             "value": "click to view"},
            {"name": "Default/args0:0",
             "full_name": "Default/args0:0",
             "node_type": "Parameter",
             "type": "input",
             "step": 0,
             "dtype": "DT_FLOAT32",
             "shape": [2, 3],
             "has_prev_step": False,
             "value": "click to view"}
        ],
        "metadata": {
            "state": "waiting",
            "step": 0,
            "device_name": "0",
            "pos": "0",
            "ip": "127.0.0.1:57492",
            "node_name": "",
            "backend": "Ascend"
        }
    }

    return tensor_history
