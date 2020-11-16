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
from mindinsight.conditionmgr.condition import ValueTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import is_scope_type
from mindinsight.debugger.proto.debug_grpc_pb2 import SetCMD
from mindinsight.debugger.stream_cache.watchpoint import Watchpoint, WatchpointHit, \
    WatchNodeTree
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class WatchpointHandler(StreamHandlerBase):
    """Watchpoint Handler."""

    def __init__(self):
        self._watchpoints = {}
        # list of ids of new created watchpoints
        self._created_watchpoints = []
        # list of SetCMD of watchpoints to be deleted
        self._deleted_watchpoints = []
        # dict of <id, SetCMD> of watchpoint to be updated
        self._updated_watchpoints = {}
        # the collection of watched node full names, which have been sent to MindSpore
        self._all_watched_node_full_names = set()
        # the collection of new watched node full names, which have not been sent to MindSpore
        self._new_watched_node_full_names = set()
        # record the temp stored nodes in MS, which could be set as watch node for recheck on GPU
        # should be clean at the beginning of each step
        self._temp_cached_node_full_names = set()
        self._latest_id = 0
        self._cache_set_cmd = {}

    def put(self, value):
        """
        Put Watchpoint into watchpoint handler.

        Args:
            value (Watchpoint): The name of nodes that have been chosen.
        """
        new_id = value.watchpoint_id
        self._watchpoints[new_id] = value
        self._created_watchpoints.append(new_id)
        self._updated_watchpoints[new_id] = value
        self._latest_id = new_id
        log.debug("Put watchpoint %d into cache.", new_id)

    def clean_temp_cached_names(self):
        """Clean temp cached node."""
        self._temp_cached_node_full_names.clear()

    def add_temp_cached_name(self, node_full_name):
        """Add temp stored node in cache."""
        if node_full_name:
            self._temp_cached_node_full_names.add(node_full_name)

    def sync_set_cmd(self, set_cmds):
        """Clean temp watchpoints."""
        self._new_watched_node_full_names = set()
        self._created_watchpoints = []
        self._deleted_watchpoints = []
        self._updated_watchpoints = {}
        for set_cmd in set_cmds:
            self._cache_set_cmd[set_cmd.id] = set_cmd

    def clean_cache_set_cmd(self, set_cmd):
        """Clean cache set command."""
        self._cache_set_cmd.pop(set_cmd.id, None)

    def get_watchpoint_by_id(self, watchpoint_id):
        """Get watchpoint by watchpoint id."""
        res = self.get(watchpoint_id)
        watchpoint = res.get('watch_points')[0]

        return watchpoint

    def get(self, filter_condition=None):
        """
        Get the watchpoints.

        Args:
            filter_condition (Union[None, int]): The filter conditions. Get watchpoint by
                id. If None, return all watchpoint. Default: None.

        Returns:
            dict, the watchpoint list.
        """
        reply = []
        if not filter_condition:
            # get watch condition list
            for _, watchpoint in self._watchpoints.items():
                watchpoint_info = watchpoint.get_watch_condition_info()
                reply.append(watchpoint_info)
        else:
            self.validate_watchpoint_id(filter_condition)
            reply = [self._watchpoints.get(filter_condition)]

        log.debug("get the watch points with filter_condition:%s", filter_condition)

        return {'watch_points': reply}

    def get_pending_commands(self, graph_stream):
        """
        Get all watchpoint in SetCMD proto format.

        Args:
            graph_stream (GraphHandler): Graph handler.

        Returns:
            list[SetCMD], updated watchpoint to be sent to MindSpore.
        """
        res = []
        new_watched_nodes = set()
        self._all_watched_node_full_names.clear()
        for _, watchpoint in self._updated_watchpoints.items():
            # construct set command with leaf nodes
            watch_nodes = watchpoint.get_watch_nodes()
            leaf_watch_nodes = self._expand_to_leaf_nodes(graph_stream, watch_nodes)
            res.append(watchpoint.get_pending_cmd(leaf_watch_nodes))
            # update all watched node names
            watch_node_names = [watch_node.full_name for watch_node in [*watch_nodes, *leaf_watch_nodes]]
            new_watched_nodes.update(watch_node_names)
        res.extend(self._deleted_watchpoints)
        for _, set_cmd in self._cache_set_cmd.items():
            res.append(set_cmd)
        self._all_watched_node_full_names = new_watched_nodes
        return res

    @staticmethod
    def _expand_to_leaf_nodes(graph_stream, watch_nodes):
        """
        Get all leaf node basic info according to watch nodes.

        Args:
            graph_stream (GraphHandler): Graph handler.
            watch_nodes (list[NodeBasicInfo]): The list of watch node basic infos.

        Returns:
            list[NodeBasicInfo], expanded leaf basic node infos.
        """
        leaf_watch_nodes = []
        for node in watch_nodes:
            if is_scope_type(node.type):
                pure_node_name = None
                if len(node.name.split('/')) > 1:
                    graph_name, pure_node_name = node.name.split('/', 1)
                else:
                    graph_name = node.name
                search_node_infos = graph_stream.get_node_basic_info_by_scope(pure_node_name, graph_name=graph_name)
                leaf_watch_nodes.extend(search_node_infos)
            else:
                leaf_watch_nodes.append(node)
        return leaf_watch_nodes

    def is_recheckable(self, backend=None):
        """
        Check if current status is able to recheck.

        Args:
            backend (str): The backend info. 'Ascend' or 'GPU'. Default: None.

        Returns:
            bool, if enable to recheck.
        """
        enable_recheck = bool(self._updated_watchpoints or self._deleted_watchpoints)
        if backend == 'GPU' and enable_recheck:
            # on GPU, disable to recheck if there are new watched node of which the tensor
            # has not been stored on MindSpore
            diff_set = self._new_watched_node_full_names - self._all_watched_node_full_names
            enable_recheck = not diff_set or diff_set.issubset(self._temp_cached_node_full_names)
        return enable_recheck

    def set_watch_nodes(self, graph, graph_stream, watch_point_id, graph_name=None):
        """
        set watch nodes for graph.

        Args:
            graph (dict): The graph with list of nodes.
            graph_stream (GraphHandler): The graph handler.
            watch_point_id (int): The id of watchpoint.
            graph_name (str): The graph name.
        """
        if not (watch_point_id and graph):
            return
        log.debug("add watch flags")
        watchpoint = self._watchpoints.get(watch_point_id)
        self._set_watch_status_recursively(graph, graph_stream, watchpoint, graph_name)

    def _set_watch_status_recursively(self, graph, graph_stream, watchpoint, graph_name=None):
        """Set watch status to graph."""
        if graph.get('children'):
            self._set_watch_status_recursively(
                graph.get('children'), graph_stream, watchpoint, graph_name)

        if graph.get('nodes'):
            _ = self._set_watch_state_for_nodes(graph['nodes'], graph_stream, watchpoint, graph_name)

    def _set_watch_state_for_nodes(self, nodes, graph_stream, watchpoint, graph_name):
        """
        Set watch state for nodes.

        Args:
            nodes (list[Node]): List of node info.

        Returns:
            int, the number of all watched nodes.
        """
        all_watched_num = 0
        for node in nodes:
            node_name = node.get('name')
            # search result could have `nodes` in nodes object
            if node.get('nodes'):
                flag = self._set_watch_state_for_nodes(node.get('nodes'), graph_stream, watchpoint, graph_name)
            else:
                full_name = graph_stream.get_full_name(node_name, graph_name)
                new_node_name = node_name if graph_name is None else '/'.join([graph_name, node_name])
                flag = watchpoint.get_node_status(new_node_name, node.get('type'), full_name)
            node['watched'] = flag
            if flag == WatchNodeTree.TOTAL_WATCH:
                all_watched_num += 1

        # calculate the state of current node.
        if not all_watched_num:
            state = WatchNodeTree.NOT_WATCH
        elif all_watched_num == len(nodes):
            state = WatchNodeTree.TOTAL_WATCH
        else:
            state = WatchNodeTree.PARTIAL_WATCH

        return state

    def create_watchpoint(self, condition_mgr, watch_condition, watch_nodes=None, watch_point_id=None):
        """
        Create watchpoint.
        Args:
            condition_mgr (ConditionMgr): Instance of ConditionMgr.
            watch_condition (dict): The watch condition.
                "condition": {
                    id: "tensor_too_large",
                    "params": [
                        {
                            "name": "abs_mean_gt",
                            "disable": false,
                            "value": 1.1
                        }
                    ]
                }
                - id (str): Id of condition.
                - param (list[dict]): The list of param for this condition.
            watch_nodes (list[NodeBasicInfo]): The list of node basic info.
            watch_point_id (int): The id of watchpoint.

        Returns:
            int, the new id of watchpoint.
        """
        validate_watch_condition(condition_mgr, watch_condition)
        watch_condition = set_default_param(condition_mgr, watch_condition)
        new_id = self._latest_id + 1
        watchpoint = Watchpoint(new_id, watch_condition)
        if watch_nodes:
            watchpoint.add_nodes(watch_nodes)
            self._add_watch_node_in_cache(watch_nodes)
        elif watch_point_id:
            self.validate_watchpoint_id(watch_point_id)
            watchpoint.copy_nodes_from(self._watchpoints.get(watch_point_id))
        self.put(watchpoint)

        return new_id

    def update_watchpoint(self, watch_point_id, watch_nodes, watched=False):
        """
        Update watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.
            watch_nodes (list[NodeBasicInfo]): The list of node basic info.
            watched (bool): The update operator on nodes. If False, remove nodes from watch nodes.
                If True, add nodes to watch nodes. Default: False.
        """
        self.validate_watchpoint_id(watch_point_id)
        watchpoint = self._watchpoints.get(watch_point_id)
        if watched:
            watchpoint.add_nodes(watch_nodes)
            self._add_watch_node_in_cache(watch_nodes)
        else:
            watchpoint.remove_nodes(watch_nodes)
            self._remove_watch_node_from_cache(watch_nodes)
        self._updated_watchpoints[watch_point_id] = watchpoint
        log.debug("Update watchpoint %d in cache.", watch_point_id)

    def delete_watchpoint(self, watch_point_id=None):
        """
        Delete watchpoint.

        Args:
            watch_point_id (Union[None, int]): The id of watchpoint.
                If None, delete all watchpoints. Default: None.
        """
        if watch_point_id is None:
            watch_point_ids = [sub_id for sub_id, _ in self._watchpoints.items()]
        else:
            self.validate_watchpoint_id(watch_point_id)
            watch_point_ids = [watch_point_id]
        for single_id in watch_point_ids:
            self._delete_single_watchpoint(single_id)

    def _delete_single_watchpoint(self, watch_point_id):
        """
        Delete single watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.
        """
        self._watchpoints.pop(watch_point_id)
        # if the watchpoint has not been created by MindSpore, clean the relative cache directly
        if watch_point_id in self._created_watchpoints:
            self._created_watchpoints.remove(watch_point_id)
            self._updated_watchpoints.pop(watch_point_id)
            log.debug("Cancel create watchpoint %d in cache.", watch_point_id)
            return
        set_cmd = SetCMD()
        set_cmd.id = watch_point_id
        set_cmd.delete = True
        self._deleted_watchpoints.append(set_cmd)
        log.debug("Delete watchpoint %d in cache.", watch_point_id)

    def validate_watchpoint_id(self, watch_point_id):
        """Validate watchpoint id."""
        if not isinstance(watch_point_id, int):
            log.error("Invalid watchpoint id %s. The watch point id should be int.", watch_point_id)
            raise DebuggerParamTypeError("Watchpoint id should be int type.")
        if watch_point_id and watch_point_id not in self._watchpoints:
            log.error("Invalid watchpoint id: %d.", watch_point_id)
            raise DebuggerParamValueError("Invalid watchpoint id: {}".format(watch_point_id))

    def _add_watch_node_in_cache(self, watch_nodes):
        """
        Add watch nodes in cache.

        Args:
            watch_nodes (list[NodeBasicInfo]): The list of node basic info.
        """
        node_full_names = [node.full_name for node in watch_nodes]
        self._new_watched_node_full_names.update(node_full_names)

    def _remove_watch_node_from_cache(self, watch_nodes):
        """
        Remove watch nodes from cache.

        Args:
            watch_nodes (list[NodeBasicInfo]): The list of node basic info.
        """
        for node in watch_nodes:
            if node.full_name in self._new_watched_node_full_names:
                self._new_watched_node_full_names.remove(node.full_name)


class WatchpointHitHandler(StreamHandlerBase):
    """Watchpoint hit handler."""

    def __init__(self):
        # dict of <ui node_name, dict of <slot, WatchpointHit>>,
        self._hits = {}

    @property
    def empty(self):
        """Whether the watchpoint hit is empty."""
        return not self._hits

    def put(self, value):
        """
        Put value into watchpoint hit cache. Called by grpc server.

        Args:
            value (dict): The watchpoint hit info.

                - tensor_proto (TensorProto): The message about hit tensor.

                - watchpoint (Watchpoint): The Watchpoint that a node hit.

                - node_name (str): The UI node name.

                - graph_name (str): The graph name.
        """
        watchpoint_hit = WatchpointHit(
            tensor_proto=value.get('tensor_proto'),
            watchpoint=value.get('watchpoint'),
            node_name=value.get('node_name'),
            graph_name=value.get('graph_name')
        )
        # get all hit watchpoints according to node name ans tensor slot
        watchpoint_hits = self._get_watchpoints_by_tensor_name(watchpoint_hit.node_name,
                                                               watchpoint_hit.slot)
        if watchpoint_hit not in watchpoint_hits:
            watchpoint_hits.append(watchpoint_hit)

    def _get_watchpoints_by_tensor_name(self, node_name, slot):
        """
        Get hit tensors according to ui node name and slot.

        Args:
            node_name (str): The node name.
            slot (str): The tensor slot.

        Returns:
            list, list of watchpoints.
        """
        hit_node = self._hits.get(node_name)
        if hit_node is None:
            hit_node = {}
            self._hits[node_name] = hit_node
        hit_tensors = hit_node.get(slot)
        if hit_tensors is None:
            hit_tensors = []
            hit_node[slot] = hit_tensors
        return hit_tensors

    def get(self, filter_condition=None):
        """
        Get watchpoint hit list.

        Args:
            filter_condition (str): Get the watchpoint hit according to specified node name.
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
            tensors = []
            graph_name = None
            for slot, tensor_hits in watchpoint_hits.items():
                if graph_name is None:
                    graph_name = tensor_hits[0].graph_name
                tensor_info = self._get_tensor_hit_info(slot, tensor_hits)
                tensors.append(tensor_info)
            watch_point_hits.append({
                'node_name': node_name,
                'tensors': tensors,
                'graph_name': graph_name
            })

        return {'watch_point_hits': watch_point_hits}

    @staticmethod
    def _get_tensor_hit_info(slot, tensor_hits):
        """
        Get watchpoint hit info of specified tensor.

        Args:
            slot (str): Slot id.
            tensor_hits (list): A list of watchpoint hit objects that the tensor hit.

        Returns:
            dict, tensor hit info.
        """
        res = {}
        watch_points = [tensor_hit.watchpoint for tensor_hit in tensor_hits]
        if watch_points:
            res = {
                'slot': slot,
                'watch_points': watch_points
            }
        return res

    def _is_tensor_hit(self, tensor_name):
        """
        Check if the tensor is record in hit cache.

        Args:
            tensor_name (str): The name of ui tensor name.

        Returns:
            bool, if the tensor is hit.
        """
        node_name, slot = tensor_name.rsplit(':', 1)
        watchpoint_hits = self._hits.get(node_name, {}).get(slot)
        return bool(watchpoint_hits)

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
            tensor_name = tensor_info['name']
            hit_flag = self._is_tensor_hit(tensor_name)
            tensor_info['is_hit'] = hit_flag

    def get_tensor_hit_infos(self, tensor_name):
        """
        Get all hit information of a tensor.

        Args:
            tensor_name (str): Tensor name showed on UI.

        Returns:
            dict, tensor hit info.
        """
        tensor_hit_info = {}
        if self._is_tensor_hit(tensor_name):
            node_name, slot = tensor_name.rsplit(':', 1)
            tensor_hits = self._get_watchpoints_by_tensor_name(node_name, slot)
            tensor_hit_info = self._get_tensor_hit_info(slot, tensor_hits)
        return tensor_hit_info


def validate_watch_condition(condition_mgr, watch_condition):
    """Validate watch condition."""
    if not isinstance(watch_condition, dict):
        log.error("<watch_condition> should be dict. %s received.", watch_condition)
        raise DebuggerParamTypeError("<watch_condition> should be dict.")
    # validate condition_id
    condition_id = watch_condition.get('id')
    if condition_id not in condition_mgr.conditions.keys():
        log.error("Invalid watch condition. Acceptable values are <%s>. %s received.",
                  str(condition_mgr.conditions.keys()), condition_id)
        raise DebuggerParamValueError("Invalid watch condition value.")
    # validate param
    validate_watch_condition_params(condition_mgr, watch_condition)


def validate_watch_condition_params(condition_mgr, watch_condition):
    """
    Validate watch condition parameters.

    Args:
        condition_mgr (ConditionMgr): Instance of ConditionMgr.
        watch_condition (dict): Watch condition.

            - id (str): Condition id. Should be in WATCHPOINT_CONDITION_MAPPING.

            - param (list): Condition value. Should be given for comparison condition. The value
                will be translated to np.float32.
    """
    condition_id = watch_condition.get('id')
    params = watch_condition.get('params')
    condition = condition_mgr.get_condition(condition_id)
    if condition_id in condition_mgr.get_no_param_condition():
        if params:
            log.error("No param is expected for %s condition", condition_id)
            raise DebuggerParamValueError("No param is expected.")
        return

    for param in params:
        condition_param_name = param.get("name")
        if condition_param_name not in condition.names:
            log.error("Invalid name of parameter for condition: %s, available values: %s",
                      condition_id, condition.names)
            raise DebuggerParamValueError("Invalid name of parameter.")

        condition_param = condition.get_parameter_definition(condition_param_name)
        if condition_param.type.name in (ValueTypeEnum.FLOAT64.name, ValueTypeEnum.INT64.name) \
                and not isinstance(param.get("value"), (float, int)):
            log.error("Number param should be given for condition: %s", condition_id)
            raise DebuggerParamValueError("Number param should be given.")

        if condition_param.type.name == ValueTypeEnum.BOOL.name \
                and not isinstance(param.get("value"), bool):
            log.error("Bool param should be given for condition: %s", condition_id)
            raise DebuggerParamValueError("Bool param should be given.")

        if not condition_param.is_valid(param.get("value")):
            log.error("Param %s out of range for condition: %s", condition_param_name, condition_id)
            raise DebuggerParamValueError("Parameter out of range.")


def set_default_param(condition_mgr, watch_condition):
    """
    Set default param.
    Args:
        condition_mgr (ConditionMgr): Instance of ConditionMgr.
        watch_condition (dict): The watch condition.
            "condition": {
                id: "tensor_too_large",
                "params": [
                    {
                        "name": "abs_mean_gt",
                        "disable": false,
                        "value": 1.1
                    }
                ]
            }
            - id (str): Id of condition.
            - param (list[dict]): The list of param for this condition.

    Returns:
        dict, the new watch_condition.
    """
    condition_id = watch_condition.get('id')
    condition = condition_mgr.get_condition(condition_id)
    for param in condition.parameters:
        if not param.visible_on_ui and not param.support_disable:
            watch_condition["params"].append({
                "name": param.name,
                "disable": False,
                "value": param.default_value
            })
    watch_condition["abbr"] = condition.abbr
    return watch_condition
