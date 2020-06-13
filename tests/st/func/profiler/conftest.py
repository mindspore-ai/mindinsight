# Copyright 2019 Huawei Technologies Co., Ltd
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
import shutil
import sys
import tempfile

import pytest

from tests.utils import mindspore

sys.modules['mindspore'] = mindspore

BASE_SUMMARY_DIR = tempfile.mkdtemp(prefix='test_profiler_summary_dir_base_')


@pytest.fixture(scope="session")
def create_summary_dir():
    """Create summary directory for profiler module."""

    try:
        if os.path.exists(BASE_SUMMARY_DIR):
            shutil.rmtree(BASE_SUMMARY_DIR)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(BASE_SUMMARY_DIR):
            os.mkdir(BASE_SUMMARY_DIR, mode=mode)
        yield
    finally:
        if os.path.exists(BASE_SUMMARY_DIR):
            shutil.rmtree(BASE_SUMMARY_DIR)
