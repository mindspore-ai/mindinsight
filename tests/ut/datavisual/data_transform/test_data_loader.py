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
    Test mindinsight.datavisual.data_transform.data_loader.
Usage:
    pytest tests/ut/datavisual
"""
import os
import shutil
import tempfile

import pytest

from mindinsight.datavisual.common.exceptions import SummaryLogPathInvalid
from mindinsight.datavisual.data_transform import data_loader
from mindinsight.datavisual.data_transform.data_loader import DataLoader

from ..mock import MockLogger


class TestDataLoader:
    """Test data_loader."""

    @classmethod
    def setup_class(cls):
        data_loader.logger = MockLogger

    def setup_method(self):
        self._summary_dir = tempfile.mkdtemp()
        if os.path.exists(self._summary_dir):
            shutil.rmtree(self._summary_dir)
        os.mkdir(self._summary_dir)

    def teardown_method(self):
        if os.path.exists(self._summary_dir):
            shutil.rmtree(self._summary_dir)

    def _generate_files(self, dir_path, file_list):
        for file_name in file_list:
            with open(os.path.join(dir_path, file_name), 'w'):
                pass

    def test_load_with_not_file_list(self):
        """Test loading method with empty file list."""
        loader = DataLoader(self._summary_dir)
        with pytest.raises(SummaryLogPathInvalid):
            loader.load()
        assert 'No valid files can be loaded' in str(MockLogger.log_msg['warning'])

    def test_load_with_invalid_file_list(self):
        """Test loading method with valid path and invalid file_list."""
        file_list = ['summary.abc01', 'summary.abc02']
        self._generate_files(self._summary_dir, file_list)
        loader = DataLoader(self._summary_dir)
        with pytest.raises(SummaryLogPathInvalid):
            loader.load()
        assert 'No valid files can be loaded' in str(MockLogger.log_msg['warning'])

    def test_load_success(self):
        """Test loading method with valid path and file_list."""
        dir_path = tempfile.NamedTemporaryFile().name
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        file_list = ['summary.001', 'summary.002']
        self._generate_files(dir_path, file_list)
        dataloader = DataLoader(dir_path)
        dataloader.load()
        assert dataloader._loader is not None
        shutil.rmtree(dir_path)
