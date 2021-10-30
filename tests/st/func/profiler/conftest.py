# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
"""The st config."""

import os
import sys
import tempfile
import shutil

from unittest.mock import Mock
from flask import Response

from mindinsight.datavisual.utils import tools
from tests.st.func.profiler import RAW_DATA_BASE
from tests.utils import mindspore

import pytest


sys.modules['mindspore'] = mindspore

BASE_SUMMARY_DIR = os.path.realpath(os.path.join(RAW_DATA_BASE, "run_1"))
# Notice:
# 1. Run_2 is new performance data.
# 2. The names of some files have been changed. \
#    For example, timeline_display_1.json becomes ascend_timeline_display_1.json.
# 3. Some new files have been added. For example, aicpu_intermediate_1.csv.
# 4. It is recommended that the new mindinsight st ut test be based on this version of the performance file.
BASE_SUMMARY_DIR_RUN_2 = os.path.realpath(os.path.join(RAW_DATA_BASE, "run_2"))
BASE_SUMMARY_DIR_RUN_3 = os.path.realpath(os.path.join(RAW_DATA_BASE, "run_3"))
BASE_SUMMARY_DIR_RUN_4 = os.path.realpath(os.path.join(RAW_DATA_BASE, "run_4"))

TEMP_BASE_SUMMARY_DIR = tempfile.mkdtemp(suffix='summary')


@pytest.fixture(scope="session")
def create_summary_dir():
    """Create summary directory."""
    try:
        if os.path.exists(TEMP_BASE_SUMMARY_DIR):
            shutil.rmtree(TEMP_BASE_SUMMARY_DIR)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(TEMP_BASE_SUMMARY_DIR):
            os.mkdir(TEMP_BASE_SUMMARY_DIR, mode=mode)
        yield
    finally:
        if os.path.exists(TEMP_BASE_SUMMARY_DIR):
            shutil.rmtree(TEMP_BASE_SUMMARY_DIR)


@pytest.fixture
def client():
    """This fixture is flask client."""

    packages = ["mindinsight.backend.profiler"]

    mock_obj = Mock(return_value=packages)
    tools.find_app_package = mock_obj

    from mindinsight.backend.application import APP
    APP.response_class = Response
    app_client = APP.test_client()

    yield app_client
