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
"""The st config for optimizer."""

import os
import shutil
import tempfile
from unittest.mock import Mock

import pytest
from flask import Response

from mindinsight.lineagemgr.cache_item_updater import LineageCacheItemUpdater
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.datavisual.utils import tools

SUMMARY_BASE_DIR = tempfile.NamedTemporaryFile(prefix='test_optimizer_summary_dir_base_').name
MOCK_DATA_MANAGER = DataManager(SUMMARY_BASE_DIR)
MOCK_DATA_MANAGER.register_brief_cache_item_updater(LineageCacheItemUpdater())
MOCK_DATA_MANAGER.start_load_data().join()


@pytest.fixture(scope="session")
def init_summary_logs():
    """Create summary directory."""
    try:
        if os.path.exists(SUMMARY_BASE_DIR):
            shutil.rmtree(SUMMARY_BASE_DIR)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(SUMMARY_BASE_DIR):
            os.mkdir(SUMMARY_BASE_DIR, mode=mode)
        yield
    finally:
        if os.path.exists(SUMMARY_BASE_DIR):
            shutil.rmtree(SUMMARY_BASE_DIR)


@pytest.fixture
def client():
    """This fixture is flask client."""
    data_manager.DATA_MANAGER = MOCK_DATA_MANAGER

    packages = ["mindinsight.backend.optimizer"]

    mock_obj = Mock(return_value=packages)
    tools.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client
