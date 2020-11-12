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
    AGGREGATION_SCOPE = 'aggregation_scope'
    PARAMETER = 'Parameter'
    CONST = 'Const'


class Node:
    """
    Define a node object.

    Args:
        name (str): Name of new node.
        node_id (str): The id of this node, and node id is unique in graph.
    """

    def __init__(self, name, node_id, topological_index=-1):
        self._node_id = node_id
        self.name = name
        self.type = ""
        self._attr = dict()
        self._input = dict()
        self.output_i = 0
        self._output = {}
        self._proxy_input = {}
        self._proxy_output = {}
        self.subnode_count = 0
        self.scope = ""
        self.independent_layout = False
        self.output_shape = []
        self.output_data_type = ""
        self.output_nums = 0
        self.elem_types = []
        self.full_name = ""
        # This value will be used as the priority field.
        self.topological_index = topological_index

    def to_dict(self):
        """Converts the node object to dictionary format."""
        return {
            'name': self.name,
            'type': self.type,
            'attr': self._attr,
            'input': self._input,
            'output': self._output,
            'output_i': self.output_i,
            'proxy_input': self._proxy_input,
            'proxy_output': self._proxy_output,
            'subnode_count': self.subnode_count,
            'independent_layout': self.independent_layout
        }

    @property
    def node_id(self):
        """The id of this node, and id is unique in graph."""
        return self._node_id

    @staticmethod
    def create_node_name(scope, base_name):
        """
        The name of the node consists of the scope and the basic name.

        Args:
            scope (str): The scope of node, such as 'Default/Conv2D'
            base_name (str): The base name of node, such as 'Add11'.

        Returns:
            str, a node name.
        """
        return f'{scope}/{base_name}' if scope else base_name

    @property
    def attr(self):
        """Get node attr."""
        return self._attr

    def add_attr(self, attr_dict):
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
            dict[str, dict], refer to the input attr.
        """
        return self._input

    def add_inputs(self, src_name, input_attr):
        """
        Update input.

        Args:
            src_name (stc): The source node name.
            input_attr (dict): The attribute of the input.

                - shape (list): The shape of input tensor.
                - edge_type (str): The type of edge, optional value refer to `EdgeTypeEnum`.
                - data_type (str): The data type of the input.
                - independent_layout (bool): Indicates whether the source nodes are laid out independently.
        """
        self._input.update({src_name: input_attr})

    def delete_inputs(self, src_name):
        """
        Delete input attribute by the given source name.

        Args:
            src_name (str): The source node name.
        """
        self._input.pop(src_name)

    @property
    def outputs(self):
        """The output node of this node."""
        return self._output

    def add_outputs(self, dst_name, output_attr):
        """
        Add a output node to this node.

        Args:
            dst_name (str): The name of the output node.
            output_attr (dict: Same as the input attribute.
        """
        self._output.update({dst_name: output_attr})

    def delete_outputs(self, dst_name):
        """
        Delete a output node.

        Args:
            dst_name (str): The name of the node to be deleted.
        """
        self._output.pop(dst_name)

    @property
    def proxy_inputs(self):
        """Return proxy input, type is dict."""
        return self._proxy_input

    def add_proxy_inputs(self, src_name, attr):
        """
        Add a proxy input to node.

        Args:
            src_name (str): The name of the input node.
            attr (dict): The attr of the input.

            - edge_type (str): The edge type, refer to `EdgeTypeEnum`.
        """
        self._proxy_input.update({src_name: attr})

    def delete_proxy_inputs(self, src_name):
        """Delete a proxy input by the src name."""
        self._proxy_input.pop(src_name)

    @property
    def proxy_outputs(self):
        """Get proxy output, data type is dict."""
        return self._proxy_output

    def add_proxy_outputs(self, dst_name, attr):
        """
        Add a proxy output to node.

        Args:
            dst_name (str): The name of the output node.
            attr (dict): The attr of the output.

            - edge_type (str): The edge type, refer to `EdgeTypeEnum`.
        """
        self._proxy_output.update({dst_name: attr})

    def delete_proxy_outputs(self, dst_name):
        """Delete a proxy output by dst name."""
        self._proxy_output.pop(dst_name)

    @staticmethod
    def copy_node_without_input_output(src_node, dst_node):
        """
        Copy a source node attribute to a new node, but not input and output.

        Args:
            src_node (Node): The copied node.
            dst_node (Node): The destination node.
        """
        dst_node.full_name = src_node.full_name
        dst_node.type = src_node.type
        dst_node.output_i = src_node.output_i
        dst_node.subnode_count = src_node.subnode_count
        dst_node.scope = src_node.scope
        dst_node.independent_layout = src_node.independent_layout
        dst_node.output_shape = src_node.output_shape
        dst_node.output_data_type = src_node.output_data_type
        dst_node.output_nums = src_node.output_nums
        dst_node.elem_types = src_node.elem_types
        dst_node.add_attr(src_node.attr)

    def __str__(self):
        return f'<Node, name: {self.name}, type: {self.type}>'
