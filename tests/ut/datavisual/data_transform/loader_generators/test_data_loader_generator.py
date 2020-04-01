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
"""
Function:
    Test mindinsight.datavisual.data_transform.loader_generators.data_loader_generator
Usage:
    pytest tests/ut/datavisual
"""
import datetime
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from mindinsight.datavisual.data_transform.loader_generators import data_loader_generator
from mindinsight.utils.exceptions import ParamValueError

from ...mock import MockLogger


class TestDataLoaderGenerator:
    """Test data_loader_generator."""

    @classmethod
    def setup_class(cls):
        data_loader_generator.logger = MockLogger

    def _generate_summaries(self, summary_base_dir, dir_num=1):
        """Utils function for tests."""
        summaries = list()

        if os.path.exists(summary_base_dir):
            shutil.rmtree(summary_base_dir)
        os.mkdir(summary_base_dir)
        for i in range(dir_num):
            log_dir = os.path.join(summary_base_dir, f'job{i}')
            os.mkdir(log_dir)
            summary_info = dict(relative_path=log_dir.replace(summary_base_dir, "."),
                                update_time=datetime.datetime.now().replace(minute=i).astimezone())
            summaries.append(summary_info)
        return summaries

    def test_invalid_summary_path(self):
        """Test invalid summary path."""
        path = None
        with pytest.raises(ParamValueError) as exc_info:
            data_loader_generator.DataLoaderGenerator(path)

        assert "Summary path is None." in exc_info.value.message
        assert MockLogger.log_msg['warning'] == "Summary path is None. It will not init data loader generator."

    def test_generate_loaders_with_not_exist_path(self):
        """Test generating loaders with not exist path."""
        path = tempfile.NamedTemporaryFile().name
        os.mkdir(path)
        generator = data_loader_generator.DataLoaderGenerator(path)
        os.removedirs(path)
        loader_dict = generator.generate_loaders(loader_pool=dict())
        assert MockLogger.log_msg['warning'] == "Summary path does not exist. It will not start " \
                                                "loading events data. Current path is %r." % path
        assert loader_dict == {}

    @patch.object(data_loader_generator.DataLoader, "has_valid_files")
    @patch.object(data_loader_generator.SummaryWatcher, "list_summary_directories")
    def test_generate_loaders(self, mock_summary_watcher, mock_data_loader):
        """Test generating loaders."""
        summary_base_dir = tempfile.NamedTemporaryFile().name
        summaries = self._generate_summaries(summary_base_dir, 20)

        # mock summary_watcher.
        generator = data_loader_generator.DataLoaderGenerator(summary_base_dir)
        mock_summary_watcher.return_value = summaries

        # mock DataLoader
        mock_data_loader.return_value = True

        loader_dict = generator.generate_loaders(loader_pool=dict())
        expected_ids = [
            summary.get('relative_path') for summary in summaries[-data_loader_generator.MAX_DATA_LOADER_SIZE:]
        ]
        assert sorted(loader_dict.keys()) == sorted(expected_ids)

        shutil.rmtree(summary_base_dir)

    def test_check_job_exist(self):
        """Test checking if job exists."""
        summary_base_dir = tempfile.NamedTemporaryFile().name
        self._generate_summaries(summary_base_dir)
        with open(os.path.join(summary_base_dir, 'job0', "summary.1"), 'w'):
            pass

        generator = data_loader_generator.DataLoaderGenerator(summary_base_dir)

        assert generator.check_train_job_exist(train_id='./job0')
        assert not generator.check_train_job_exist(train_id='job0')
        assert not generator.check_train_job_exist(train_id='././../job0')

        shutil.rmtree(summary_base_dir)

    def test_generate_loader_by_train_id(self):
        """Test generating loader by train id."""
        summary_base_dir = tempfile.NamedTemporaryFile().name
        self._generate_summaries(summary_base_dir)
        with open(os.path.join(summary_base_dir, 'job0', "summary.1"), 'w'):
            pass
        generator = data_loader_generator.DataLoaderGenerator(summary_base_dir)

        train_id = "./job0"
        loader = generator.generate_loader_by_train_id(train_id)
        assert loader.loader_id == train_id

        shutil.rmtree(summary_base_dir)
