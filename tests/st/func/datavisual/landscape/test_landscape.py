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
    Test landscape restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import os
import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum

from tests.utils.tools import get_url
import tests.st.func.datavisual.globals as gbl

BASE_URL = '/v1/mindinsight/datavisual/landscape'


class TestLandscpae:
    """Test Landscpae."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_intervals(self, client):
        """Test getting interval data."""
        plugin_name = PluginNameEnum.LANDSCAPE.value
        train_id = gbl.get_train_ids()[0]
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_landscapes = gbl.get_metadata(train_id, tag_name)

        params = dict(train_id=train_id)
        url = get_url(os.path.join(BASE_URL, "intervals"), params)
        response = client.get(url)
        intervals = response.get_json().get("intervals")
        assert expected_landscapes[0].get("value").get("intervals") == intervals[0].get("value")

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_landscapes(self, client):
        """Test getting interval data."""
        plugin_name = PluginNameEnum.LANDSCAPE.value
        train_id = gbl.get_train_ids()[0]
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_landscapes = gbl.get_metadata(train_id, tag_name)

        params = dict(train_id=train_id, type="interval", interval_id=str(hash(str([1, 3]))))
        url = get_url(os.path.join(BASE_URL, "landscapes"), params)
        response = client.get(url)
        landscapes = response.get_json().get("landscapes")
        assert expected_landscapes[0].get("value").get("step_per_epoch") == \
               landscapes[0].get("metadata").get("step_per_epoch")
