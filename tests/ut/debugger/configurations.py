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
"""Common configurations for debugger unit testing."""
import json
import os

from google.protobuf import json_format

from mindinsight.debugger.stream_handler.graph_handler import GraphHandler, MultiCardGraphHandler
from mindinsight.debugger.stream_handler.watchpoint_handler import WatchpointHitHandler
from mindinsight.domain.graph.proto import ms_graph_pb2
from tests.utils.tools import compare_result_with_file

GRAPH_PROTO_FILE = os.path.join(
    os.path.dirname(__file__), '../../utils/resource/graph_pb/lenet.pb'
)
DEBUGGER_EXPECTED_RESULTS = os.path.join(os.path.dirname(__file__), 'expected_results')


def get_graph_proto():
    """Get graph proto."""
    with open(GRAPH_PROTO_FILE, 'rb') as f:
        content = f.read()

    graph = ms_graph_pb2.GraphProto()
    graph.ParseFromString(content)

    return graph


def init_graph_handler():
    """Init GraphHandler."""
    graph = get_graph_proto()
    graph_handler = GraphHandler()
    graph_handler.put({graph.name: graph})

    return graph_handler


def init_multi_card_graph_handler():
    """Init GraphHandler."""
    graph = get_graph_proto()
    multi_card_graph_handler = MultiCardGraphHandler()
    multi_card_graph_handler.put({0: {graph.name: graph}, 1: {graph.name: graph}})

    return multi_card_graph_handler


def init_watchpoint_hit_handler(values):
    """Init WatchpointHitHandler."""
    wph_handler = WatchpointHitHandler()
    for value in values:
        wph_handler.put(value)

    return wph_handler


def get_node_basic_infos(node_names):
    """Get node info according to node names."""
    if not node_names:
        return []
    graph_stream = init_graph_handler()
    graph_name = graph_stream.graph_names[0]
    node_infos = []
    for node_name in node_names:
        node_infos.append(graph_stream.get_node_basic_info(node_name, graph_name))
    return node_infos


def get_watch_nodes_by_search(watch_nodes):
    """Get watched leaf nodes by search name."""
    watched_leaf_nodes = []
    graph_stream = init_graph_handler()
    graph_name = graph_stream.graph_names[0]
    for search_name in watch_nodes:
        search_node_info = graph_stream.get_node_basic_info_by_scope(search_name, graph_name)
        watched_leaf_nodes.extend(search_node_info)

    return watched_leaf_nodes


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
             "graph_name": "kernel_graph_0",
             "node_type": "TransData",
             "type": "output",
             "step": 0,
             "dtype": "DT_FLOAT32",
             "shape": [2, 3],
             "has_prev_step": False,
             "value": "click to view"},
            {"name": "Default/args0:0",
             "full_name": "Default/args0:0",
             "graph_name": "kernel_graph_0",
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


class WatchpointHit:
    """Watchpoint hit structure."""
    def __init__(self, name, slot, condition, watchpoint_id, parameters, error_code, rank_id, root_graph_id):
        self.name = name
        self.slot = slot
        self.condition = condition
        self.watchpoint_id = watchpoint_id
        self.parameters = parameters
        self.error_code = error_code
        self.rank_id = rank_id
        self.root_graph_id = root_graph_id


def compare_debugger_result_with_file(res, expect_file, save=False):
    """
    Compare debugger result with file.

    Args:
        res (dict): The debugger result in dict type.
        expect_file: The expected file name.
    """
    real_path = os.path.join(DEBUGGER_EXPECTED_RESULTS, expect_file)
    if save:
        with open(real_path, 'w') as file_handler:
            json.dump(res, file_handler)
    else:
        compare_result_with_file(res, real_path)
