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
"""Test Name manager module."""
from unittest import mock, TestCase
from mindinsight.mindconverter.graph_based_converter.hierarchical_tree.hierarchical_tree import HierarchicalTree
from mindinsight.mindconverter.graph_based_converter.third_party_graph.pytorch_graph_node import PyTorchGraphNode


class TestHierarchicalTree(TestCase):
    """Test the class of HierarchicalTree."""

    def test_tree_identifier(self):
        """Test tree_identifier"""
        tree = HierarchicalTree()
        self.assertIsInstance(tree.tree_identifier, str)

    @mock.patch(
        'mindinsight.mindconverter.graph_based_converter.' \
        'third_party_graph.pytorch_graph_node.PyTorchGraphNode._get_raw_params')
    def test_insert(self, get_raw_params):
        """Test insert"""
        get_raw_params.return_value = []
        tree = HierarchicalTree()
        pt_node = PyTorchGraphNode()
        tree.insert(pt_node, 'ResNet', (1, 3, 224, 224), (1, 64, 112, 112))
        self.assertEqual(tree.root, 'ResNet')
