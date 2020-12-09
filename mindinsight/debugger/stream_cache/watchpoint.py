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
"""Define the watchpoint stream."""

import copy

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import is_scope_type, is_cst_type
from mindinsight.debugger.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.debugger.conditionmgr.common.utils import NodeBasicInfo
from mindinsight.debugger.conditionmgr.condition import ConditionIdEnum
from mindinsight.debugger.proto.debug_grpc_pb2 import SetCMD, WatchCondition

WATCHPOINT_CONDITION_MAPPING = {
    ConditionIdEnum.ACTIVATION_RANGE.value: WatchCondition.Condition.tensor_range,
    ConditionIdEnum.GRADIENT_EXPLODING.value: WatchCondition.Condition.tensor_general_overflow,
    ConditionIdEnum.GRADIENT_TOO_LARGE.value: WatchCondition.Condition.tensor_too_large,
    ConditionIdEnum.GRADIENT_VANISHING.value: WatchCondition.Condition.tensor_too_small,
    ConditionIdEnum.OPERATOR_OVERFLOW.value: WatchCondition.Condition.overflow,
    ConditionIdEnum.TENSOR_ALL_ZERO.value: WatchCondition.Condition.tensor_all_zero,
    ConditionIdEnum.TENSOR_OVERFLOW.value: WatchCondition.Condition.tensor_general_overflow,
    ConditionIdEnum.TENSOR_RANGE.value: WatchCondition.Condition.tensor_range,
    ConditionIdEnum.TENSOR_TOO_LARGE.value: WatchCondition.Condition.tensor_too_large,
    ConditionIdEnum.TENSOR_TOO_SMALL.value: WatchCondition.Condition.tensor_too_small,
    ConditionIdEnum.WEIGHT_CHANGE_TOO_LARGE.value: WatchCondition.Condition.tensor_change_too_large,
    ConditionIdEnum.WEIGHT_CHANGE_TOO_SMALL.value: WatchCondition.Condition.tensor_change_too_small,
    ConditionIdEnum.WEIGHT_INITIALIZATION.value: WatchCondition.Condition.tensor_initialization,
    ConditionIdEnum.WEIGHT_NOT_CHANGED.value: WatchCondition.Condition.tensor_not_changed,
    ConditionIdEnum.WEIGHT_OVERFLOW.value: WatchCondition.Condition.tensor_general_overflow,
    ConditionIdEnum.WEIGHT_TOO_LARGE.value: WatchCondition.Condition.tensor_too_large,
    ConditionIdEnum.WEIGHT_TOO_SMALL.value: WatchCondition.Condition.tensor_too_small
}


class WatchNodeTree:
    """The WatchNode Node Structure."""
    INVALID = -1  # the scope node and the nodes below are invalid
    NOT_WATCH = 0  # the scope node and the nodes below are not watched
    PARTIAL_WATCH = 1  # at least one node under the scope node is not watched
    TOTAL_WATCH = 2  # the scope node and the nodes below are all watched

    def __init__(self, node_name='', node_type=None, full_name='', watch_status=1):
        self._node_name = node_name
        self._full_name = full_name
        self._node_type = self._translate_node_type(node_type)
        self._watch_status = watch_status
        self._children = {}

    @property
    def node_name(self):
        """The property of node name."""
        return self._node_name

    @property
    def full_name(self):
        """The property of node name."""
        return self._full_name

    @property
    def node_type(self):
        """The property of node type."""
        return self._node_type

    @node_type.setter
    def node_type(self, value):
        """Set the node type."""
        self._node_type = self._translate_node_type(value)

    @property
    def watch_status(self):
        """The property of watch status about current node."""
        return self._watch_status

    @watch_status.setter
    def watch_status(self, value):
        """Set the node watch_status."""
        self._watch_status = value

    def update_metadata(self, node_type, full_name, watch_status):
        """Update the metadata for watched node."""
        self._full_name = full_name
        self._node_type = self._translate_node_type(node_type)
        self._watch_status = watch_status

    @staticmethod
    def _translate_node_type(node_type):
        """Translate node type to watch node type."""
        flag = node_type
        if not node_type or is_scope_type(node_type):
            flag = 'scope'
        return flag

    def get(self, sub_name):
        """Get sub node."""
        return self._children.get(sub_name)

    def get_children(self):
        """Get all children."""
        for name_scope, sub_watch_node in self._children.items():
            yield name_scope, sub_watch_node

    def get_children_count(self):
        """Get the count of children nodes."""
        return len(self._children)

    def add_node(self, node_name, node_type, full_name=''):
        """
        Add watch node to watch node tree.

        Args:
            node_name (str): The node name.
            node_type (str): The node type.
            full_name (str): The full name of node.
        """
        log.debug("Add node %s with type: %s, full_name: %s", node_name, node_type, full_name)
        scope_names = node_name.split('/', 1)
        if len(scope_names) == 1:
            target_node = self.get(node_name)
            if not target_node:
                self.add(node_name, node_type, full_name, watch_status=WatchNodeTree.TOTAL_WATCH)
            else:
                target_node.update_metadata(node_type, full_name, WatchNodeTree.TOTAL_WATCH)
            return

        scope_name, sub_names = scope_names
        sub_tree = self.get(scope_name)
        if not sub_tree:
            sub_tree = self.add(scope_name, watch_status=1)
        sub_tree.add_node(sub_names, node_type, full_name)

    def add(self, name, node_type=None, full_name='', watch_status=1):
        """Add sub WatchPointTree."""
        sub_name = '/'.join([self._node_name, name]) if self._node_name else name
        sub_tree = WatchNodeTree(sub_name, node_type, full_name, watch_status)
        self._children[name] = sub_tree

        return sub_tree

    def remove_node(self, node_name):
        """Remove sub node from current tree."""
        log.debug("Remove %s", node_name)
        scope_names = node_name.split('/', 1)
        sub_tree_name = scope_names[0]
        sub_tree = self._children.get(sub_tree_name)
        if not sub_tree:
            log.error("Failed to find node %s in WatchNodeTree.", sub_tree_name)
            raise DebuggerParamValueError("Failed to find node {}".format(sub_tree_name))

        if len(scope_names) > 1:
            sub_tree.remove_node(scope_names[1])

        if sub_tree.watch_status == WatchNodeTree.NOT_WATCH or len(scope_names) == 1:
            self._children.pop(sub_tree_name)

        self._watch_status = WatchNodeTree.PARTIAL_WATCH if self._children else \
            WatchNodeTree.NOT_WATCH


class Watchpoint:
    """
    The class of watchpoint stream.

    Args:
        watchpoint_id (int): The id of Watchpoint.
        watch_condition (dict): The condition of Watchpoint.

            - condition (str): Accept `INF` or `NAN`.
            - param (list[float]): Not defined yet.
    """

    def __init__(self, watchpoint_id, watch_condition, name=None):
        self._id = watchpoint_id
        self._condition = watch_condition
        self._watch_node = WatchNodeTree()
        self.name = name

    @property
    def watchpoint_id(self):
        """The property of watchpoint id."""
        return self._id

    @property
    def nodes(self):
        """The property of watch nodes."""
        return self._watch_node

    @property
    def condition(self):
        """The property of watch condition."""
        return self._condition

    def copy_nodes_from(self, other_watchpoint, deep_copy=False):
        """
        Copy nodes from other watchpoint.
        Args:
            other_watchpoint (Watchpoint): Other watchpoint.
            deep_copy (bool): Whether using deepcopy.
        """
        if deep_copy:
            self._watch_node = copy.deepcopy(other_watchpoint.nodes)
        else:
            self._watch_node = other_watchpoint.nodes

    def add_nodes(self, nodes):
        """Add node into watchpoint."""
        if not nodes:
            log.warning("Add empty nodes.")
            return

        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            self._watch_node.add_node(node.name, node.type, node.full_name)

    def remove_nodes(self, nodes):
        """Remove nodes from watchpoint."""
        if not nodes:
            return
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            self._watch_node.remove_node(node.name)

    def get_node_status(self, node_name, node_type, full_name):
        """Judge if the node is in watch nodes."""
        if is_cst_type(node_type):
            return WatchNodeTree.INVALID
        scope_names = node_name.split('/')
        cur_node = self._watch_node
        status = 1
        for scope_name in scope_names:
            cur_node = cur_node.get(scope_name)
            if cur_node is None:
                status = WatchNodeTree.NOT_WATCH
                break
            if cur_node.watch_status == WatchNodeTree.TOTAL_WATCH:
                status = WatchNodeTree.TOTAL_WATCH
                break
        if status == WatchNodeTree.TOTAL_WATCH and cur_node.node_name != node_name:
            self._watch_node.add_node(node_name, node_type, full_name)

        return status

    def _get_watch_node(self, cur_watch_node, watch_node_list):
        """
        Traverse the watch nodes and add total watched node list to `watch_node_list`.

        Args:
            cur_watch_node (WatchNodeTree): The current watch node.
            watch_node_list (list[NodeBasicInfo]): The list of watch node basic infos.
        """
        if cur_watch_node.watch_status == WatchNodeTree.TOTAL_WATCH:
            node_info = NodeBasicInfo(name=cur_watch_node.node_name,
                                      full_name=cur_watch_node.full_name,
                                      type=cur_watch_node.node_type)
            watch_node_list.append(node_info)
            return
        for _, watch_node in cur_watch_node.get_children():
            self._get_watch_node(watch_node, watch_node_list)

    def get_watch_nodes(self):
        """
        Get the name of all total watched nodes.

        Returns:
            list[NodeBasicInfo], the list of watch node basic infos.
        """
        watch_nodes = []
        self._get_watch_node(self._watch_node, watch_nodes)
        return watch_nodes

    def get_pending_cmd(self, watch_nodes):
        """Return the watchpoint in proto format."""
        # construct SetCMD
        condition_id = self._condition.get('id')
        set_cmd = SetCMD()
        set_cmd.id = self._id
        set_cmd.delete = False
        set_cmd.watch_condition.condition = WATCHPOINT_CONDITION_MAPPING.get(condition_id)
        condition_mgr = ConditionMgr()
        condition = condition_mgr.get_condition(condition_id)
        param_dict = {
            param.get('name'): param for param in self._condition.get('params')
        }
        for param_name in condition.ordered_parameter_names:
            param = param_dict.get(param_name)
            if param:
                param_proto = set_cmd.watch_condition.params.add()
                param_proto.name = param.get('name')
                param_proto.value = param.get('value')
                param_proto.disabled = False
                # Only one parameter of condition in old mindspore version.
                set_cmd.watch_condition.value = param.get('value')
            else:
                param_proto = set_cmd.watch_condition.params.add()
                param_proto.name = param_name
                param_proto.disabled = True

        for watch_node in watch_nodes:
            event_node = set_cmd.watch_nodes.add()
            event_node.node_name = watch_node.full_name
            event_node.node_type = watch_node.type
        return set_cmd

    def get_watch_condition_info(self):
        """Get watch condition info."""
        watchpoint_info = {
            'id': self._id,
            'watch_condition': self._condition
        }
        if self.name:
            watchpoint_info['name'] = self.name
        return watchpoint_info


class WatchpointHit:
    """The watchpoint hit structure."""

    def __init__(self, tensor_proto, watchpoint, node_name, graph_name):
        self._full_name = tensor_proto.node_name
        self._watchpoint = watchpoint
        self.node_name = node_name
        self.slot = tensor_proto.slot
        self.graph_name = graph_name
        self.error_code = 0

    @property
    def tensor_full_name(self):
        """The property of tensor full name."""
        tensor_name = ':'.join([self._full_name, self.slot])
        return tensor_name

    @property
    def watchpoint(self):
        """The property of watchpoint."""
        watchpoint = self._watchpoint.get_watch_condition_info()
        return watchpoint

    def __eq__(self, other):
        """Define the equal condition."""
        flag = self.tensor_full_name == other.tensor_full_name \
               and self.watchpoint == other.watchpoint \
               and self.graph_name == other.graph_name
        return flag
