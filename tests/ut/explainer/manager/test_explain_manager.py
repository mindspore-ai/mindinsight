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
"""UT for explainer.manager.explain_loader."""
import os
import threading
import time
from unittest.mock import patch

from mindinsight.explainer.manager.explain_loader import ExplainLoader
from mindinsight.explainer.manager.explain_loader import _LoaderStatus
from mindinsight.explainer.manager.explain_manager import ExplainManager
from mindinsight.explainer.manager.explain_manager import _ExplainManagerStatus


class TestExplainManager:
    """Test explain manager class."""

    def test_stop_load_data_not_loading_status(self):
        """Test stop load data when the status is not loading."""
        manager = ExplainManager('./summary_dir')
        assert manager.status == _ExplainManagerStatus.INIT.value

        manager.status = _ExplainManagerStatus.DONE.value
        manager._stop_load_data()
        assert manager.status == _ExplainManagerStatus.DONE.value

    @patch.object(os, 'stat')
    def test_stop_load_data_with_loading_status(self, mock_stat):
        """Test stop load data with status is loading."""
        class _MockStat:
            def __init__(self, _):
                self.st_ctime = 1
                self.st_mtime = 1
                self.st_size = 1

        mock_stat.side_effect = _MockStat

        manager = ExplainManager('./summary_dir')
        manager.status = _ExplainManagerStatus.LOADING.value
        loader_count = 3
        for i in range(loader_count):
            loader = ExplainLoader(f'./summary_dir{i}', f'./summary_dir{i}')
            loader.status = _LoaderStatus.LOADING.value
            manager._loader_pool[i] = loader

        def _wrapper(loader_manager):
            assert loader_manager.status == _ExplainManagerStatus.LOADING.value
            time.sleep(0.01)
            loader_manager.status = _ExplainManagerStatus.DONE.value
        thread = threading.Thread(target=_wrapper, args=(manager,), daemon=True)
        thread.start()
        manager._stop_load_data()
        for loader in manager._loader_pool.values():
            assert loader.status == _LoaderStatus.STOP.value
        assert manager.status == _ExplainManagerStatus.DONE.value

    def test_stop_load_data_with_after_cache_loaders(self):
        """
        Test stop load data that is triggered by get a not in loader pool job.

        In this case, we will mock the cache_loader function, and set status to STOP by other thread.
        """
        manager = ExplainManager('./summary_dir')

        def _mock_cache_loaders():
            for _ in range(3):
                time.sleep(0.1)
        manager._cache_loaders = _mock_cache_loaders
        load_data_thread = threading.Thread(target=manager._load_data, name='manager_load_data', daemon=True)
        stop_thread = threading.Thread(target=manager._stop_load_data, name='stop_load_data', daemon=True)
        load_data_thread.start()
        while manager.status != _ExplainManagerStatus.LOADING.value:
            continue
        stop_thread.start()
        stop_thread.join()
        assert manager.status == _ExplainManagerStatus.DONE.value
