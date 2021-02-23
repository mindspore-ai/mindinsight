# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define PyTorch graph node."""
import os

from mindinsight.mindconverter.graph_based_converter.third_party_graph.base import GraphNode
from mindinsight.mindconverter.graph_based_converter.constant import SEPARATOR_IN_SCOPE, NodeType


class InputNode(GraphNode):
    """
    PyTorch Input Node.

    Args:
        input_shape: Input shape of module.
    """

    def _get_arg_name(self, arg, variable_name):
        raise NotImplementedError()

    def to_code(self, ipt_args_in_construct: str, variable_name: str, output_var: str, code_fragment):
        raise NotImplementedError()

    def _get_raw_params(self, node):
        pass

    def clear_args_of_declaration(self):
        pass

    @property
    def op_name(self):
        return self._op_name

    @property
    def hash_key(self):
        pass

    def replace_with_arg(self, src_arg, tgt_arg):
        pass

    def add_input_and_output_shape(self, input_shape, output_shape):
        pass

    def __init__(self, name, input_shape):
        super(InputNode, self).__init__(node=None)
        self._op_name = 'Input'
        self.node_name = name
        self._op_params = {'input_shape': input_shape,
                           "output_shape": input_shape}
        self._node_type = NodeType.INPUTS.value

    @property
    def input_shape(self):
        """
        Input tensor shape of current node.

        Returns:
            tuple, tensor shape of input.
        """
        return self._op_params["input_shape"]

    @property
    def output_shape(self):
        """
        Output tensor shape.

        Returns:
            tuple, output tensor shape.
        """
        return self._op_params["output_shape"]

    def set_scope_name(self, original_input_scope_name):
        """
        Set scope name.
        Args:
            original_input_scope_name: Original input scope name needed to be linked.
        """
        prefix_name = original_input_scope_name.split(SEPARATOR_IN_SCOPE)[0]
        node_name = ''.join((self.node_type, '[input]'))
        self._scope_name = os.path.join(prefix_name, node_name)

    def set_successor_nodes(self, original_input_scope_names):
        """
        Set successor nodes.
        Args:
            original_input_scope_names: Original input scope names needed to be linked.
        """
        if isinstance(original_input_scope_names, list):
            self.successor_nodes = original_input_scope_names
        elif isinstance(original_input_scope_names, str):
            self.successor_nodes.append(original_input_scope_names)
        else:
            raise ValueError

    @property
    def real_name(self):
        return

    def to_ir(self):
        """
        No need to implement for now.
        """
        raise NotImplementedError()
