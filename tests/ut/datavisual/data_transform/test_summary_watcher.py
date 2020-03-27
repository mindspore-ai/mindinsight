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
    Test mindinsight.datavisual.data_transform.summary_watcher.
Usage:
    pytest tests/ut/datavisual
"""
import datetime
import math
import os
import random
import shutil
import tempfile

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher


def gen_directories_and_files(summary_base_dir, file_count, directory_count):
    """Generate directories and files for test."""
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=10)

    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    for _ in range(file_count):
        summary = os.path.join(summary_base_dir, f'prefix.summary.{random.randint(start_ts, end_ts)}.suffix')
        with open(summary, 'w'):
            pass

    os.mkdir(os.path.join(summary_base_dir, 'run'))
    for _ in range(file_count):
        summary = os.path.join(summary_base_dir,
                               'run',
                               f'prefix.summary.{random.randint(start_ts, end_ts)}.suffix')
        with open(summary, 'w'):
            pass

    for index in range(directory_count-1):
        shutil.copytree(os.path.join(summary_base_dir, 'run'), os.path.join(summary_base_dir, f'run{index}'))


class TestSummaryWatcher:
    """Test summary watcher."""

    def test_list_summary_directories_with_overall_on(self):
        """Test list_summary_directories method success."""
        summary_base_dir = tempfile.mkdtemp()
        file_count = 10
        directory_count = 10
        gen_directories_and_files(summary_base_dir, file_count, directory_count)

        summary_watcher = SummaryWatcher()
        directories = summary_watcher.list_summary_directories(summary_base_dir, overall=True)
        expected_directory_count = directory_count + 1
        assert len(directories) == min(expected_directory_count, SummaryWatcher.MAX_SUMMARY_DIR_COUNT)
        shutil.rmtree(summary_base_dir)

    def test_list_summary_directories_by_pagination(self):
        """Test list_summary_directories method success."""
        summary_base_dir = tempfile.mkdtemp()
        file_count = 10
        directory_count = 10
        gen_directories_and_files(summary_base_dir, file_count, directory_count)

        summary_watcher = SummaryWatcher()
        total, directories = summary_watcher.list_summary_directories_by_pagination(
            summary_base_dir, offset=0, limit=10)

        if (file_count + 1) * directory_count + file_count >= SummaryWatcher.MAX_SCAN_COUNT:
            expected_directory_count = math.ceil((SummaryWatcher.MAX_SCAN_COUNT - file_count) / (file_count + 1) + 1)
            assert total == len(directories) == expected_directory_count
        else:
            expected_directory_count = directory_count + 1
            assert total == min(expected_directory_count, SummaryWatcher.MAX_SUMMARY_DIR_COUNT)

        shutil.rmtree(summary_base_dir)

    def test_is_summary_directory(self):
        """Test is_summary_directory method success."""
        summary_base_dir = tempfile.mkdtemp()
        file_count = 1
        directory_count = 1
        gen_directories_and_files(summary_base_dir, file_count, directory_count)

        summary_watcher = SummaryWatcher()
        flag = summary_watcher.is_summary_directory(summary_base_dir, './')
        assert flag
        flag = summary_watcher.is_summary_directory(summary_base_dir, './\x00')
        assert not flag
        shutil.rmtree(summary_base_dir)

    def test_list_summaries(self):
        """Test list_summaries method success."""
        summary_base_dir = tempfile.mkdtemp()
        file_count = 10
        directory_count = 1
        gen_directories_and_files(summary_base_dir, file_count, directory_count)

        summary_watcher = SummaryWatcher()
        summaries = summary_watcher.list_summaries(summary_base_dir)
        assert len(summaries) == file_count
        summaries = summary_watcher.list_summaries(summary_base_dir, './\x00')
        assert not summaries
        shutil.rmtree(summary_base_dir)
