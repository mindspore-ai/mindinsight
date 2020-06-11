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

    def test_judge_forward(self):
        """test judge_forward"""
        name1 = 'conv1'
        forward_list = {'conv1', 'relu'}
        result1 = self.converter_ins.judge_forward(name1, forward_list)
        assert result1 is True

        name2 = 'self.forward'
        result2 = self.converter_ins.judge_forward(name2, forward_list)
        assert result2 is True

    def test_find_left_parentheses(self):
        """test find_left_parentheses"""
        code = '''nn.Sequential(nn.Conv2d(in_dim, 6, 5, stride=1, padding=0, ),
                                                  nn.ReLU(),
                                                  nn.ReLU(True),
                                                  nn.MaxPool2d(2, 2),
                                                  nn.Conv2d(6, 16, 5, stride=1, padding=0),
                                                  nn.ReLU(inplace=False),
                                                  nn.MaxPool2d(2, 2))'''
        right_index = len(code) - 1
        left_index = code.index('nn.Conv2d')
        result = self.converter_ins.find_left_parentheses(code, right_index)
        assert result == left_index - 1

    def test_find_api(self):
        """test find_api"""
        code = '''nn.Sequential(nn.Conv2d(in_dim, 6, 5, stride=1, padding=0, ),
                                  nn.ReLU(),
                                  nn.ReLU(True),
                                  nn.MaxPool2d(2, 2),  # TODO padding
                                  nn.Conv2d(6, 16, 5, stride=1, padding=0),
                                  nn.ReLU(inplace=False),
                                  nn.MaxPool2d(2, 2))'''
        index = 0
        is_forward = False
        result = self.converter_ins.find_api(code, index, is_forward)
        assert result == 'nn.Sequential'

    def test_get_call_name(self):
        """test get_call_name"""
        code = '''nn.Sequential(nn.Conv2d(in_dim, 6, 5, stride=1, padding=0))'''
        end = len(code)
        call_name, index = self.converter_ins.get_call_name(code, end)

        assert call_name == ''
        assert index == -1

    def test_find_right_parentheses(self):
        """test find_right_parentheses"""
        code = '''nn.Sequential(nn.Conv2d(in_dim, 6, 5, stride=1, padding=0, ),
                                          nn.ReLU(),
                                          nn.ReLU(True),
                                          nn.MaxPool2d(2, 2),  # TODO padding
                                          nn.Conv2d(6, 16, 5, stride=1, padding=0),
                                          nn.ReLU(inplace=False),
                                          nn.MaxPool2d(2, 2))'''
        left_index = 0
        result = self.converter_ins.find_right_parentheses(code, left_index)
        assert_index = len(code) - 1
        assert result == assert_index

    # test convert_api with nn ops
    def test_convert_api_nn_layernorm(self):
        """Test convert_api function work ok when convert api nn.LayerNorm"""
        code = """
        def __init__(self, num_classes=1000):
            self.features = nn.SequentialCell([
            nn.LayerNorm((5, 10, 10), elementwise_affine=False),
            nn.ReLU(inplace=False)
            ])
        """
        api_name = 'nn.LayerNorm'
        start = code.find(api_name)

        layer_norm_info = NN_MAPPING.get(api_name)
        expected_ms_api_name = 'nn.LayerNorm'

        epsilon = layer_norm_info.pt_api.params.get('eps')

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('nn.LayerNorm((5, 10, 10), elementwise_affine=False)',
                                             '{}(normalized_shape=(5, 10, 10), epsilon={})'.format(
                                                 expected_ms_api_name, epsilon))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_nn_leaky_relu(self):
        """Test convert_api function work ok when convert api nn.LeakyReLU"""
        code = """
        def __init__(self, num_classes=1000):
            self.features = nn.SequentialCell([
            nn.LayerNorm((5, 10, 10), elementwise_affine=False),
            nn.LeakyReLU(0.3)])
        """
        api_name = 'nn.LeakyReLU'
        start = code.find(api_name)
        expected_ms_api_name = 'nn.LeakyReLU'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('nn.LeakyReLU(0.3)',
                                             '{}(alpha=0.3)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_nn_prelu(self):
        """Test convert_api function work ok when convert api nn.PReLU"""
        code = """
        input = torch.randn(2, 3, 5)
        nn.PReLU()(input)
        
        """
        api_name = 'nn.PReLU'
        start = code.find(api_name)
        expected_ms_api_name = 'nn.PReLU'
        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('nn.PReLU()(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_nn_softmax(self):
        """Test convert_api function work ok when convert api nn.Softmax"""
        code = """
        nn.Softmax(dim=1)(input)
        """
        api_name = 'nn.Softmax'
        expected_ms_api_name = 'nn.Softmax'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('nn.Softmax(dim=1)(input)',
                                             '{}(axis=1)(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    # test convert_api with torch dot ops
    def test_convert_api_torch_dot_abs(self):
        """Test convert_api function work ok when convert api torch.abs"""
        code = """
        torch.abs(input)
        """
        api_name = 'torch.abs'
        start = code.find(api_name)
        expected_ms_api_name = 'P.Abs'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.abs(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_acos(self):
        """Test convert_api function work ok when convert api torch.acos"""
        code = """
        torch.acos(input)
        """
        api_name = 'torch.acos'
        start = code.find(api_name)
        expected_ms_api_name = 'P.ACos'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.acos(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_cos(self):
        """Test convert_api function work ok when convert api torch.cos"""
        code = """
        torch.cos(input)
        """
        api_name = 'torch.cos'
        expected_ms_api_name = 'P.Cos'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.cos(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_exp(self):
        """Test convert_api function work ok when convert api torch.exp"""
        code = """
        torch.exp(input)
        """
        api_name = 'torch.exp'
        expected_ms_api_name = 'P.Exp'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.exp(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_log(self):
        """Test convert_api function work ok when convert api torch.log"""
        code = """
        torch.log(input)
        """
        api_name = 'torch.log'
        expected_ms_api_name = 'P.Log'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.log(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_pow(self):
        """Test convert_api function work ok when convert api torch.pow"""
        code = """
        torch.pow(a, exp)
        """
        api_name = 'torch.pow'
        expected_ms_api_name = 'P.Pow'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.pow(a, exp)',
                                             '{}()(a, exp)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_div(self):
        """Test convert_api function work ok when convert api torch.div"""
        code = """
        input = torch.randn(5)
        other = torch.randn(5)
        torch.div(input, other)
        """
        api_name = 'torch.div'
        expected_ms_api_name = 'P.Div'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)

        assert replaced_code == code.replace('torch.div(input, other)',
                                             '{}()(input, other)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_sin(self):
        """Test convert_api function work ok when convert api torch.sin"""
        code = """
        torch.sin(input)
        """
        api_name = 'torch.sin'
        expected_ms_api_name = 'P.Sin'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.sin(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_sqrt(self):
        """Test convert_api function work ok when convert api torch.sqrt"""
        code = """
        torch.sqrt(input)
        """
        api_name = 'torch.sqrt'
        expected_ms_api_name = 'P.Sqrt'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.sqrt(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_eye_with_n(self):
        """Test convert_api function work ok when convert api torch.eye"""
        code = """
        torch.eye(3)
        """
        api_name = 'torch.eye'
        expected_ms_api_name = 'P.Eye'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.eye(3)',
                                             '{}()(3, 3, mindspore.int32)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_eye_with_m(self):
        """Test convert_api function work ok when convert api torch.eye"""
        code = """
        torch.eye(3, 4)
        """
        api_name = 'torch.eye'
        expected_ms_api_name = 'P.Eye'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.eye(3, 4)',
                                             '{}()(3, 4, mindspore.int32)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_add_with_alpha_default(self):
        """Test convert_api function work ok when convert api torch.add"""
        code = """
        torch.add(input, value)
        """
        api_name = 'torch.add'
        expected_ms_api_name = 'P.TensorAdd'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.add(input, value)',
                                             '{}()(input, value)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_torch_dot_add_with_alpha_not_default(self):
        """Test convert_api function work ok when convert api torch.add"""
        code = """
        torch.add(input, value, 3)
        """
        api_name = 'torch.add'
        expected_ms_api_name = 'P.TensorAdd'
        start = code.find(api_name)

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('torch.add(input, value, 3)',
                                             '{}()(input, value*3)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    # test convert_api with F ops
    def test_convert_api_f_normalize(self):
        """Test convert_api function work ok when convert api F.normalize"""
        code = """
        input = torch.randn(2, 3, 5)
        F.normalize(input)
        """
        api_name = 'F.normalize'
        start = code.find(api_name)
        expected_ms_api_name = 'P.L2Normalize'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('F.normalize(input)',
                                             '{}(1, 1e-12)(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_f_sigmoid(self):
        """Test convert_api function work ok when convert api F.sigmoid"""
        code = """
        input = torch.randn(2, 3, 5)
        F.sigmoid(input)
        """
        api_name = 'F.sigmoid'
        start = code.find(api_name)
        expected_ms_api_name = 'P.Sigmoid'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('F.sigmoid(input)',
                                             '{}()(input)'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)

    # test convert_api with tensor dot ops
    def test_convert_api_tensor_dot_repeat(self):
        """Test convert_api function work ok when convert api .repeat"""
        code = """
        x.repeat(4, 2)
        """
        api_name = '.repeat'
        start = code.find(api_name)
        expected_ms_api_name = 'P.Tile'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('x.repeat(4, 2)',
                                             '{}()(x, {})'.format(expected_ms_api_name, '(4, 2,)'))
        assert new_start == start + len(expected_ms_api_name)

    def test_convert_api_tensor_dot_permute(self):
        """Test convert_api function work ok when convert api .permute"""
        code = """
        x.permute(2, 0, 1)
        """
        api_name = '.permute'
        start = code.find(api_name)
        expected_ms_api_name = 'P.Transpose'

        replaced_code, new_start = self.converter_ins.convert_api(code, start, api_name)
        assert replaced_code == code.replace('x.permute(2, 0, 1)',
                                             '{}()(x, (2, 0, 1,))'.format(expected_ms_api_name))
        assert new_start == start + len(expected_ms_api_name)
