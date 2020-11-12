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
Function:
    Test query debugger node type identifier.
Usage:
    pytest tests/ut/debugger
"""
from unittest.mock import MagicMock

import pytest

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.stream_cache.node_type_identifier import NodeTypeIdentifier


class TestNodeTypeIdentifier:
    """Test NodeTypeIdentifier."""

    @pytest.mark.parametrize("name, node_type, result", [
        ('Default/mock/node_name.bias', "Parameter", True),
        ('Default/mock/node_name.weight', "Parameter", True),
        ('Gradients/mock/node_name.bias', "Parameter", False),
        ('Default/optimizer-mock/node_name.bias', "Parameter", False),
    ])
    def test_weight_node(self, name, node_type, result):
        """Test weight node."""
        identifier = NodeTypeIdentifier('weight')
        mock_node = MagicMock(type=node_type)
        mock_node.name = name
        res = identifier.is_match(mock_node)
        assert res is result

    @pytest.mark.parametrize("name, node_type, result", [
        ('Default/mock/node_name.bias', "Parameter", False),
        ('Gradients/mock/node_name.bias', "Parameter", False),
        ('Gradients/mock-mock/node_name.bias', "ReluGrad", True),
    ])
    def test_gradient_node(self, name, node_type, result):
        """Test gradient node."""
        identifier = NodeTypeIdentifier('gradient')
        mock_node = MagicMock(type=node_type)
        mock_node.name = name
        res = identifier.is_match(mock_node)
        assert res is result

    @pytest.mark.parametrize("name, node_type, condition, result", [
        ('Default/mock/relu_ReLU-op11', "ReLU", None, True),
        ('Gradients/mock/relu_ReLU-op11', "ReLU", None, False),
        ('Default/mock/relu_ReLU-op11', "Parameter", None, False),
        ('Default/mock/relu_ReLU-op11', "ReLU", {'activation_func': 'Softmax'}, False),
        ('Default/mock/relu_ReLU-op11', "Softmax", {'activation_func': ['ReLU', 'Softmax']}, True)
    ])
    def test_activate_node(self, name, node_type, condition, result):
        """Test activate node."""
        identifier = NodeTypeIdentifier('activation')
        mock_node = MagicMock(type=node_type)
        mock_node.name = name
        res = identifier.is_match(mock_node, condition)
        assert res is result

    def test_invalid_func(self):
        """Test invalid func."""
        with pytest.raises(DebuggerParamValueError, match='Invalid identify type.'):
            NodeTypeIdentifier('invalid_type')
