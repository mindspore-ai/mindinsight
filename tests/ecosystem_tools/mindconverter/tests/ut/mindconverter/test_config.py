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
"""Test config module."""
from collections import OrderedDict

import pytest

from mindconverter.config import APIPt, REQUIRED


class TestAPIBase:
    """Test the class of APIPt."""
    function_name = "func"

    @pytest.mark.parametrize('parameters', ['(out.size(0), -1', '(2, 1, 0)'])
    def test_parse_args_exception(self, parameters):
        """Test parse arguments exception"""
        parameters_spec = OrderedDict(in_channels=REQUIRED, out_channels=REQUIRED)
        api_parser = APIPt(self.function_name, parameters_spec)
        with pytest.raises(ValueError):
            api_parser.parse_args(api_parser.name, parameters)

    def test_parse_single_arg(self):
        """Test parse one argument"""
        source = '(1)'
        parameters_spec = OrderedDict(in_channels=REQUIRED)
        api_parser = APIPt(self.function_name, parameters_spec)
        parsed_args = api_parser.parse_args(api_parser.name, source)

        assert parsed_args['in_channels'] == '1'

    def test_parse_args(self):
        """Test parse multiple arguments"""
        source = '(1, 2)'
        parameters_spec = OrderedDict(in_channels=REQUIRED, out_channels=REQUIRED)
        api_parser = APIPt(self.function_name, parameters_spec)
        parsed_args = api_parser.parse_args(api_parser.name, source)

        assert parsed_args['in_channels'] == '1'
        assert parsed_args['out_channels'] == '2'
