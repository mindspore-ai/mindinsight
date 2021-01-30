# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""UT for explainer.manager.explain_manager"""
import os
import threading
import time
from unittest.mock import patch

from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.explainer.manager.explain_loader import ExplainLoader
from mindinsight.explainer.manager.explain_loader import _LoaderStatus
from mindinsight.explainer.manager.explain_parser import ExplainParser


class _MockStat:
    def __init__(self, _):
        self.st_ctime = 1
        self.st_mtime = 1
        self.st_size = 1


class TestExplainLoader:
    """Test explain loader class."""
    @patch.object(ExplainParser, 'list_events')
    @patch.object(FileHandler, 'list_dir')
    @patch.object(FileHandler, 'is_file')
    @patch.object(os, 'stat')
    def test_stop(self, mock_stat, mock_is_file, mock_list_dir, mock_list_events):
        """Test stop function."""
        mock_is_file.return_value = True
        mock_list_dir.return_value = ['events.summary.123.host_explain']
        mock_list_events.return_value = (True, False, None)


        mock_stat.side_effect = _MockStat

        loader = ExplainLoader(
            loader_id='./summary_dir',
            summary_dir='./summary_dir')

        def _stop_loader(explain_loader):
            while explain_loader.status != _LoaderStatus.LOADING.value:
                time.sleep(0.01)
            explain_loader.stop()

        thread = threading.Thread(target=_stop_loader, args=[loader], daemon=True)
        thread.start()

        loader.load()
        assert loader.status == _LoaderStatus.STOP.value

    @patch.object(ExplainParser, 'list_events')
    @patch.object(FileHandler, 'list_dir')
    @patch.object(FileHandler, 'is_file')
    @patch.object(os, 'stat')
    def test_loaded_with_is_end(self, mock_stat, mock_is_file, mock_list_dir, mock_list_events):
        """Test loading function."""
        mock_is_file.return_value = True
        mock_list_dir.return_value = ['events.summary.123.host_explain']
        mock_list_events.return_value = (True, True, None)

        mock_stat.side_effect = _MockStat

        loader = ExplainLoader(
            loader_id='./summary_dir',
            summary_dir='./summary_dir')

        loader.load()
        assert loader.status == _LoaderStatus.LOADED.value
