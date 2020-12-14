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
"""This file is used to identify the type of the node."""
import sys

from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError

_ACTIVATIONS = [
    'elu',
    'fastgelu',
    'gelu',
    'hsigmoid',
    'hswish',
    'leakyrelu',
    'logsigmoid',
    'logsoftmax',
    'prelu',
    'relu',
    'relu6',
    'reluv2',
    'sigmoid',
    'softmax',
    'tanh'
]


class NodeTypeIdentifier:
    """Node type identifier."""

    def __init__(self, node_type):
        self.identify_func = self.get_identify_func(node_type)

    @staticmethod
    def get_identify_func(node_type):
        """
        Get the identify function in this module.

        Args:
            node_type (str): The node type.

        Returns:
            function, the identify function.
        """
        # the name of the identity function should start with 'is_' and end with '_node'
        target_name = 'is_' + node_type + '_node'
        cur_module = sys.modules[__name__]
        for sub_module in dir(cur_module):
            # the rule to get the identify function
            if sub_module == target_name:
                return getattr(cur_module, sub_module)
        raise DebuggerParamValueError("Invalid identify type.")

    def is_match(self, *args, **kwargs):
        """Check if the input match the idenfity function."""
        return self.identify_func(*args, **kwargs)


def is_parameter_node(node):
    """
    Check if the node is weight type.

    Args:
        node (Node): The node object.

    Returns:
        bool, if the node is weight type.
    """
    return bool(node.type == NodeTypeEnum.PARAMETER.value)


def is_weight_node(node):
    """
    Check if the node is weight type.

    Args:
        node (Node): The node object.

    Returns:
        bool, if the node is weight type.
    """
    if node.type == NodeTypeEnum.PARAMETER.value:
        full_name = node.full_name.lower()
        weight_flag = False
        if full_name.endswith('.weight') or full_name.endswith('.bias'):
            weight_flag = True
        if weight_flag and 'optimizer-' not in full_name and not full_name.startswith('gradients/'):
            return True
    return False


def is_activation_node(node, condition=None):
    """
    Check if the node is activation type.

    Args:
        node (Node): The node object.
        condition (dict): Filter condition.

            - activation_func (Union[str, list[str]): The target functions.

    Returns:
        bool, if the node is activation type.
    """
    activation_funcs = condition.get('activation_func') if condition else _ACTIVATIONS
    if not activation_funcs:
        activation_funcs = _ACTIVATIONS
    if not isinstance(activation_funcs, list):
        activation_funcs = [activation_funcs]

    if not is_gradient_node(node):
        node_type = node.type
        for activation_name in activation_funcs:
            if node_type.lower() == activation_name:
                return True
    return False


def is_gradient_node(node):
    """
    Check if the node is gradient type.

    Args:
        node (Node): The node object.

    Returns:
        bool, if the node is gradient type.
    """
    full_name = node.full_name.lower()
    if full_name.startswith('gradients/') and \
            node.type not in [NodeTypeEnum.PARAMETER.value, NodeTypeEnum.CONST.value]:
        return True
    return False


def is_tensor_node(node):
    """
    Check if the node is tensor type.

    Args:
        node (Node): The node object.

    Returns:
        bool, if the node is tensor type.
    """
    if node is not None:
        return True
    return False
