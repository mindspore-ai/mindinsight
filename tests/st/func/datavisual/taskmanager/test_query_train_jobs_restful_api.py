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
"""
Function:
    test query train jobs module.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from ..constants import SUMMARY_DIR_NUM
from .....utils.tools import get_url

BASE_URL = '/v1/mindinsight/datavisual/train-jobs'


class TestQueryTrainJobs:
    """Test Query Train Jobs."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs(self, client):
        """Test query train jobs."""
        params = dict(offset=0, limit=10)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('total') == SUMMARY_DIR_NUM
        assert len(result.get('train_jobs')) == min(10, SUMMARY_DIR_NUM)

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs_with_large_offset(self, client):
        """Test query train jobs with large offset."""
        params = dict(offset=10000, limit=10)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('total') == SUMMARY_DIR_NUM
        assert len(result.get('train_jobs')) == min(
            max(0, SUMMARY_DIR_NUM - 1000), 10)

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs_with_exceeded_limit(self, client):
        """Test query train jobs with exceeded limit."""
        params = dict(offset=0, limit=1000)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('error_code') == '50540002'

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs_without_offset(self, client):
        """Test query train jobs without offset."""
        params = dict(limit=10)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('total') == SUMMARY_DIR_NUM
        assert len(result.get('train_jobs')) == min(10, SUMMARY_DIR_NUM)

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs_with_wrong_offse(self, client):
        """Test query train jobs with wrong offse."""
        params = dict(offse=0, limit=10)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('total') == SUMMARY_DIR_NUM
        assert len(result.get('train_jobs')) == min(10, SUMMARY_DIR_NUM)

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_train_jobs_with_lower_offset(self, client):
        """Test query train jobs with lower offset."""
        params = dict(offset=-1, limit=10)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        result = response.get_json()
        assert result.get('error_code') == '50540002'
