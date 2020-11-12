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
"""
This file is used to define the node of graph and associated base types.
"""
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log


class NodeTree:
    """A class for building a node tree."""
    def __init__(self, node_name='', node_type=None):
        self.node_name = node_name
        self._node_type = node_type
        self._children = {}

    @property
    def node_type(self):
        """The property of node type."""
        return self._node_type

    @node_type.setter
    def node_type(self, value):
        """Set the node type."""
        self._node_type = value

    def add(self, name, node_type=None):
        """Add sub node."""
        sub_name = '/'.join([self.node_name, name]) if self.node_name else name
        sub_node = NodeTree(sub_name, node_type)
        self._children[name] = sub_node
        return sub_node

    def get(self, sub_name):
        """Get sub node."""
        return self._children.get(sub_name)

    def get_children(self):
        """Get all childrens."""
        for name_scope, sub_node in self._children.items():
            yield name_scope, sub_node

    def remove(self, sub_name):
        """Remove sub node."""
        try:
            self._children.pop(sub_name)
        except KeyError as err:
            log.error("Failed to find node %s. %s", sub_name, err)
            raise DebuggerParamValueError("Failed to find node {}".format(sub_name))
