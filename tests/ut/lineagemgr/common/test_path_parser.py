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
"""Test the path_parser module."""
from datetime import datetime
from unittest import TestCase, mock

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.lineagemgr.common.path_parser import SummaryPathParser


class TestSummaryPathParser(TestCase):
    """Test the class of SummaryPathParser."""

    @mock.patch.object(SummaryWatcher, 'list_summary_directories')
    def test_get_summary_dirs(self, *args):
        """Test the function of get_summary_dirs."""
        args[0].return_value = [
            {
                'relative_path': './relative_path0'
            },
            {
                'relative_path': './'
            },
            {
                'relative_path': './relative_path1'
            }
        ]

        expected_result = [
            '/path/to/base/relative_path0',
            '/path/to/base',
            '/path/to/base/relative_path1'
        ]
        base_dir = '/path/to/base'
        result = SummaryPathParser.get_summary_dirs(base_dir)
        self.assertListEqual(expected_result, result)

        args[0].return_value = []
        result = SummaryPathParser.get_summary_dirs(base_dir)
        self.assertListEqual([], result)

    @mock.patch.object(SummaryWatcher, 'list_summaries')
    def test_get_latest_lineage_summary(self, *args):
        """Test the function of get_latest_lineage_summary."""
        args[0].return_value = [
            {
                'file_name': 'file0',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file0_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file1',
                'create_time': datetime.fromtimestamp(1582031971)
            },
            {
                'file_name': 'file1_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            }
        ]
        summary_dir = '/path/to/summary_dir'
        result = SummaryPathParser.get_latest_lineage_summary(summary_dir)
        self.assertEqual('/path/to/summary_dir/file1_lineage', result)

        args[0].return_value = [
            {
                'file_name': 'file0',
                'create_time': datetime.fromtimestamp(1582031970)
            }
        ]
        result = SummaryPathParser.get_latest_lineage_summary(summary_dir)
        self.assertEqual(None, result)

        args[0].return_value = [
            {
                'file_name': 'file0_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            }
        ]
        result = SummaryPathParser.get_latest_lineage_summary(summary_dir)
        self.assertEqual(None, result)

        args[0].return_value = [
            {
                'file_name': 'file0_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file0_lineage_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file1_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            },
            {
                'file_name': 'file1_lineage_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            }
        ]
        result = SummaryPathParser.get_latest_lineage_summary(summary_dir)
        self.assertEqual('/path/to/summary_dir/file1_lineage_lineage', result)

    @mock.patch.object(SummaryWatcher, 'list_summaries')
    @mock.patch.object(SummaryWatcher, 'list_summary_directories')
    def test_get_latest_lineage_summaries(self, *args):
        """Test the function of get_latest_lineage_summaries."""
        args[0].return_value = [
            {
                'relative_path': './relative_path0'
            },
            {
                'relative_path': './'
            },
            {
                'relative_path': './relative_path1'
            }
        ]
        args[1].return_value = [
            {
                'file_name': 'file0',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file0_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file1',
                'create_time': datetime.fromtimestamp(1582031971)
            },
            {
                'file_name': 'file1_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            }
        ]

        expected_result = [
            '/path/to/base/relative_path0/file1_lineage',
            '/path/to/base/file1_lineage',
            '/path/to/base/relative_path1/file1_lineage'
        ]
        base_dir = '/path/to/base'
        result = SummaryPathParser.get_latest_lineage_summaries(base_dir)
        self.assertListEqual(expected_result, result)

        args[1].return_value = [
            {
                'file_name': 'file0_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            }
        ]
        result = SummaryPathParser.get_latest_lineage_summaries(base_dir)
        self.assertListEqual([], result)
