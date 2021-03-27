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
"""Test fragment."""
from unittest import TestCase
from mindinsight.mindconverter.graph_based_converter.common.code_fragment import Fragment


class TestFragment(TestCase):
    """Tester of fragment."""

    def test_matmul(self):
        """Test matmul like operation's template."""
        template = {
            'var_0': {
                'init': [
                    'self.{var_0} = nn.MatMul()',
                    'self.{var_0}_w = Tensor(np.random.rand(*(2048, 1000)).astype(np.float32))'
                ],
                'construct': ['opt_{var_0} = self.{var_0}({inputs},self.{var_0}_w)']
            }
        }
        rewrite_data = {
            'var_0': {
                'operation': 'nn.MatMul',
                'output_type': 'tensor',
                'variable_name': "matmul", 'inputs': ["x"], 'args': {},
                'weights': {},
                'trainable_params': {}
            },
            'metadata': {
                'source': 'probs/MatMul', 'operation': 'MatMul', 'scope': 'Model/MatMul',
                'inputs': ['avg_pool/Mean:0', 'probs/MatMul/ReadVariableOp:0'],
                'inputs_shape': (1, 2048), 'outputs': ['probs/MatMul:0'], 'outputs_shape': [1, 1000],
                'precursor_nodes': ['avg_pool/Mean'], 'successor_nodes': ['probs/BiasAdd'],
                'attributes': {}
            }
        }
        fragment = Fragment(data_entity=rewrite_data, code_template=template, outputs=["opt_{var_0}"],
                            outputs_mapping=((0, 0),))
        code = fragment()
        init = code[0]
        construct = code[1]
        self.assertEqual(init, ['self.matmul = nn.MatMul()',
                                'self.matmul_w = Tensor(np.random.rand(*(2048, 1000)).astype(np.float32))'])
        self.assertEqual(construct, ['opt_matmul = self.matmul(x,self.matmul_w)'])
        self.assertEqual(fragment.get_outputs_by_idx(0), "opt_matmul")

    def test_biasadd(self):
        """Test biasadd like operation's template."""
        template = {
            'var_0': {
                'init': [
                    'self.{var_0} = P.TensorAdd()',
                    'self.{var_0}_bias = Tensor(np.random.rand(*(1000,)).astype(np.float32))'
                ],
                'construct': ['opt_{var_0} = self.{var_0}({inputs},self.{var_0}_bias)']
            }
        }
        rewrite_data = {
            'var_0': {
                'operation': 'P.TensorAdd',
                'output_type': 'tensor',
                'variable_name': "add", 'inputs': ["x"], 'args': {}, 'weights': {},
                'trainable_params': {}
            },
            'metadata': {
                'source': 'probs/BiasAdd', 'operation': 'Add', 'scope': 'Model/Add',
                'inputs': ['probs/MatMul:0', 'probs/BiasAdd/ReadVariableOp:0'], 'inputs_shape': (1, 1000),
                'outputs': ['probs/BiasAdd:0'], 'outputs_shape': [1, 1000], 'precursor_nodes': ['probs/MatMul'],
                'successor_nodes': ['probs/Softmax'], 'attributes': {}
            }
        }
        fragment = Fragment(data_entity=rewrite_data, code_template=template, outputs=["opt_{var_0}"],
                            outputs_mapping=((0, 0),))
        code = fragment()
        init = code[0]
        construct = code[1]
        self.assertEqual(init, ['self.add = P.TensorAdd()',
                                'self.add_bias = Tensor(np.random.rand(*(1000,)).astype(np.float32))'])
        self.assertEqual(construct, ['opt_add = self.add(x,self.add_bias)'])
        self.assertEqual(fragment.get_outputs_by_idx(0), "opt_add")

    def test_transpose(self):
        """Test transpose like operation's template."""
        template = {
            'var_0': {
                'init': ['self.{var_0} = P.Transpose()'],
                'construct': ['opt_{var_0} = self.{var_0}({inputs}, (0, 3, 1, 2))']
            }
        }
        rewrite_data = {
            'var_0': {
                'operation': 'P.Transpose',
                'output_type': 'tensor',
                'variable_name': "transpose", 'inputs': ["x"], 'args': {}, 'weights': {},
                'trainable_params': {}
            }
        }
        fragment = Fragment(data_entity=rewrite_data, code_template=template, outputs=["opt_{var_0}"],
                            outputs_mapping=((0, 0),))
        code = fragment()
        init = code[0]
        construct = code[1]
        self.assertEqual(init, ['self.transpose = P.Transpose()'])
        self.assertEqual(construct, ['opt_transpose = self.transpose(x, (0, 3, 1, 2))'])
        self.assertEqual(fragment.get_outputs_by_idx(0), "opt_transpose")

    def test_split(self):
        """Test split like operation's template."""
        template = {
            'var_0': {
                'init': ['self.{var_0} = P.Split(axis={axis}, output_num={output_num})'],
                'construct': ['opt_{var_0} = self.{var_0}({inputs})']
            }
        }
        rewrite_data = {
            'var_0': {
                'operation': 'P.Split',
                'variable_name': "split",
                'output_type': 'array',
                'inputs': ["x"],
                'args': {"axis": 1, "output_num": 2}, 'weights': {},
                'trainable_params': {}
            }
        }
        fragment = Fragment(data_entity=rewrite_data, code_template=template, outputs=["opt_{var_0}"],
                            outputs_mapping=((0, 0),))
        code = fragment()
        init = code[0]
        construct = code[1]
        self.assertEqual(init, ['self.split = P.Split(axis=1, output_num=2)'])
        self.assertEqual(construct, ['opt_split = self.split(x)'])
        self.assertEqual(fragment.get_outputs_by_idx(0, 1), 'opt_split[1]')
