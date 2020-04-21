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

from ..mock import MockLogger

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
        assert MockLogger.log_msg['warning'] == "There are some files has been deleted, " \
                                                "we will reload all files in path {}.".format(summary_dir)
        shutil.rmtree(summary_dir)

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
        assert 'Check crc faild and ignore this file' in str(MockLogger.log_msg['warning'])
        shutil.rmtree(summary_dir)

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
        assert sorted(res) == expected

        shutil.rmtree(summary_dir)


def write_file(filename, record):
    """Write bytes strings to file."""
    with open(filename, 'wb') as file:
        file.write(record)
