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
"""Test LineageSummaryAnalyzer.py."""
from unittest import mock, TestCase
from unittest.mock import MagicMock

from mindinsight.datavisual.proto_files.mindinsight_lineage_pb2 import LineageEvent
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageVerificationException, \
    LineageSummaryAnalyzeException
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.summary.lineage_summary_analyzer import LineageSummaryAnalyzer, \
    LineageInfo, SummaryAnalyzer


class TestSummaryAnalyzer(TestCase):
    """Test SummaryAnalyzer class."""

    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.FileHandler")
    def setUp(self, *args):
        args[0].return_value = MagicMock()
        self.analyzer = SummaryAnalyzer("fake_path.log")

    @mock.patch.object(SummaryAnalyzer, '_has_next')
    @mock.patch.object(SummaryAnalyzer, '_read_event')
    def test_load_events(self, *args):
        """Test load_events method."""
        args[1].side_effect = [True, False]
        args[0].return_value = "event"
        res = self.analyzer.load_events()
        self.assertEqual(list(res), ["event"])

    def test_has_next_true(self):
        """Test has_next method when return value is True."""
        self.analyzer.file_handler.tell.return_value = 0
        self.analyzer.file_handler.size = 10
        res = self.analyzer._has_next()
        self.assertEqual(res, True)

    def test_has_next_false(self):
        """Test has_next method when return value is False."""
        self.analyzer.file_handler.tell.return_value = 10
        self.analyzer.file_handler.size = 10
        res = self.analyzer._has_next()
        self.assertEqual(res, False)

    @mock.patch.object(SummaryAnalyzer, '_read_header')
    @mock.patch.object(SummaryAnalyzer, '_read_body')
    @mock.patch.object(LineageEvent, 'FromString')
    def test_read_event(self, *args):
        """Test read_event method."""
        args[2].return_value = 10
        args[1].return_value = "a" * 10
        args[0].return_value = "event"
        res = self.analyzer._read_event()
        self.assertEqual(res, "event")

    @mock.patch.object(SummaryAnalyzer, '_check_crc')
    def test_read_header(self, *args):
        """Test read_header method."""
        args[0].return_value = None
        header_str = b'\x01' + b'\x00' * 7
        header_crc_str = b'\x00' * 4
        self.analyzer.file_handler.read.side_effect = [
            header_str, header_crc_str]
        res = self.analyzer._read_header()
        self.assertEqual(res, 1)

    @mock.patch.object(SummaryAnalyzer, '_check_crc')
    def test_read_body(self, *args):
        """Test read_body method."""
        args[0].return_value = None
        body_str = b'\x01' * 5
        body_crc_str = b'\x00' * 4
        self.analyzer.file_handler.read.side_effect = [
            body_str, body_crc_str]
        res = self.analyzer._read_body(5)
        self.assertEqual(res, body_str)

    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.crc32")
    @mock.patch.object(log, "error")
    def test_check_crc(self, *args):
        """Test _check_crc method."""
        args[0].return_value = None
        args[1].CheckValueAgainstData.return_value = False
        source_str = b'\x01' * 10
        crc_str = b'\x00' * 4
        with self.assertRaisesRegex(LineageVerificationException, "The CRC verification failed."):
            self.analyzer._check_crc(source_str, crc_str)


class TestLineageSummaryAnalyzer(TestCase):
    """Test LineageSummaryAnalyzer class."""

    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.safe_normalize_path")
    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.FileHandler")
    def setUp(self, *args):
        args[0].return_value = MagicMock()
        self.analyzer = LineageSummaryAnalyzer("fake_path.log")

    @mock.patch.object(LineageSummaryAnalyzer, 'load_events')
    def test_get_latest_info(self, *args):
        """Test get_latest_info method."""
        mock_event = MagicMock()
        mock_event.HasField.side_effect = [False, True]
        args[0].return_value = [mock_event]
        res = self.analyzer.get_latest_info()
        self.assertEqual(res.train_lineage, None)
        self.assertEqual(res.eval_lineage, mock_event)

    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.safe_normalize_path")
    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.FileHandler")
    @mock.patch.object(LineageSummaryAnalyzer, 'get_latest_info')
    def test_get_summary_infos(self, *args):
        """Test get_summary_infos method."""
        args[0].return_value = LineageInfo(None, None, None)
        res = LineageSummaryAnalyzer.get_summary_infos('fake_path.log')
        self.assertEqual(res.train_lineage, None)
        self.assertEqual(res.eval_lineage, None)

    @mock.patch.object(log, "error")
    @mock.patch.object(log, "exception")
    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.safe_normalize_path")
    @mock.patch("mindinsight.lineagemgr.summary.lineage_summary_analyzer.FileHandler")
    @mock.patch.object(LineageSummaryAnalyzer, 'get_latest_info')
    def test_get_summary_infos_except(self, *args):
        """Test get_summary_infos method with exception."""
        args[0].side_effect = LineageVerificationException("mock exception")
        with self.assertRaises(LineageSummaryAnalyzeException):
            _ = LineageSummaryAnalyzer.get_summary_infos('fake_path.log')
