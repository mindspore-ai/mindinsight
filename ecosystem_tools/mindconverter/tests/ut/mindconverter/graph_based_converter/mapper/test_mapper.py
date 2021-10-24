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
"""Test all operator mappers on transformation from pytorch to mindspore."""
import numpy as np
import pytest

from mindconverter.graph_based_converter.third_party_graph.base import NodeWeight
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class TestMappers:
    """Test Mappers."""

    @pytest.mark.parametrize('params', [{
        'input': {'op_name': 'onnx::Conv',
                  'params': {'dilations': [1, 1],
                             'group': 1,
                             'pads': [1, 2, 3, 4],
                             'strides': [1, 1]},
                  'weights': {'weight': np.zeros((64, 3, 1, 1), dtype=np.int32)}},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Conv',
                  'params': {'dilations': [1, 1],
                             'group': 1,
                             'pads': [0, 0, 0, 0],
                             'strides': [1, 1]},
                  'weights': {'weight': np.zeros((64, 3, 2, 2), dtype=np.int32)}},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Gemm',
                  'params': dict(),
                  'weights': {'weight': np.zeros((10, 3), dtype=np.int32),
                              'bias': np.zeros((10, 1), dtype=np.int32)}},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::BatchNormalization',
                  'params': {'epsilon': 1e-5,
                             'momentum': 0.9,
                             'output_shape': (1, 6, 224, 224)},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Relu',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::MaxPool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2],
                             'input_shape': (1, 3, 224, 224),
                             'output_shape': (1, 3, 112, 112)},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::AveragePool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2],
                             'input_shape': (1, 3, 224, 224),
                             'output_shape': (1, 3, 112, 112)},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::GlobalAveragePool',
                  'params': {'input_shape': (1, 3, 10, 10),
                             'output_shape': (1, 3, 1, 1)},
                  'weights': ''},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Flatten',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Add',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'value': 0,
                             'mode': 'constant'},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'mode': 'reflect'},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'value': 1,
                             'mode': 'constant'},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'mode': 'edge'},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::ReduceMean',
                  'params': {'keepdims': 0,
                             'axes': [1, 2]},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::ReduceMean',
                  'params': {'keepdims': 1,
                             'axes': [1]},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Concat',
                  'params': {'axis': 0},
                  'weights': dict()},
        'expected_output': {}
    }, {
        'input': {'op_name': 'onnx::Clip',
                  'params': {},
                  'weights': [
                      NodeWeight("min", np.array(0).astype(np.float32), 0),
                      NodeWeight("min", np.array(6).astype(np.float32), 0)]},
        'expected_output': {}
    }])
    def test_mapper(self, params):
        """Test mapper function."""
        _, _, _, _ = ONNXToMindSporeMapper.convert(params['input']['op_name'],
                                                   params['input']['params'],
                                                   params['input']['weights'])
