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
"""Test Converter"""
from mindinsight.mindconverter.converter import Converter
from mindinsight.mindconverter.config import NN_MAPPING


class TestConverter:
    """Test Converter"""

    converter_ins = Converter()

    # test convert_api with nn ops
    def test_convert_api_nn_layernorm(self):
        """Test convert_api function work ok when convert api nn.LayerNorm"""
        code = "nn.LayerNorm((5, 10, 10), elementwise_affine=False)"
        api_name = 'nn.LayerNorm'

        layer_norm_info = NN_MAPPING.get(api_name)
        expected_ms_api_name = 'nn.LayerNorm'

        epsilon = layer_norm_info.pt_api.params.get('eps')

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('nn.LayerNorm((5, 10, 10), elementwise_affine=False)',
                                             '{}(normalized_shape=(5, 10, 10), epsilon={})'.format(
                                                 expected_ms_api_name, epsilon))

    def test_convert_api_nn_leaky_relu(self):
        """Test convert_api function work ok when convert api nn.LeakyReLU"""
        code = "nn.LeakyReLU(0.3)"
        expected_ms_api_name = 'nn.LeakyReLU'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('nn.LeakyReLU(0.3)',
                                             '{}(alpha=0.3)'.format(expected_ms_api_name))

    def test_convert_api_nn_prelu(self):
        """Test convert_api function work ok when convert api nn.PReLU"""
        code = "nn.PReLU()(input)"
        expected_ms_api_name = 'nn.PReLU'
        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('nn.PReLU()(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_nn_softmax(self):
        """Test convert_api function work ok when convert api nn.Softmax"""
        code = "nn.Softmax(dim=1)"
        expected_ms_api_name = 'nn.Softmax'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('nn.Softmax(dim=1)',
                                             '{}(axis=1)'.format(expected_ms_api_name))

    # test convert_api with torch dot ops
    def test_convert_api_torch_dot_abs(self):
        """Test convert_api function work ok when convert api torch.abs"""
        code = "torch.abs(input)"
        expected_ms_api_name = 'P.Abs'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.abs(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_acos(self):
        """Test convert_api function work ok when convert api torch.acos"""
        code = "torch.acos(input)"
        expected_ms_api_name = 'P.ACos'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.acos(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_cos(self):
        """Test convert_api function work ok when convert api torch.cos"""
        code = "torch.cos(input)"
        expected_ms_api_name = 'P.Cos'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.cos(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_exp(self):
        """Test convert_api function work ok when convert api torch.exp"""
        code = "torch.exp(input)"
        expected_ms_api_name = 'P.Exp'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.exp(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_log(self):
        """Test convert_api function work ok when convert api torch.log"""
        code = "torch.log(input)"
        expected_ms_api_name = 'P.Log'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.log(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_pow(self):
        """Test convert_api function work ok when convert api torch.pow"""
        code = "torch.pow(a, exp)"
        expected_ms_api_name = 'P.Pow'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.pow(a, exp)',
                                             '{}()(a, exp)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_div(self):
        """Test convert_api function work ok when convert api torch.div"""
        code = "torch.div(input, other)"
        expected_ms_api_name = 'P.Div'

        replaced_code = self.converter_ins.convert_api(code)

        assert replaced_code == code.replace('torch.div(input, other)',
                                             '{}()(input, other)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_sin(self):
        """Test convert_api function work ok when convert api torch.sin"""
        code = "torch.sin(input)"
        expected_ms_api_name = 'P.Sin'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.sin(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_sqrt(self):
        """Test convert_api function work ok when convert api torch.sqrt"""
        code = "torch.sqrt(input)"
        expected_ms_api_name = 'P.Sqrt'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.sqrt(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_eye_with_n(self):
        """Test convert_api function work ok when convert api torch.eye"""
        code = "torch.eye(3)"
        expected_ms_api_name = 'P.Eye'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.eye(3)',
                                             '{}()(3, 3, mindspore.int32)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_eye_with_m(self):
        """Test convert_api function work ok when convert api torch.eye"""
        code = "torch.eye(3, 4)"
        expected_ms_api_name = 'P.Eye'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.eye(3, 4)',
                                             '{}()(3, 4, mindspore.int32)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_add_with_alpha_default(self):
        """Test convert_api function work ok when convert api torch.add"""
        code = "torch.add(input, value)"
        expected_ms_api_name = 'P.TensorAdd'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.add(input, value)',
                                             '{}()(input, value)'.format(expected_ms_api_name))

    def test_convert_api_torch_dot_add_with_alpha_not_default(self):
        """Test convert_api function work ok when convert api torch.add"""
        code = "torch.add(input, value, 3)"
        expected_ms_api_name = 'P.TensorAdd'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('torch.add(input, value, 3)',
                                             '{}()(input, value*3)'.format(expected_ms_api_name))

    # test convert_api with F ops
    def test_convert_api_f_normalize(self):
        """Test convert_api function work ok when convert api F.normalize"""
        code = "F.normalize(input)"
        expected_ms_api_name = 'P.L2Normalize'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('F.normalize(input)',
                                             '{}(1, 1e-12)(input)'.format(expected_ms_api_name))

    def test_convert_api_f_sigmoid(self):
        """Test convert_api function work ok when convert api F.sigmoid"""
        code = "F.sigmoid(input)"
        expected_ms_api_name = 'P.Sigmoid'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('F.sigmoid(input)',
                                             '{}()(input)'.format(expected_ms_api_name))

    # test convert_api with tensor dot ops
    def test_convert_api_tensor_dot_repeat(self):
        """Test convert_api function work ok when convert api .repeat"""
        code = "x.repeat(4, 2)"
        expected_ms_api_name = 'P.Tile'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('x.repeat(4, 2)',
                                             '{}()(x, {})'.format(expected_ms_api_name, '(4, 2,)'))

    def test_convert_api_tensor_dot_permute(self):
        """Test convert_api function work ok when convert api .permute"""
        code = "x.permute(2, 0, 1)"
        expected_ms_api_name = 'P.Transpose'

        replaced_code = self.converter_ins.convert_api(code)
        assert replaced_code == code.replace('x.permute(2, 0, 1)',
                                             '{}()(x, (2, 0, 1,))'.format(expected_ms_api_name))
