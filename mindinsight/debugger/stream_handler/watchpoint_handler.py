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
"""Define the watchpoint stream handler."""
import numpy as np

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.proto.debug_grpc_pb2 import SetCMD
from mindinsight.debugger.stream_cache.watchpoint import Watchpoint, WatchpointHit, \
    WATCHPOINT_CONDITION_MAPPING
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class WatchpointHandler(StreamHandlerBase):
    """watchpoint Handler."""

    def __init__(self):
        self._watchpoints = {}
        self._deleted_watchpoints = []
        self._updated_watchpoints = {}
        self._latest_id = 0

    def put(self, value):
        """
        Put Watchpoint into watchpoint handler.

        Args:
            value (Watchpoint): The name of nodes that have been chosen.
        """
        new_id = value.watchpoint_id
        self._watchpoints[new_id] = value
        self._updated_watchpoints[new_id] = value
        self._latest_id = new_id
        log.debug("Put watchpoint %d into cache.", new_id)

    def sync_set_cmd(self):
        """Clean temp watchpoints."""
        self._deleted_watchpoints = []
        self._updated_watchpoints = {}

    def get_watchpoint_by_id(self, watchpoint_id):
        """Get watchpoint by watchpoint id."""
        watchpoint = self._watchpoints.get(watchpoint_id)
        if not watchpoint:
            log.error("Invalid watchpoint id %d", watchpoint_id)
            raise DebuggerParamValueError("Invalid watchpoint id {}".format(watchpoint_id))

        return watchpoint

    def get(self, filter_condition=False):
        """
        Get the watchpoints.

        Args:
            filter_condition (bool): If True, get all watchpoints without nodes. If False,
                get updated watchpoints in SetCMD proto format. Default: False.

        Returns:
            dict, the watchpoints.
        """
        reply = []
        if not filter_condition:
            # get watch condition list
            for _, watchpoint in self._watchpoints.items():
                watchpoint_info = watchpoint.get_watch_condition_info()
                reply.append(watchpoint_info)
        else:
            # get updated watchpoint list
            for _, watchpoint in self._updated_watchpoints.items():
                set_cmd = watchpoint.get_set_cmd()
                reply.append(set_cmd)
            reply.extend(self._deleted_watchpoints)

        log.debug("get the watch points with filter_condition:%s", filter_condition)

        return {'watch_points': reply}

    def set_watch_nodes(self, graph, watch_point_id):
        """
        set watch nodes for graph.

        Args:
            graph (dict): The graph with list of nodes.
            watch_point_id (int): The id of watchpoint.
        """
        if not (watch_point_id and graph):
            return
        self._validate_watchpoint_id(watch_point_id)
        log.debug("add watch flags")
        watchpoint = self._watchpoints.get(watch_point_id)
        self._set_watch_status_recursively(graph, watchpoint)

    def _set_watch_status_recursively(self, graph, watchpoint):
        """Set watch status to graph."""
        if not isinstance(graph, dict):
            log.warning("The graph is not dict.")
            return
        if graph.get('children'):
            self._set_watch_status_recursively(graph.get('children'), watchpoint)

        for node in graph.get('nodes', []):
            if not isinstance(node, dict):
                log.warning("The node is not dict.")
                return
            node_name = node.get('name')
            if not node_name:
                continue
            flag = watchpoint.get_node_status(node_name, node.get('type'), node.get('full_name'))
            node['watched'] = flag
            if node.get('nodes'):
                self._set_watch_status_recursively(node, watchpoint)

    def create_watchpoint(self, watch_condition, watch_nodes=None, watch_point_id=None):
        """
        Create watchpoint.
        Args:
            watch_condition (dict): The watch condition.

                - condition (str): Accept `INF` or `NAN`.

                - param (list[float]): Not defined yet.
            watch_nodes (list[NodeBasicInfo]): The list of node basic info.
            watch_point_id (int): The id of watchpoint.

        Returns:
            int, the new id of watchpoint.
        """
        validate_watch_condition(watch_condition)
        new_id = self._latest_id + 1
        watchpoint = Watchpoint(new_id, watch_condition)
        if watch_nodes:
            watchpoint.add_nodes(watch_nodes)
        elif watch_point_id:
            self._validate_watchpoint_id(watch_point_id)
            watchpoint.copy_nodes_from(self._watchpoints.get(watch_point_id))
        self.put(watchpoint)

        return new_id

    def update_watchpoint(self, watch_point_id, watch_nodes, watched=False):
        """
        Update watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.
            watch_nodes (list[str]): The list of node names.
            watched (bool): The update operator on nodes. If False, remove nodes from watch nodes.
                If True, add nodes to watch nodes. Default: False.

        Returns:
            dict, empty response.
        """
        self._validate_watchpoint_id(watch_point_id)
        watchpoint = self._watchpoints.get(watch_point_id)
        if watched:
            watchpoint.add_nodes(watch_nodes)
        else:
            watchpoint.remove_nodes(watch_nodes)
        self._updated_watchpoints[watch_point_id] = watchpoint
        log.debug("Update watchpoint %d in cache.", watch_point_id)

    def delete_watchpoint(self, watch_point_id):
        """
        Delete watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.

        Returns:
            dict, empty response.
        """
        self._validate_watchpoint_id(watch_point_id)
        self._watchpoints.pop(watch_point_id)
        set_cmd = SetCMD()
        set_cmd.id = watch_point_id
        set_cmd.delete = True
        self._deleted_watchpoints.append(set_cmd)
        log.debug("Delete watchpoint %d in cache.", watch_point_id)

    def _validate_watchpoint_id(self, watch_point_id):
        """Validate watchpoint id."""
        if watch_point_id and watch_point_id not in self._watchpoints:
            log.error("Invalid watchpoint id: %d.", watch_point_id)
            raise DebuggerParamValueError("Invalid watchpoint id: {}".format(watch_point_id))


class WatchpointHitHandler(StreamHandlerBase):
    """Watchpoint hit handler."""

    def __init__(self):
        self._hits = {}

    def put(self, value):
        """
        Put value into watchpoint hit cache. Called by grpc server.

        Args:
            value (dict): The watchpoint hit info.

                - tensor_proto (TensorProto): The message about hit tensor.

                - watchpoint (Watchpoint): The Watchpoint that a node hit.
        """
        watchpoint_hit = WatchpointHit(
            tensor_proto=value.get('tensor_proto'),
            watchpoint=value.get('watchpoint'),
            node_name=value.get('node_name')
        )

        node_name = value.get('node_name')
        hit_tensors = self._hits.get(node_name)
        if hit_tensors is None:
            hit_tensors = []
            self._hits[node_name] = hit_tensors
        if watchpoint_hit not in hit_tensors:
            hit_tensors.append(watchpoint_hit)

    def get(self, filter_condition=None):
        """
        Get watchpoint hit list.

        Args:
            filter_condition (str): Get the watchpoint hit according to specifiled node name.
                If not given, get all watchpoint hits. Default: None.

        Returns:
            dict, the watchpoint hit list.
        """
        if filter_condition is None:
            log.debug("Get all watchpoint hit list.")
            reply = self.get_watchpoint_hits()
        else:
            log.debug("Get the watchpoint for node: <%s>.", filter_condition)
            reply = self._hits.get(filter_condition)

        return reply

    def get_watchpoint_hits(self):
        """Return the list of watchpoint hits."""
        watch_point_hits = []
        for node_name, watchpoint_hits in self._hits.items():
            watch_points = [watchpoint_hit.watchpoint for watchpoint_hit in watchpoint_hits]
            watch_point_hits.append({
                'node_name': node_name,
                'watch_points': watch_points
            })

        return {'watch_point_hits': watch_point_hits}

    def _is_tensor_hit(self, tensor_name):
        """Check if the tensor is record in hit cache."""
        node_name = tensor_name.split(':')[0]
        watchpoint_hits = self.get(node_name)
        if watchpoint_hits is None:
            return False

        for watchpoint_hit in watchpoint_hits:
            if tensor_name == watchpoint_hit.tensor_name:
                return True

        return False

    def update_tensor_history(self, tensor_history):
        """
        Add hit flag to tensor history.

        Args:
            tensor_history (dict): The tensor history.
        """
        if not self._hits:
            return

        # add hit tensor names to `tensor_names`
        for tensor_info in tensor_history.get('tensor_history'):
            tensor_name = tensor_info['full_name']
            hit_flag = self._is_tensor_hit(tensor_name)
            tensor_info['is_hit'] = hit_flag


def validate_watch_condition(watch_condition):
    """Validate watch condition."""
    if not isinstance(watch_condition, dict):
        log.error("<watch_condition> should be dict. %s received.", watch_condition)
        raise DebuggerParamTypeError("<watch_condition> should be dict.")
    # validate condition
    condition = watch_condition.get('condition')
    if condition not in WATCHPOINT_CONDITION_MAPPING.keys():
        log.error("Invalid watch condition. Acceptable values are <%s>.",
                  str(WATCHPOINT_CONDITION_MAPPING.keys()))
        raise DebuggerParamValueError("Invalid watch condition value.")
    # validate param
    validate_watch_condition_params(watch_condition)


def validate_watch_condition_params(watch_condition):
    """
    Validate watch condition parameters.

    Args:
        watch_condition (dict): Watch condition.

            - condition (str): Condition type. Should be in WATCHPOINT_CONDITION_MAPPING.

            - param (list): Condition value. Should be given for comparison condition. The value will
                be translated to np.float32.
    """
    condition = watch_condition.get('condition')
    param = watch_condition.get('param')
    if condition in ['NAN', 'INF', 'OVERFLOW']:
        if param:
            log.error("No param is expected for %s condition.", condition)
            raise DebuggerParamValueError("No param is expected.")
    else:
        if not isinstance(param, (float, int)):
            log.error("Number param should be given for condition <%s>.",
                      condition)
            raise DebuggerParamValueError("Number param should be given.")
        if np.isinf(np.float32(param)):
            log.error("Condition param should be float32.")
            raise DebuggerParamValueError("The value of condition param should be within float32.")
