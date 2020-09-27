# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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

import pytest

from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class TestMappers:
    """Test Mappers."""
    @pytest.mark.parametrize('params', [{
        'input': {'op_name': 'onnx::BatchNormalization',
                  'params': {'epsilon': 1e-5,
                             'momentum': 0.9,
                             'output_shape': (1, 6, 224, 224)},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.BatchNorm2d',
                            'converted_params': {'num_features': 6,
                                                 'eps': 1e-5,
                                                 'momentum': 0.9}}
    }, {
        'input': {'op_name': 'onnx::Relu',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.ReLU',
                            'converted_params': dict()}
    }, {
        'input': {'op_name': 'onnx::MaxPool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.MaxPool2d',
                            'converted_params': {'kernel_size': (3, 3),
                                                 'stride': (2, 2),
                                                 'pad_mode': '"same"'}}
    }, {
        'input': {'op_name': 'onnx::AveragePool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.AvgPool2d',
                            'converted_params': {'kernel_size': (3, 3),
                                                 'stride': (2, 2),
                                                 'pad_mode': '"same"'}}
    }, {
        'input': {'op_name': 'onnx::GlobalAveragePool',
                  'params': {'input_shape': (1, 3, 10, 10),
                             'output_shape': (1, 3, 1, 1)},
                  'weights': ''},
        'expected_output': {'converter_name': 'nn.AvgPool2d',
                            'converted_params': {'kernel_size': (10, 10)}}
    }, {
        'input': {'op_name': 'onnx::Flatten',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Flatten',
                            'converted_params': dict()}
    }, {
        'input': {'op_name': 'onnx::Add',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'P.TensorAdd',
                            'converted_params': dict()}
    }])
    def test_mapper(self, params):
        """Test mapper function."""
        mapper = ONNXToMindSporeMapper()
        converter_name, converted_params = \
            mapper.convert(params['input']['op_name'], params['input']['params'], params['input']['weights'])
        assert params['expected_output']['converter_name'] == converter_name
        assert params['expected_output']['converted_params'] == converted_params
