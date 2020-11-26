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
"""Test hierarchical tree module."""
import os
import shutil
from unittest import mock

import pytest

from mindinsight.mindconverter.graph_based_converter.hierarchical_tree.hierarchical_tree import HierarchicalTree
from mindinsight.mindconverter.graph_based_converter.third_party_graph.pytorch_graph_node import PyTorchGraphNode
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindinsight.mindconverter.graph_based_converter.constant import NodeType

from tests.ut.mindconverter.graph_based_converter.conftest import TEST_BASE_PATH


class TestHierarchicalTree:
    """Test the class of HierarchicalTree."""

    def test_tree_identifier(self):
        """Test tree_identifier"""
        tree = HierarchicalTree()
        assert isinstance(tree.tree_identifier, str)

    @mock.patch(
        '.'.join((TEST_BASE_PATH, 'third_party_graph.pytorch_graph_node.PyTorchGraphNode._get_raw_params')))
    def test_insert(self, get_raw_params):
        """Test insert"""
        get_raw_params.return_value = []
        tree = HierarchicalTree()
        pt_node = PyTorchGraphNode()
        tree.insert(pt_node, 'ResNet')
        assert tree.root == 'ResNet'

    def test_remove(self):
        """Test remove function."""
        tree = HierarchicalTree()
        tree.create_node(
            tag='node_root',
            identifier='root',
            parent=None,
            data=None
        )
        node = tree.get_node('root')
        tree.remove(node)
        assert tree.root is None

    @mock.patch(
        '.'.join((TEST_BASE_PATH, 'third_party_graph.pytorch_graph_node.PyTorchGraphNode._get_raw_params')))
    def test_shrink(self, get_raw_params):
        """Test shrink function."""
        params = {'root': {},
                  'root/child0': {},
                  'root/child0/child1': {}}
        tree = self._create_tree(get_raw_params=get_raw_params, params=params)
        node = tree.get_node('root/child0')
        tree.shrink(node)
        assert tree.leaves()[0].tag == 'child1'

    @pytest.mark.parametrize('params', [{
        'tree_params': {'root': {'op_name': 'Root',
                                 'precursor_nodes': [],
                                 'successor_nodes': ['root/relu'],
                                 'node_type': NodeType.MODULE.value,
                                 'input_shape': [1, 3, 224, 224],
                                 'output_shape': [1, 1, 224, 224]},
                        'root/relu': {'op_name': 'onnx::Relu',
                                      'precursor_nodes': ['root'],
                                      'successor_nodes': ['root/unknown'],
                                      'node_type': NodeType.OPERATION.value,
                                      'input_shape': [1, 3, 224, 224],
                                      'output_shape': [1, 3, 224, 224]},
                        'root/unknown': {'op_name': 'onnx::Unknown',
                                         'precursor_nodes': ['root/relu'],
                                         'successor_nodes': [],
                                         'node_type': NodeType.OPERATION.value,
                                         'input_shape': [1, 3, 224, 224],
                                         'output_shape': [1, 1, 224, 224]}},
        'report_dir': 'report_folder'
    }, {
        'tree_params': {'root': {'op_name': 'Root',
                                 'precursor_nodes': [],
                                 'successor_nodes': ['root/relu'],
                                 'node_type': NodeType.MODULE.value,
                                 'input_shape': [1, 3, 224, 224],
                                 'output_shape': [1, 1, 224, 224]},
                        'root/relu': {'op_name': 'onnx::Relu',
                                      'precursor_nodes': ['root'],
                                      'successor_nodes': ['root/unknown'],
                                      'node_type': NodeType.OPERATION.value,
                                      'input_shape': [1, 3, 224, 224],
                                      'output_shape': [1, 3, 224, 224]},
                        'root/unknown': {'op_name': 'onnx::Unknown',
                                         'precursor_nodes': ['root/relu'],
                                         'successor_nodes': [],
                                         'node_type': NodeType.OPERATION.value,
                                         'input_shape': [1, 3, 224, 224],
                                         'output_shape': [1, 1, 224, 224]}},
        'report_dir': None
    }])
    @mock.patch(
        '.'.join((TEST_BASE_PATH, 'third_party_graph.pytorch_graph_node.PyTorchGraphNode._get_raw_params')))
    def test_save_source_file(self, get_raw_params, params):
        """Test save_source_file function."""
        tree_params = params['tree_params']
        out_folder = 'out_folder'
        report_folder = params['report_dir']
        model_name = 'model_name'
        mapper = ONNXToMindSporeMapper()

        tree = self._create_tree(get_raw_params=get_raw_params, params=tree_params)
        tree.save_source_files(out_folder, mapper, model_name, report_folder)

        out_path = os.path.realpath(os.path.join(out_folder, f"{model_name}.py"))
        report_folder_test = report_folder if report_folder else out_folder
        report_path = os.path.realpath(
            os.path.join(report_folder_test, f"report_of_{model_name}.txt"))
        try:
            assert os.path.exists(out_path)
            assert os.path.exists(report_path)
            with open(out_path, 'r') as out_r:
                code = out_r.read()
                assert 'nn.ReLU' in code
                assert 'onnx.Unknown' in code
            with open(report_path, 'r') as report_r:
                report = report_r.read()
                assert "[UnConvert] 'onnx::Unknown' didn't convert." in report
                assert "Converted Rate: 50.00%." in report
        finally:
            shutil.rmtree(out_folder)
            if report_folder:
                shutil.rmtree(report_folder)

    @staticmethod
    def _create_node(key, val, weight, input_shape, output_shape):
        """Create node."""
        node = PyTorchGraphNode(weight=weight)
        node.add_input_and_output_shape(input_shape, output_shape)
        node.tag = key.split('/')[-1] if len(key.split('/')) > 1 else key
        node.op_name = val['op_name'] if val.get('op_name') else None
        node.precursor_nodes = val['precursor_nodes'] if val.get('precursor_nodes') else []
        node.successor_nodes = val['successor_nodes'] if val.get('successor_nodes') else []
        node.node_type = val['node_type'] if val.get('node_type') else None
        return node

    @staticmethod
    def _create_tree(get_raw_params, params):
        """Create tree."""
        tree = HierarchicalTree()
        for key, val in params.items():
            input_shape = val['input_shape'] if val.get('input_shape') else []
            output_shape = val['output_shape'] if val.get('output_shape') else []
            get_raw_params.return_value = val['op_params'] if val.get('op_params') else dict()
            weight = val['weight'] if val.get('weight') else None

            node = TestHierarchicalTree._create_node(key, val, weight, input_shape, output_shape)

            tree.create_node(
                tag=node.tag,
                identifier=key,
                parent='/'.join(key.split('/')[:-1]) if len(key.split('/')) > 1 else None,
                data=node
            )
        return tree
