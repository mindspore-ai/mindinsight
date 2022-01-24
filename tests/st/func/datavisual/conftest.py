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
Description: This file is used for some common util.
"""
import os
import shutil
from unittest.mock import Mock

import pytest
from flask import Response

from mindinsight.conf import settings
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import MAX_DATA_LOADER_SIZE
from mindinsight.datavisual.utils import tools

from ....utils.log_operations import LogOperations
from . import constants
from . import globals as gbl

summaries_metadata = None
mock_data_manager = None
summary_base_dir = constants.SUMMARY_BASE_DIR


@pytest.fixture(autouse=True)
def set_summary_base_dir(monkeypatch):
    """Mock settings.SUMMARY_BASE_DIR."""
    monkeypatch.setattr(settings, 'SUMMARY_BASE_DIR', summary_base_dir)


@pytest.fixture(scope="session")
def init_summary_logs():
    """Init summary logs."""
    try:
        if os.path.exists(summary_base_dir):
            shutil.rmtree(summary_base_dir)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(summary_base_dir):
            os.mkdir(summary_base_dir, mode=mode)
        global summaries_metadata, mock_data_manager
        log_operations = LogOperations()
        summaries_metadata = log_operations.create_summary_logs(summary_base_dir, constants.SUMMARY_DIR_NUM_FIRST,
                                                                constants.SUMMARY_DIR_PREFIX)
        mock_data_manager = DataManager(summary_base_dir)
        thread, brief_thread = mock_data_manager.start_load_data()
        thread.join()
        brief_thread.join()

        summaries_metadata.update(
            log_operations.create_summary_logs(summary_base_dir, constants.SUMMARY_DIR_NUM_SECOND,
                                               constants.SUMMARY_DIR_PREFIX,
                                               constants.SUMMARY_DIR_NUM_FIRST))
        summaries_metadata.update(
            log_operations.create_multiple_logs(summary_base_dir, constants.MULTIPLE_DIR_NAME,
                                                constants.MULTIPLE_LOG_NUM))
        summaries_metadata.update(
            log_operations.create_reservoir_log(summary_base_dir, constants.RESERVOIR_DIR_NAME,
                                                constants.RESERVOIR_STEP_NUM))
        thread, brief_thread = mock_data_manager.start_load_data()
        thread.join()
        brief_thread.join()

        # Maximum number of loads is `MAX_DATA_LOADER_SIZE`.
        for i in range(len(summaries_metadata) - MAX_DATA_LOADER_SIZE):
            summaries_metadata.pop("./%s%d" % (constants.SUMMARY_DIR_PREFIX, i))

        yield
    finally:
        if os.path.exists(summary_base_dir):
            shutil.rmtree(summary_base_dir)


@pytest.fixture(autouse=True)
def populate_globals():
    """Populate globals."""
    gbl.summaries_metadata = summaries_metadata
    gbl.mock_data_manager = mock_data_manager


@pytest.fixture
def client():
    """This fixture is flask client."""

    thread, brief_thread = gbl.mock_data_manager.start_load_data()
    thread.join()
    brief_thread.join()
    data_manager.DATA_MANAGER = gbl.mock_data_manager

    packages = ["mindinsight.backend.datavisual"]

    mock_obj = Mock(return_value=packages)
    tools.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client
