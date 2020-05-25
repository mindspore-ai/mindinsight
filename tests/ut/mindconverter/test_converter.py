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
