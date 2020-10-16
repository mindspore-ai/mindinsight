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
import numpy as np
import pytest

from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from tests.utils import mindspore


class TestMappers:
    """Test Mappers."""
    @pytest.mark.parametrize('params', [{
        'input': {'op_name': 'onnx::Conv',
                  'params': {'dilations': [1, 1],
                             'group': 1,
                             'pads': [1, 2, 3, 4],
                             'strides': [1, 1]},
                  'weights': {'weight': mindspore.Tensor(np.zeros([64, 3, 1, 1], dtype=np.int32))}},
        'expected_output': {'converter_name': 'nn.Conv2d',
                            'converted_params': {'in_channels': 3,
                                                 'out_channels': 64,
                                                 'kernel_size': (1, 1),
                                                 'stride': (1, 1),
                                                 'padding': (1, 3, 2, 4),
                                                 'pad_mode': '\"pad\"',
                                                 'dilation': (1, 1),
                                                 'group': 1},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Conv',
                  'params': {'dilations': [1, 1],
                             'group': 1,
                             'pads': [0, 0, 0, 0],
                             'strides': [1, 1]},
                  'weights': {'weight': mindspore.Tensor(np.zeros([64, 3, 2, 2], dtype=np.int32))}},
        'expected_output': {'converter_name': 'nn.Conv2d',
                            'converted_params': {'in_channels': 3,
                                                 'out_channels': 64,
                                                 'kernel_size': (2, 2),
                                                 'stride': (1, 1),
                                                 'padding': 0,
                                                 'pad_mode': '\"valid\"',
                                                 'dilation': (1, 1),
                                                 'group': 1},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Gemm',
                  'params': dict(),
                  'weights': {'weight': mindspore.Tensor(np.zeros([10, 3], dtype=np.int32)),
                              'bias': mindspore.Tensor(np.zeros([10, 1], dtype=np.int32))}},
        'expected_output': {'converter_name': 'nn.Dense',
                            'converted_params': {'in_channels': 3,
                                                 'out_channels': 10,
                                                 'has_bias': True},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::BatchNormalization',
                  'params': {'epsilon': 1e-5,
                             'momentum': 0.9,
                             'output_shape': (1, 6, 224, 224)},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.BatchNorm2d',
                            'converted_params': {'num_features': 6,
                                                 'eps': 1e-5,
                                                 'momentum': 0.9},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Relu',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.ReLU',
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::MaxPool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.MaxPool2d',
                            'converted_params': {'kernel_size': (3, 3),
                                                 'stride': (2, 2),
                                                 'pad_mode': '"same"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::AveragePool',
                  'params': {'kernel_shape': [3, 3],
                             'pads': [1, 1, 1, 1],
                             'strides': [2, 2]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.AvgPool2d',
                            'converted_params': {'kernel_size': (3, 3),
                                                 'stride': (2, 2),
                                                 'pad_mode': '"same"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::GlobalAveragePool',
                  'params': {'input_shape': (1, 3, 10, 10),
                             'output_shape': (1, 3, 1, 1)},
                  'weights': ''},
        'expected_output': {'converter_name': 'nn.AvgPool2d',
                            'converted_params': {'kernel_size': (10, 10)},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Flatten',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Flatten',
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Add',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'P.TensorAdd',
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'value': 0,
                             'mode': 'constant'},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Pad',
                            'converted_params': {'paddings': ((0, 2), (1, 3)),
                                                 'mode': '\"CONSTANT\"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'mode': 'reflect'},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Pad',
                            'converted_params': {'paddings': ((0, 2), (1, 3)),
                                                 'mode': '\"REFLECT\"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'value': 1,
                             'mode': 'constant'},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Pad',
                            'converted_params': {'paddings': ((0, 2), (1, 3)),
                                                 'mode': '{UNSUPPORTED: value is NOT 0}\"CONSTANT\"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Pad',
                  'params': {'pads': [0, 1, 2, 3],
                             'mode': 'edge'},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.Pad',
                            'converted_params': {'paddings': ((0, 2), (1, 3)),
                                                 'mode': '{UNSUPPORTED: \"edge\"}\"UNKNOWN\"'},
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::ReduceMean',
                  'params': {'keepdims': 0,
                             'axes': [1, 2]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'P.ReduceMean',
                            'converted_params': {'keep_dims': False},
                            'converted_settings': {'values': {'axis': (1, 2)}}}
    }, {
        'input': {'op_name': 'onnx::ReduceMean',
                  'params': {'keepdims': 1,
                             'axes': [1]},
                  'weights': dict()},
        'expected_output': {'converter_name': 'P.ReduceMean',
                            'converted_params': {'keep_dims': True},
                            'converted_settings': {'values': {'axis': 1}}}
    }, {
        'input': {'op_name': 'onnx::Concat',
                  'params': {'axis': 0},
                  'weights': dict()},
        'expected_output': {'converter_name': 'P.Concat',
                            'converted_params': {'axis': 0},
                            'converted_settings': {'input_type': "list"}}
    }, {
        'input': {'op_name': 'onnx::Clip',
                  'params': {'max': 6,
                             'min': 0},
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.ReLU6',
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Clip',
                  'params': dict(),
                  'weights': dict()},
        'expected_output': {'converter_name': 'nn.ReLU',
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }, {
        'input': {'op_name': 'onnx::Clip',
                  'params': {'max': 3,
                             'min': 2},
                  'weights': dict()},
        'expected_output': {'converter_name': None,
                            'converted_params': dict(),
                            'converted_settings': dict()}
    }])
    def test_mapper(self, params):
        """Test mapper function."""
        mapper = ONNXToMindSporeMapper()
        converter_name, converted_params, converted_settings = \
            mapper.convert(params['input']['op_name'], params['input']['params'], params['input']['weights'])
        assert params['expected_output']['converter_name'] == converter_name
        assert params['expected_output']['converted_params'] == converted_params
        assert params['expected_output']['converted_settings'] == converted_settings
