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
from enum import Enum

class NodeTypeEnum(Enum):
    """Node type enum. The following types are new to our custom."""
    NAME_SCOPE = 'name_scope'
    POLYMERIC_SCOPE = 'polymeric_scope'
    PARAMETER = 'Parameter'
    CONST = 'Const'


class Node:
    """
    Define a node object.

    Args:
        name (str): Name of new node.
        node_id (str): The id of this node, and node id is unique in graph.
    """

    def __init__(self, name, node_id):
        self._node_id = node_id
        self._name = name
        self._type = ""
        self._attr = dict()
        self._input = dict()
        self._output_i = -1
        self._output = {}
        self._polymeric_input = {}
        self._polymeric_output = {}
        self._polymeric_scope_name = ""
        self._subnode_count = 0
        self._name_scope = ""
        self.shape = []

    def to_dict(self):
        """Converts the node object to dictionary format."""
        return {
            'name': self._name,
            'type': self._type,
            'attr': self._attr,
            'input': self._input,
            'output_i': self._output_i,
            'output': self._output,
            'polymeric_input': self._polymeric_input,
            'polymeric_output': self._polymeric_output,
            'subnode_count': self._subnode_count,
            'polymeric_scope_name': self._polymeric_scope_name
        }

    @property
    def node_id(self):
        """The id of this node, and id is unique in graph."""
        return self._node_id

    @property
    def name(self):
        """Get node name."""
        return self._name

    @name.setter
    def name(self, name):
        """Set node name."""
        self._name = name

    @property
    def node_type(self):
        """Get node type."""
        return self._type

    @node_type.setter
    def node_type(self, node_type):
        """Set node type."""
        self._type = node_type

    @property
    def attr(self):
        """Get node attr."""
        return self._attr

    def update_attr(self, attr_dict):
        """
        Update node attr.

        Args:
            attr_dict (dict[str, str]): Format is {'<key>': '<value>'}.
        """
        self._attr.update(attr_dict)

    @property
    def input(self):
        """
        Get all input of current node.

        Returns:
            dict[str, dict], format is {'<src_name>': {'shape': [], 'edge_type', 'scope'}}.
        """
        return self._input

    def update_input(self, input_dict):
        """
        Update input.

        Args:
            input_dict (dict[str, dict]): Format is {'<src_name>': {'shape': [], 'edge_type', 'scope'}}.
        """
        self._input.update(input_dict)

    @property
    def output_i(self):
        """The memory address of this node when it is in run time."""
        return self._output_i

    @output_i.setter
    def output_i(self, output_i):
        """Set memory address."""
        self._output_i = output_i

    @property
    def polymeric_input(self):
        """
        The polymeric input is the input of the polymeric nodes.

        Returns:
            dict[str, dict], format is {'<src_name>': {'edge_type': '<value>'}}.
        """
        return self._polymeric_input

    def update_polymeric_input(self, polymeric_input):
        """The polymeric input is the input of the polymeric nodes."""
        self._polymeric_input.update(polymeric_input)

    @property
    def output(self):
        """The output node of this node."""
        return self._output

    def update_output(self, output):
        """
        Update output node.

        Args:
            output (dict[str, TypedDict('NodeType', {'type': str})]): Format
                is {"<node_name>": {"type": "<node type>"}}.
        """
        self._output.update(output)

    @property
    def polymeric_output(self):
        """Get polymeric output."""
        return self._polymeric_output

    def update_polymeric_output(self, polymeric_output):
        """
        Update polymeric output.

        Args:
            polymeric_output (dict[str, dict): Format is {dst_node.polymeric_scope_name:
                                                {'edge_type': EdgeTypeEnum.DATA.value}}).

        """
        self._polymeric_output.update(polymeric_output)

    @property
    def polymeric_scope_name(self):
        """Get polymeric scope name."""
        return self._polymeric_scope_name

    @polymeric_scope_name.setter
    def polymeric_scope_name(self, name):
        """Set polymeric scope name."""
        self._polymeric_scope_name = name

    @property
    def subnode_count(self):
        """The sub node count of this node, if this node is a scope node, this count will not be zero."""
        return self._subnode_count

    @subnode_count.setter
    def subnode_count(self, count):
        """Set sub node count."""
        self._subnode_count = count

    @property
    def name_scope(self):
        """Get name scope of this node."""
        return self._name_scope

    @name_scope.setter
    def name_scope(self, name_scope):
        """Set name scope."""
        self._name_scope = name_scope

    def __str__(self):
        return f'<Node, name: {self._name}, type: {self._type}>'
