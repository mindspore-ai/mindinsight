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

from mindinsight.lineagemgr.model import filter_summary_lineage, get_flattened_lineage
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageSummaryParseException, \
    LineageQuerierParamException, LineageQuerySummaryDataError, LineageSearchConditionParamError, LineageParamTypeError
from mindinsight.lineagemgr.common.path_parser import SummaryPathParser
from ...st.func.lineagemgr.test_model import LINEAGE_FILTRATION_RUN1, LINEAGE_FILTRATION_RUN2


class TestFilterAPI(TestCase):
    """Test the function of filter_summary_lineage."""
    _MOCK_DATA_MANAGER = MagicMock()

    @mock.patch('mindinsight.lineagemgr.model.Querier')
    @mock.patch('mindinsight.lineagemgr.lineage_parser.SummaryPathParser.get_lineage_summaries')
    def test_filter_summary_lineage(self, latest_summary_mock, qurier_mock):
        """Test the function of filter_summary_lineage."""
        latest_summary_mock.return_value = ['/path/to/summary_base_dir/summary_dir']
        mock_querier = MagicMock()
        qurier_mock.return_value = mock_querier
        mock_querier.filter_summary_lineage.return_value = [{'loss': 3.0}]

        result = filter_summary_lineage(self._MOCK_DATA_MANAGER)
        self.assertEqual(result, [{'loss': 3.0}])

    @mock.patch('mindinsight.lineagemgr.model.validate_condition')
    def test_invalid_search_condition(self, mock_valid):
        """Test filter_summary_lineage with invalid invalid param."""
        mock_valid.side_effect = LineageParamTypeError(
            'Invalid search_condition type.')
        self.assertRaisesRegex(
            LineageSearchConditionParamError,
            'Invalid search_condition type.',
            filter_summary_lineage,
            self._MOCK_DATA_MANAGER,
            'invalid_condition'
        )

    def test_failed_to_get_summary_files(self):
        """Test filter_summary_lineage with invalid invalid param."""
        default_result = {
            'customized': {},
            'object': [],
            'count': 0
        }
        assert default_result == filter_summary_lineage(self._MOCK_DATA_MANAGER)

    @mock.patch('mindinsight.lineagemgr.model.validate_search_model_condition')
    @mock.patch('mindinsight.lineagemgr.model.validate_condition')
    @mock.patch.object(SummaryPathParser, 'get_lineage_summaries')
    @mock.patch('mindinsight.lineagemgr.model.Querier')
    def test_failed_to_querier(self, mock_query, *args):
        """Test filter_summary_lineage with invalid invalid param."""
        mock_query.side_effect = LineageSummaryParseException()
        args[0].return_value = None
        res = filter_summary_lineage(self._MOCK_DATA_MANAGER)
        assert res == {'object': [], 'count': 0}

        mock_query.side_effect = LineageQuerierParamException(['keys'], 'key')
        self.assertRaisesRegex(
            LineageQuerySummaryDataError,
            'Filter summary lineage failed.',
            filter_summary_lineage,
            self._MOCK_DATA_MANAGER
        )

    @mock.patch('mindinsight.lineagemgr.model.filter_summary_lineage')
    def test_get_lineage_table(self, mock_filter_summary_lineage):
        """Test get_flattened_lineage with valid param."""
        mock_data = {
            'object': [LINEAGE_FILTRATION_RUN1, LINEAGE_FILTRATION_RUN2]
        }
        mock_data_manager = MagicMock()
        mock_filter_summary_lineage.return_value = mock_data
        result = get_flattened_lineage(mock_data_manager)
        assert result.get('[U]info') == ['info1', None]
