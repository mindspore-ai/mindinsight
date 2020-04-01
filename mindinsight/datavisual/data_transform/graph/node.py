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
        self._inputs = dict()
        self._output_i = -1
        self._outputs = {}
        self._polymeric_inputs = {}
        self._polymeric_outputs = {}
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
            'input': self._inputs,
            'output_i': self._output_i,
            'output': self._outputs,
            'polymeric_input': self._polymeric_inputs,
            'polymeric_output': self._polymeric_outputs,
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
            attr_dict (dict[str, str]): The attr of node.
        """
        self._attr.update(attr_dict)

    @property
    def inputs(self):
        """
        Get all input of current node.

        Returns:
            dict[str, dict], format is {'<src_name>': {'shape': [], 'edge_type', 'scope'}}.
        """
        return self._inputs

    def update_input(self, input_dict):
        """
        Update input.

        Args:
            input_dict (dict[str, dict]): Key is a source node name, and the value is a dict.

                - shape (list): The shape of input tensor.
                - edge_type (str): The type of edge, optional value refer to `EdgeTypeEnum`.
                - scope (str): The scope of this source node.
        """
        self._inputs.update(input_dict)

    @property
    def output_i(self):
        """The memory address of this node when it is in run time."""
        return self._output_i

    @output_i.setter
    def output_i(self, output_i):
        """Set memory address."""
        self._output_i = output_i

    @property
    def polymeric_inputs(self):
        """
        The polymeric input is the input of the polymeric nodes.

        Returns:
            dict[str, dict], format is {'<src_name>': {'edge_type': '<value>'}}.
        """
        return self._polymeric_inputs

    def update_polymeric_input(self, polymeric_input):
        """The polymeric input is the input of the polymeric nodes."""
        self._polymeric_inputs.update(polymeric_input)

    @property
    def outputs(self):
        """The output node of this node."""
        return self._outputs

    def update_output(self, output):
        """
        Update output node.

        Args:
            output (dict[str, TypedDict('NodeType', {'type': str})]): Key is a dst node name, and value is a dict.

                - type (str): The type of the dst node.
        """
        self._outputs.update(output)

    @property
    def polymeric_outputs(self):
        """Get polymeric output."""
        return self._polymeric_outputs

    def update_polymeric_output(self, polymeric_output):
        """
        Update polymeric output.

        Args:
            polymeric_output (dict[str, dict): Key is the polymeric scope name of dst name, and value is dict.

                - edge_type (str): The edge type of the dst node.

        """
        self._polymeric_outputs.update(polymeric_output)

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
