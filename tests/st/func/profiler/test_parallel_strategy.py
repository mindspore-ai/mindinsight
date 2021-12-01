# Copyright 2021 Huawei Technologies Co., Ltd
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
Function:
    Test parsing parallel strategy.
Usage:
    pytest tests/st/func/profiler
"""
import os
import shutil
import time

from mindinsight.conf import settings

from mindinsight.profiler.analyser.parallel_strategy_analyser import Status

from tests.utils.tools import get_url, compare_result_with_file
from tests.st.func.profiler import RAW_DATA_BASE
from tests.st.func.profiler.conftest import TEMP_BASE_SUMMARY_DIR

import pytest


URL = '/v1/mindinsight/profile/parallel-strategy/graphs'


@pytest.fixture(autouse=True)
def set_summary_base_dir(monkeypatch):
    """Mock settings.SUMMARY_BASE_DIR."""
    monkeypatch.setattr(settings, 'SUMMARY_BASE_DIR', TEMP_BASE_SUMMARY_DIR)


@pytest.mark.usefixtures("create_summary_dir")
class TestParallelStrategy:
    """Test parallel strategy."""

    RESULT_DIR = os.path.join(os.path.dirname(__file__), 'parallel_strategy_result')

    @classmethod
    def setup_class(cls):
        summary_base_dir = TEMP_BASE_SUMMARY_DIR
        profiler_dir = os.path.join(summary_base_dir, 'profiler')
        os.mkdir(profiler_dir)

        source_path = os.path.join(RAW_DATA_BASE, 'parallel_strategy')
        for file in os.listdir(source_path):
            file_path = os.path.join(source_path, file)
            shutil.copy(file_path, profiler_dir)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_parallel_strategy(self, client):
        """Test getting parallel strategy success."""
        params = dict(train_id='./')
        url = get_url(URL, params)
        response = client.get(url)
        assert response.status_code == 200

        ret_json = response.get_json()
        while not ret_json['status'] == Status.FINISH.value:
            time.sleep(0.2)
            response = client.get(url)
            ret_json = response.get_json()

        file_path = os.path.join(self.RESULT_DIR, 'parallel_strategy.json')
        compare_result_with_file(ret_json, file_path)
