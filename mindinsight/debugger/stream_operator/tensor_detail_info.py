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
"""This module is aimed to provide with tensor detail info."""
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import Streams, create_view_event_from_tensor_basic_info


class TensorDetailInfo:
    """Manage tensor detail information."""

    def __init__(self, cache):
        self._put_command = cache.put_command
        self._tensor_stream = cache.get_stream_handler(Streams.TENSOR)
        self._graph_stream = cache.get_stream_handler(Streams.GRAPH)
        self._hit_stream = cache.get_stream_handler(Streams.WATCHPOINT_HIT)

    def validate_tensor_name(self, tensor_name, graph_name):
        """
        Get the graph id of the tensor.

        Args:
            tensor_name (str): The tensor name on UI.
            graph_name (str): The graph name.
        """
        # validate tensor name format
        if not isinstance(tensor_name, str) or ':' not in tensor_name:
            log.error("Invalid tensor name. Received: %s", tensor_name)
            raise DebuggerParamValueError("Invalid tensor name.")
        node_name, _ = tensor_name.rsplit(':', 1)
        # check if the node name is in graph
        self._graph_stream.validate_node_name(node_name=node_name, graph_name=graph_name)

    def get_tensor_graph(self, tensor_name, graph_name):
        """
        Get the graph related to specific tensor.

        Args:
            tensor_name (str): The ui name of tensor. Format like {node_name}:{slot}.
            graph_name (str): The graph name.

        Returns:
            dict, tensor graph, format is {'nodes': [Node object]}.
            The Node object = {
                'graph_name': <graph_name>,
                'name': <node name>,
                'input': {<node name>: <Edge object>},
                'output: {<node name>: <Edge object>},
                'slots': [<Slot object>].
            }
            Edge object = {
                'data_type': <data type>,
                'edge_type': <edge type>,
                'independent_layout': bool,
                'shape': list[<dim>],
                'slot_mapping': list[pair<slot, slot>],
            }.
        """
        self.validate_tensor_name(tensor_name=tensor_name, graph_name=graph_name)
        graph = self._graph_stream.get_tensor_graph(tensor_name, graph_name)
        # add watchpoint hits info and statistics info for each tensor in tensor graph.
        # record missing tensor basic info
        nodes = graph.get('graph', {}).get('nodes', [])
        missing_tensors = []
        for node in nodes:
            node['graph_name'] = graph_name
            for slot_info in node.get('slots', []):
                self._add_watchpoint_hit_info(slot_info, node, graph_name)
                self._add_tensor_info(slot_info, node, missing_tensors)
        # query missing tensor values from client
        self._ask_for_missing_tensor_value(missing_tensors, tensor_name, graph_name)
        return graph

    def _add_watchpoint_hit_info(self, slot_info, node, graph_name):
        """
        Add watchpoint hit info for the tensor.

        Args:
            slot_info (dict): Slot object.
            node (dict): Node object.
            graph_name (str): Graph name.
        """
        tensor_name = ':'.join([node.get('name'), slot_info.get('slot')])
        slot_info.update(self._hit_stream.get_tensor_hit_infos(tensor_name, graph_name))

    def _add_tensor_info(self, slot_info, node, missing_tensors):
        """
        Add the tensor info and query for missed tensors.

        Args:
            slot_info (dict): Slot object.
            node (dict): Node object.
            missing_tensors (list[TensorBasicInfo]): List of missing tensor infos.
        """
        tensor_name = ':'.join([node.get('full_name'), slot_info.get('slot')])
        node_type = node.get('type')
        tensor_info, cur_missing_tensors = self._tensor_stream.get_tensor_info_for_tensor_graph(tensor_name, node_type)
        slot_info.update(tensor_info)
        if cur_missing_tensors:
            log.debug("Get missing tensor basic infos for %s", tensor_name)
            missing_tensors.extend(cur_missing_tensors)

    def _ask_for_missing_tensor_value(self, missing_tensors, tensor_name, graph_name):
        """
        Send view command to client to query for missing tensor values.

        Args:
            missing_tensors (list[TensorBasicInfo]): List of missing tensor basic infos.
            tensor_name (str): The ui name of tensor. Format like {node_name}:{slot}.
            graph_name (str): The graph name.
        """
        if not missing_tensors:
            return
        log.debug("Ask for tensor value for: %s", missing_tensors)
        view_cmd = create_view_event_from_tensor_basic_info(missing_tensors)
        self._put_command({'view_cmd': view_cmd, 'tensor_name': tensor_name, 'graph_name': graph_name})
        log.debug("Send view cmd for tensor-graphs.")

    def get_tensor_watch_points(self, tensor_name, graph_name):
        """
        Get all watchpoints that the tensor hit.

        Args:
            tensor_name (str): Tensor name from UI.
            graph_name (str): The graph name.

        Returns:
            list, watchpoint hit infos.
        """
        # validate tensor_name
        self.validate_tensor_name(tensor_name=tensor_name, graph_name=graph_name)
        # get watchpoint info that the tensor hit
        tensor_hit_info = self._hit_stream.get_tensor_hit_infos(tensor_name, graph_name)
        watch_points = tensor_hit_info.get('watch_points', [])
        return watch_points
