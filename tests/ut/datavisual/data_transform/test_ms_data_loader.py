# Copyright 2019 Huawei Technologies Co., Ltd
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
"""
Function:
    Test mindinsight.datavisual.data_transform.ms_data_loader.
Usage:
    pytest tests/ut/datavisual
"""
import os
import shutil
import tempfile
from unittest.mock import Mock

import pytest

from mindinsight.datavisual.data_transform import ms_data_loader
from mindinsight.datavisual.data_transform.ms_data_loader import MSDataLoader
from mindinsight.datavisual.data_transform.ms_data_loader import _PbParser
from mindinsight.datavisual.data_transform.events_data import TensorEvent
from mindinsight.datavisual.common.enums import PluginNameEnum

from ..mock import MockLogger
from ....utils.log_generators.graph_pb_generator import create_graph_pb_file

# bytes of 3 scalar events
SCALAR_RECORD = (b'\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\x96\xe1\xeb)>}\xd7A\x10\x01*'
                 b'\x11\n\x0f\n\x08tag_name\x1d\r\x06V>\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00'
                 b'\x00\x00\x00\x00\x00\t\x96\xe1\xeb)>}\xd7A\x10\x03*\x11\n\x0f\n\x08tag_name\x1d'
                 b'\xac`\x85>\x00\x00\x00\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\t\x96'
                 b'\xe1\xeb)>}\xd7A\x10\x05*\x11\n\x0f\n\x08tag_name\x1d\xf80y?\x00\x00\x00\x00')
RECORD_LEN = len(SCALAR_RECORD)


class TestMsDataLoader:
    """Test ms_data_loader."""

    @classmethod
    def setup_method(cls):
        """
        Set up for testing.
        Generate a temp directory to store log files and mock the EventsData.EventsData.
        """
        mock_exception = Mock(return_value=True)
        MockLogger.exception = mock_exception
        ms_data_loader.logger = MockLogger

    @pytest.fixture(scope="function")
    def crc_pass(self):
        """Mock the crc to pass the check."""
        ms_data_loader.crc32.CheckValueAgainstData = Mock(return_value=True)

    @pytest.fixture(scope="function")
    def crc_fail(self):
        """Mock the crc to fail the check."""
        ms_data_loader.crc32.CheckValueAgainstData = Mock(return_value=False)

    def test_check_files_update_success_deleted_files(self):
        """Test new file list delete some files."""
        old_file_list = ['summary.01', 'summary.02']
        new_file_list = ['summary02']
        summary_dir = tempfile.mkdtemp()
        ms_loader = MSDataLoader(summary_dir)
        ms_loader._check_files_deleted(new_file_list, old_file_list)
        shutil.rmtree(summary_dir)
        assert MockLogger.log_msg['warning'] == "There are some files has been deleted, " \
                                                "we will reload all files in path {}.".format(summary_dir)

    @pytest.mark.usefixtures('crc_pass')
    def test_load_success_with_crc_pass(self):
        """Test load success."""
        summary_dir = tempfile.mkdtemp()
        file1 = os.path.join(summary_dir, 'summary.01')
        write_file(file1, SCALAR_RECORD)
        ms_loader = MSDataLoader(summary_dir)
        ms_loader._latest_summary_filename = 'summary.00'
        ms_loader.load()
        shutil.rmtree(summary_dir)
        assert ms_loader._latest_summary_file_size == RECORD_LEN
        tag = ms_loader.get_events_data().list_tags_by_plugin('scalar')
        tensors = ms_loader.get_events_data().tensors(tag[0])
        assert len(tensors) == 3

    @pytest.mark.usefixtures('crc_fail')
    def test_load_with_crc_fail(self):
        """Test when crc_fail and will not go to func _event_parse."""
        summary_dir = tempfile.mkdtemp()
        file2 = os.path.join(summary_dir, 'summary.02')
        write_file(file2, SCALAR_RECORD)
        ms_loader = MSDataLoader(summary_dir)
        ms_loader.load()
        shutil.rmtree(summary_dir)
        assert 'Check crc faild and ignore this file' in str(MockLogger.log_msg['warning'])

    def test_filter_event_files(self):
        """Test filter_event_files function ok."""
        file_list = [
            'abc.summary', '123sumary0009abc', 'summary1234', 'aaasummary.5678', 'summary.0012', 'hellosummary.98786',
            'mysummary.123abce', 'summay.4567'
        ]
        summary_dir = tempfile.mkdtemp()
        for file in file_list:
            with open(os.path.join(summary_dir, file), 'w'):
                pass
        ms_loader = MSDataLoader(summary_dir)
        res = ms_loader.filter_valid_files()
        expected = sorted(['aaasummary.5678', 'summary.0012', 'hellosummary.98786', 'mysummary.123abce'])
        shutil.rmtree(summary_dir)
        assert sorted(res) == expected

    def test_load_single_pb_file(self):
        """Test load pb file success."""
        filename = 'ms_output.pb'
        summary_dir = tempfile.mkdtemp()
        create_graph_pb_file(output_dir=summary_dir, filename=filename)
        ms_loader = MSDataLoader(summary_dir)
        ms_loader.load()
        events_data = ms_loader.get_events_data()
        plugins = events_data.list_tags_by_plugin(PluginNameEnum.GRAPH.value)
        shutil.rmtree(summary_dir)
        assert len(plugins) == 1
        assert plugins[0] == filename


class TestPbParser:
    """Test pb parser"""
    _summary_dir = ''

    def setup_method(self):
        self._summary_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self._summary_dir)

    def test_parse_pb_file(self):
        """Test parse pb file success."""
        filename = 'ms_output.pb'
        create_graph_pb_file(output_dir=self._summary_dir, filename=filename)
        parser = _PbParser(self._summary_dir)
        tensor_event = parser.parse_pb_file(filename)
        assert isinstance(tensor_event, TensorEvent)

    def test_is_parse_pb_file(self):
        """Test parse an older file."""
        filename = 'ms_output.pb'
        create_graph_pb_file(output_dir=self._summary_dir, filename=filename)
        parser = _PbParser(self._summary_dir)
        result = parser._is_parse_pb_file(filename)
        assert result

        filename = 'ms_output_older.pb'
        file_path = create_graph_pb_file(output_dir=self._summary_dir, filename=filename)
        atime = 1
        mtime = 1
        os.utime(file_path, (atime, mtime))
        result = parser._is_parse_pb_file(filename)
        assert not result

    def test_sort_pb_file_by_mtime(self):
        """Test sort pb files."""
        filenames = ['abc.pb', 'bbc.pb']
        for file in filenames:
            create_graph_pb_file(output_dir=self._summary_dir, filename=file)
        parser = _PbParser(self._summary_dir)

        sorted_filenames = parser.sort_pb_files(filenames)
        assert filenames == sorted_filenames

    def test_sort_pb_file_by_filename(self):
        """Test sort pb file by file name."""
        filenames = ['aaa.pb', 'bbb.pb', 'ccc.pb']
        for file in filenames:
            create_graph_pb_file(output_dir=self._summary_dir, filename=file)

        atime, mtime = (3, 3)
        os.utime(os.path.realpath(os.path.join(self._summary_dir, 'aaa.pb')), (atime, mtime))
        atime, mtime = (1, 1)
        os.utime(os.path.realpath(os.path.join(self._summary_dir, 'bbb.pb')), (atime, mtime))
        os.utime(os.path.realpath(os.path.join(self._summary_dir, 'ccc.pb')), (atime, mtime))

        expected_filenames = ['bbb.pb', 'ccc.pb', 'aaa.pb']
        parser = _PbParser(self._summary_dir)
        sorted_filenames = parser.sort_pb_files(filenames)
        assert expected_filenames == sorted_filenames


def write_file(filename, record):
    """Write bytes strings to file."""
    with open(filename, 'wb') as file:
        file.write(record)
