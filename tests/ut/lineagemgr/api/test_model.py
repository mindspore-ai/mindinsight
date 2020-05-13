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
"""Test the model module."""
from unittest import TestCase, mock
from unittest.mock import MagicMock

from mindinsight.lineagemgr import get_summary_lineage, filter_summary_lineage
from mindinsight.lineagemgr.api.model import _convert_relative_path_to_abspath
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamSummaryPathError, \
    LineageFileNotFoundError, LineageSummaryParseException, LineageQuerierParamException, \
    LineageQuerySummaryDataError, LineageSearchConditionParamError, LineageParamTypeError, \
    LineageParamValueError
from mindinsight.lineagemgr.common.path_parser import SummaryPathParser


class TestModel(TestCase):
    """Test the function of get_summary_lineage and filter_summary_lineage."""

    @mock.patch('mindinsight.lineagemgr.api.model.Querier')
    @mock.patch('mindinsight.lineagemgr.api.model.LineageParser')
    @mock.patch('os.path.isdir')
    def test_get_summary_lineage_success(self, isdir_mock, parser_mock, qurier_mock):
        """Test the function of get_summary_lineage."""
        isdir_mock.return_value = True
        parser_mock.return_value = MagicMock()

        mock_querier = MagicMock()
        qurier_mock.return_value = mock_querier
        mock_querier.get_summary_lineage.return_value = [{'algorithm': {'network': 'ResNet'}}]
        summary_dir = '/path/to/summary_dir'
        result = get_summary_lineage(summary_dir, keys=['algorithm'])
        self.assertEqual(result, {'algorithm': {'network': 'ResNet'}})

    def test_get_summary_lineage_failed(self):
        """Test get_summary_lineage failed."""
        invalid_path = '../fake_dir'
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            get_summary_lineage,
            invalid_path
        )

    @mock.patch('mindinsight.lineagemgr.common.utils.validate_path')
    @mock.patch.object(SummaryPathParser, 'get_latest_lineage_summary')
    def test_get_summary_lineage_failed2(self, mock_summary, mock_valid):
        """Test get_summary_lineage failed."""
        mock_summary.return_value = None
        mock_valid.return_value = '/path/to/summary/dir'
        self.assertRaisesRegex(
            LineageFileNotFoundError,
            'no summary log file under summary_dir',
            get_summary_lineage,
            '/path/to/summary_dir'
        )

    @mock.patch('mindinsight.lineagemgr.lineage_parser.LineageParser._parse_summary_log')
    @mock.patch('mindinsight.lineagemgr.common.utils.validate_path')
    @mock.patch.object(SummaryPathParser, 'get_latest_lineage_summary')
    def test_get_summary_lineage_failed3(self,
                                         mock_summary,
                                         mock_valid,
                                         mock_paser):
        """Test get_summary_lineage failed."""
        mock_summary.return_value = '/path/to/summary/file'
        mock_valid.return_value = '/path/to/summary_dir'
        mock_paser.return_value = None
        result = get_summary_lineage('/path/to/summary_dir')
        assert {} == result

    @mock.patch('mindinsight.lineagemgr.api.model.validate_path')
    def test_convert_relative_path_to_abspath(self, validate_path_mock):
        """Test the function of converting realtive path to abspath."""
        validate_path_mock.return_value = '/path/to/summary_base_dir/summary_dir'
        summary_base_dir = '/path/to/summary_base_dir'
        search_condition = {
            'summary_dir': {
                'in': ['/path/to/summary_base_dir']
            }
        }
        result = _convert_relative_path_to_abspath(summary_base_dir,
                                                   search_condition)
        self.assertDictEqual(
            result, {'summary_dir': {'in': ['/path/to/summary_base_dir/summary_dir']}})

        search_condition = {
            'summary_dir': {
                'in': ['./summary_dir']
            }
        }
        result = _convert_relative_path_to_abspath(summary_base_dir, search_condition)
        self.assertDictEqual(
            result, {'summary_dir': {'in': ['/path/to/summary_base_dir/summary_dir']}}
        )

        search_condition = {
            'summary_dir': {
                'eq': '/summary_dir'
            }
        }
        result = _convert_relative_path_to_abspath(summary_base_dir, search_condition)
        self.assertDictEqual(
            result, {'summary_dir': {'eq': '/path/to/summary_base_dir/summary_dir'}})

        search_condition = {
            'summary_dir': None
        }
        result = _convert_relative_path_to_abspath(summary_base_dir, search_condition)
        self.assertDictEqual(
            result, search_condition
        )


class TestFilterAPI(TestCase):
    """Test the function of filter_summary_lineage."""
    @mock.patch('mindinsight.lineagemgr.api.model.LineageOrganizer')
    @mock.patch('mindinsight.lineagemgr.api.model.Querier')
    @mock.patch('mindinsight.lineagemgr.lineage_parser.SummaryPathParser.get_latest_lineage_summary')
    @mock.patch('mindinsight.lineagemgr.api.model._convert_relative_path_to_abspath')
    @mock.patch('mindinsight.lineagemgr.api.model.normalize_summary_dir')
    def test_filter_summary_lineage(self, validate_path_mock, convert_path_mock,
                                    latest_summary_mock, qurier_mock, organizer_mock):
        """Test the function of filter_summary_lineage."""
        convert_path_mock.return_value = {
            'summary_dir': {
                'in': ['/path/to/summary_base_dir']
            },
            'loss': {
                'gt': 2.0
            }
        }
        organizer_mock = MagicMock()
        organizer_mock.super_lineage_objs = None
        validate_path_mock.return_value = True
        latest_summary_mock.return_value = ['/path/to/summary_base_dir/summary_dir']
        mock_querier = MagicMock()
        qurier_mock.return_value = mock_querier
        mock_querier.filter_summary_lineage.return_value = [{'loss': 3.0}]

        summary_base_dir = '/path/to/summary_base_dir'
        result = filter_summary_lineage(summary_base_dir)
        self.assertEqual(result, [{'loss': 3.0}])

    def test_invalid_path(self):
        """Test filter_summary_lineage with invalid path."""
        invalid_path = '../fake_dir'
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'The summary path is invalid.',
            filter_summary_lineage,
            invalid_path
        )

    @mock.patch('mindinsight.lineagemgr.api.model.validate_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.normalize_summary_dir')
    def test_invalid_search_condition(self, mock_path, mock_valid):
        """Test filter_summary_lineage with invalid invalid param."""
        mock_path.return_value = None
        mock_valid.side_effect = LineageParamTypeError(
            'Invalid search_condition type.')
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'Invalid search_condition type.',
            filter_summary_lineage,
            '/path/to/summary/dir',
            'invalid_condition'
        )

    @mock.patch('mindinsight.lineagemgr.api.model.validate_search_model_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.validate_condition')
    @mock.patch('mindinsight.lineagemgr.common.utils.validate_path')
    @mock.patch('mindinsight.lineagemgr.api.model._convert_relative_path_to_abspath')
    def test_failed_to_convert_path(self, mock_convert, *args):
        """Test filter_summary_lineage with invalid invalid param."""
        mock_convert.side_effect = LineageParamValueError('invalid path')
        args[0].return_value = None
        self.assertRaisesRegex(
            LineageParamSummaryPathError,
            'invalid path',
            filter_summary_lineage,
            '/path/to/summary/dir',
            {}
        )

    @mock.patch('mindinsight.lineagemgr.api.model._convert_relative_path_to_abspath')
    @mock.patch('mindinsight.lineagemgr.api.model.validate_search_model_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.validate_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.normalize_summary_dir')
    @mock.patch.object(SummaryPathParser, 'get_latest_lineage_summary')
    def test_failed_to_get_summary_filesh(self, mock_parse, *args):
        """Test filter_summary_lineage with invalid invalid param."""
        path = '/path/to/summary/dir'
        mock_parse.return_value = None
        args[0].return_value = path
        self.assertRaisesRegex(
            LineageFileNotFoundError,
            'There is no summary log file under summary_base_dir.',
            filter_summary_lineage,
            path
        )

    @mock.patch('mindinsight.lineagemgr.api.model._convert_relative_path_to_abspath')
    @mock.patch('mindinsight.lineagemgr.api.model.validate_search_model_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.validate_condition')
    @mock.patch('mindinsight.lineagemgr.api.model.normalize_summary_dir')
    @mock.patch.object(SummaryPathParser, 'get_latest_lineage_summaries')
    @mock.patch('mindinsight.lineagemgr.api.model.Querier')
    def test_failed_to_querier(self, mock_query, mock_parse, *args):
        """Test filter_summary_lineage with invalid invalid param."""
        mock_query.side_effect = LineageSummaryParseException()
        mock_parse.return_value = ['/path/to/summary/file']
        args[0].return_value = None
        res = filter_summary_lineage('/path/to/summary')
        assert res == {'object': [], 'count': 0}

        mock_query.side_effect = LineageQuerierParamException(['keys'], 'key')
        self.assertRaisesRegex(
            LineageQuerySummaryDataError,
            'Filter summary lineage failed.',
            filter_summary_lineage,
            '/path/to/summary/dir'
        )
