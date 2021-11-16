# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Define Pytorch graph node."""
from mindconverter.graph_based_converter.third_party_graph.base import GraphNode
from mindconverter.graph_based_converter.constant import NodeType


class PytorchGraphNode(GraphNode):
    """
    Pytorch Graph Node.

    Args:
        node (PytorchNode): Pytorch Node Object.
        weight (list): List of recording node weights
    """
    _type_frozen = False
    _module_name_frozen = False

    def __init__(self, node, weight=None):
        super(PytorchGraphNode, self).__init__(node)
        self._op_params = node.params.attribute_dict
        self._op_name = node.raw_node.kind()
        self._scope_name = node.scope_name
        self._weight = weight

    def clear_args_of_declaration(self):
        """Clear `self._args_in_code`."""
        self._args_in_code = dict()

    def _get_arg_name(self, arg, variable_name):
        """No need to implement for now."""
        raise NotImplementedError

    @property
    def hash_key(self):
        """
        Return unique hash key of current node.

        Returns:
            str, hash key.
        """
        if self._node_type not in {NodeType.CLASS.value, NodeType.FUNC.value, NodeType.MODULE.value}:
            self._hash_key = self._op_name.lower()
        return self._hash_key

    @hash_key.setter
    def hash_key(self, h):
        """
        Setter of hash key.

        Args:
            h (str): Key.
        """
        self._hash_key = h

    @property
    def op_name(self):
        """
        Op name in TorchScript.

        Returns:
            str, op_name.
        """
        return self._op_name

    @property
    def real_name(self):
        return

    def add_input_and_output_shape(self, input_shape, output_shape):
        """
        Add the node input shape.

        Args:
            output_shape (tuple): Output tensor shape.
            input_shape (tuple): Input tensor shape.
        """
        self._ipt_shape = input_shape
        self._opt_shape = output_shape

    def to_code(self, ipt_args_in_construct: str, variable_name: str, output_var: str, code_fragment):
        """No need to implement for now."""
        raise NotImplementedError

    def to_ir(self):
        """No need to implement for now."""
        raise NotImplementedError

    def _get_raw_params(self, node):
        """No need to implement for now."""
        raise NotImplementedError

    def replace_with_arg(self, src_arg, tgt_arg):
        """No need to implement for now."""
        raise NotImplementedError
