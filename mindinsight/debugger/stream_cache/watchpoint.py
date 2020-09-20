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
from mindinsight.datavisual.data_transform.graph.node import NodeTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.proto.debug_grpc_pb2 import SetCMD, WatchCondition

WATCHPOINT_CONDITION_MAPPING = {
    'INF': WatchCondition.Condition.inf,
    'NAN': WatchCondition.Condition.nan,
    'OVERFLOW': WatchCondition.Condition.overflow,
    'MAX_GT': WatchCondition.Condition.max_gt,
    'MAX_LT': WatchCondition.Condition.max_lt,
    'MIN_GT': WatchCondition.Condition.min_gt,
    'MIN_LT': WatchCondition.Condition.min_lt,
    'MAX_MIN_GT': WatchCondition.Condition.max_min_gt,
    'MAX_MIN_LT': WatchCondition.Condition.max_min_lt,
    'MEAN_GT': WatchCondition.Condition.mean_gt,
    'MEAN_LT': WatchCondition.Condition.mean_lt
}


class WatchNodeTree:
    """The WatchNode Node Structure."""
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

    def update_metadata(self, node_type, full_name, watch_status):
        """Update the metadata for watched node."""
        self._full_name = full_name
        self._node_type = self._translate_node_type(node_type)
        self._watch_status = watch_status

    @staticmethod
    def _translate_node_type(node_type):
        """Translate node type to watch node type."""
        flag = node_type
        if not node_type or node_type == NodeTypeEnum.NAME_SCOPE.value:
            flag = 'scope'
        elif node_type != NodeTypeEnum.AGGREGATION_SCOPE.value:
            flag = 'leaf'
        return flag

    def get(self, sub_name):
        """Get sub node."""
        return self._children.get(sub_name)

    def get_children(self):
        """Get all childrens."""
        for name_scope, sub_watch_node in self._children.items():
            yield name_scope, sub_watch_node

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

    def __init__(self, watchpoint_id, watch_condition):
        self._id = watchpoint_id
        self._condition = watch_condition
        self._watch_node = WatchNodeTree()

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

    def copy_nodes_from(self, other_watchpoint):
        """
        Copy nodes from other watchpoint.
        Args:
            other_watchpoint (Watchpoint): Other watchpoint.
        """
        self._watch_node = other_watchpoint.nodes

    def add_nodes(self, nodes):
        """Add node into watchcpoint."""
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
            node_name = node.split(':')[0]
            self._watch_node.remove_node(node_name)

    def get_node_status(self, node_name, node_type, full_name):
        """Judge if the node is in watch nodes."""
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

    def get_watch_node(self, cur_watch_node, watch_node_list):
        """
        Traverse the watch nodes and add total watched node list to `watch_node_list`.

        Args:
            cur_watch_node (WatchNodeTree): The current watch node.
            watch_node_list (list[WatchNodeTree]): The list of total watched node.
        """
        if cur_watch_node.watch_status == WatchNodeTree.TOTAL_WATCH and \
                cur_watch_node.node_type != NodeTypeEnum.AGGREGATION_SCOPE.value:
            watch_node_list.append(cur_watch_node)
            return
        for _, watch_node in cur_watch_node.get_children():
            self.get_watch_node(watch_node, watch_node_list)

    def get_set_cmd(self):
        """Return the watchpoint in proto format."""
        # get watch nodes.
        watch_nodes = []
        self.get_watch_node(self._watch_node, watch_nodes)
        # construct SetCMD
        set_cmd = SetCMD()
        set_cmd.id = self._id
        set_cmd.delete = False
        set_cmd.watch_condition.condition = WATCHPOINT_CONDITION_MAPPING.get(
            self._condition.get('condition'))
        if self._condition.get('param'):
            # at most one param is provided
            set_cmd.watch_condition.value = self._condition.get('param')
        for watch_node in watch_nodes:
            event_node = set_cmd.watch_nodes.add()
            event_node.node_name = watch_node.full_name
            event_node.node_type = watch_node.node_type

        return set_cmd

    def get_watch_condition_info(self):
        """Get watch condition info."""
        watchpoint_info = {
            'id': self._id,
            'watch_condition': self._condition
        }
        return watchpoint_info


class WatchpointHit:
    """The watchpoint hit structure."""

    def __init__(self, tensor_proto, watchpoint, node_name):
        self._node_name = node_name
        self._full_name = tensor_proto.node_name
        self._slot = tensor_proto.slot
        self._watchpoint = watchpoint

    @property
    def tensor_full_name(self):
        """The property of tensor_name."""
        tensor_name = ':'.join([self._full_name, self._slot])
        return tensor_name

    @property
    def watchpoint(self):
        """The property of watchpoint."""
        watchpoint = self._watchpoint.get_watch_condition_info()
        return watchpoint

    def __eq__(self, other):
        """Define the equal condition."""
        flag = self.tensor_full_name == other.tensor_full_name and self.watchpoint == other.watchpoint
        return flag
