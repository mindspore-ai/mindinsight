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
"""Test the framework parser module."""
import csv
import os
import shutil
import tempfile
from unittest import mock

import pytest
from marshmallow import ValidationError

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerPathErrorException, ProfilerDirNotFoundException, \
    ProfilerFileNotFoundException
from mindinsight.profiler.parser.framework_parser import FrameworkParser
from tests.ut.profiler import PROFILER_DIR, RAW_DATA_BASE


def get_framework_result(file_path):
    """
    Get framework result from the framework file.

    Args:
        file_path (str): The framework file path.

    Returns:
        list[list], the parsed framework information.
    """
    result = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            result.append(row)
    return result


class TestFrameworkParser:
    """Test the class of `FrameworkParser`."""
    def setup_method(self):
        """Initialization before test case execution."""
        FrameworkParser._raw_data_dir = RAW_DATA_BASE

        self._output_path_1 = tempfile.mkdtemp(prefix='test_framework_parser_')
        self._parser_1 = FrameworkParser('JOB1', '0', self._output_path_1)

        self._output_path_2 = tempfile.mkdtemp(prefix='test_framework_parser_')
        self._parser_2 = FrameworkParser('JOB2', '0', self._output_path_2)

    def teardown_method(self) -> None:
        """Clear up after test case execution."""
        shutil.rmtree(self._output_path_1)
        shutil.rmtree(self._output_path_2)
        FrameworkParser._raw_data_dir = '/var/log/npu/profiling'

    def test_save_path(self):
        """Test the querying save path function."""
        expect_result = os.path.join(self._output_path_1, 'framework_raw_0.csv')
        assert expect_result == self._parser_1.save_path

        expect_result = os.path.join(self._output_path_2, 'framework_raw_0.csv')
        assert expect_result == self._parser_2.save_path

    def test_to_task_id_full_op_name_dict(self):
        """Test the querying task id and full operator name dict function."""
        expect_result = {
            '51517': 'Default/Cast-op6',
            '51518': 'Default/TransData-op7',
            '51519': 'Default/network-WithLossCell/_backbone-ResNet/conv1-Conv2d/Cast-op5',
            '51522': 'Default/network-WithLossCell/_backbone-ResNet/'
                     'layer1-SequentialCell/0-ResidualBlock/conv1-Conv2d/Cast-op28'
        }
        assert expect_result == self._parser_1.to_task_id_full_op_name_dict()
        assert expect_result == self._parser_2.to_task_id_full_op_name_dict()

    def test_parse(self):
        """Test the parse function."""
        expect_framework_file = os.path.join(PROFILER_DIR, 'framework_raw_0.csv')
        expect_framework_file = os.path.realpath(expect_framework_file)
        expect_result = get_framework_result(expect_framework_file)

        self._parser_1.parse()
        framework_file = os.path.join(self._output_path_1, 'framework_raw_0.csv')
        result = get_framework_result(framework_file)
        assert expect_result == result

        self._parser_2.parse()
        framework_file = os.path.join(self._output_path_2, 'framework_raw_0.csv')
        result = get_framework_result(framework_file)
        assert expect_result == result

    @mock.patch('mindinsight.profiler.parser.framework_parser.validate_and_normalize_path')
    def test_create_framework_parser_fail_1(self, *args):
        """Test the function of fail to create framework parser."""
        args[0].side_effect = ValidationError({'profiler': {"The path is invalid!"}})

        with pytest.raises(ProfilerPathErrorException) as exc_info:
            FrameworkParser('JOB1', '0')
        assert exc_info.value.error_code == '50546081'
        assert exc_info.value.message == 'Path error. Profiling path is invalid.'

    @mock.patch('os.path.isdir')
    def test_create_framework_parser_fail_2(self, *args):
        """Test the function of fail to create framework parser."""
        args[0].return_value = False
        FrameworkParser._raw_data_dir = '/var/log/npu/profiling'

        with pytest.raises(ProfilerDirNotFoundException) as exc_info:
            FrameworkParser('JOB1', '0')
        assert exc_info.value.error_code == '50546083'
        assert exc_info.value.message == \
               'The dir </var/log/npu/profiling/JOB1> not found.'

    @mock.patch('os.listdir')
    @mock.patch('os.path.isdir')
    def test_create_framework_parser_fail_3(self, *args):
        """Test the function of fail to create framework parser."""
        args[0].return_value = True
        args[1].return_value = []
        FrameworkParser._raw_data_dir = '/var/log/npu/profiling'

        with pytest.raises(ProfilerFileNotFoundException) as exc_info:
            FrameworkParser('JOB1', '0')
        assert exc_info.value.error_code == '50546084'
        assert exc_info.value.message == 'The file <Framework> not found.'
