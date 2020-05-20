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


MOCK_SUMMARY_DIRS = [
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
MOCK_SUMMARIES = [
    {
        'file_name': 'file0.summary.1',
        'create_time': datetime.fromtimestamp(1582031970)
    },
    {
        'file_name': 'file0.summary.1_lineage',
        'create_time': datetime.fromtimestamp(1582031970)
    },
    {
        'file_name': 'file1.summary.2',
        'create_time': datetime.fromtimestamp(1582031971)
    },
    {
        'file_name': 'file1.summary.2_lineage',
        'create_time': datetime.fromtimestamp(1582031971)
    }
]


class TestSummaryPathParser(TestCase):
    """Test the class of SummaryPathParser."""

    @mock.patch.object(SummaryWatcher, 'list_summaries')
    def test_get_lineage_summaries(self, *args):
        """Test the function of get_lineage_summaries."""
        args[0].return_value = MOCK_SUMMARIES
        exp_result = ['file0.summary.1_lineage', 'file1.summary.2_lineage']
        summary_dir = '/path/to/summary_dir'
        result = SummaryPathParser.get_lineage_summaries(summary_dir)
        self.assertEqual(exp_result, result)

        args[0].return_value = [
            {
                'file_name': 'file0.summary.1',
                'create_time': datetime.fromtimestamp(1582031970)
            }
        ]
        result = SummaryPathParser.get_lineage_summaries(summary_dir)
        self.assertEqual([], result)

        args[0].return_value = [
            {
                'file_name': 'file0.summary.1_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            }
        ]
        result = SummaryPathParser.get_lineage_summaries(summary_dir)
        self.assertEqual(['file0.summary.1_lineage'], result)

        args[0].return_value = [
            {
                'file_name': 'file0.summary.3_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file0.summary.2_lineage_lineage',
                'create_time': datetime.fromtimestamp(1582031970)
            },
            {
                'file_name': 'file1.summary.1_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            },
            {
                'file_name': 'file1.summary.7_lineage_lineage',
                'create_time': datetime.fromtimestamp(1582031971)
            }
        ]
        exp_result = ['file1.summary.1_lineage',
                      'file0.summary.2_lineage_lineage',
                      'file0.summary.3_lineage',
                      'file1.summary.7_lineage_lineage']
        result = SummaryPathParser.get_lineage_summaries(summary_dir, is_sorted=True)
        self.assertEqual(exp_result, result)
