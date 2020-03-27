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
Function:
    Test plugins restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from tests.st.func.datavisual.utils import globals as gbl
from tests.st.func.datavisual.utils.utils import get_url

from mindinsight.datavisual.common.enums import PluginNameEnum

BASE_URL = '/v1/mindinsight/datavisual/plugins'


class TestPlugins:
    """Test Plugins."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_plugins(self, client):
        """Test getting plugins."""
        train_id = gbl.get_train_ids()[0]
        expected_plugins = gbl.summaries_metadata.get(train_id).get("plugins")

        params = dict(train_id=train_id)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        plugins = response.get_json().get('plugins')
        for plugin_name in PluginNameEnum.list_members():
            if plugin_name == PluginNameEnum.GRAPH.value:
                assert len(plugins.get(plugin_name)) == len(expected_plugins.get(plugin_name))
            else:
                assert sorted(plugins.get(plugin_name)) == sorted(expected_plugins.get(plugin_name))

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_plugins_no_train_id(self, client):
        """Test getting plugins without train_id."""
        params = dict()
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'train_id' is required."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("train_id", ["@#$", "./\x00home", "././/not_exist_id", dict()])
    def test_plugins_with_special_train_id(self, client, train_id):
        """Test passing train_id with special character, null_byte, invalid id, and wrong type."""
        params = dict(train_id=train_id)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540002'
        assert response['error_msg'] == "Invalid parameter value. Can not find " \
                                        "the train job in data manager."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("manual_update", ["@#$", "tur", dict()])
    def test_plugins_with_special_manual_update(self, client, manual_update):
        """Test passing manual_update with special character, wrong value, and wrong type."""
        train_id = gbl.get_train_ids()[0]
        params = dict(train_id=train_id, manual_update=manual_update)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540002'
        assert response['error_msg'] == "Invalid parameter value. The value of " \
                                        "manual_update must be 'false' or 'true'."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_plugins_with_train_id_not_in_cache(self, client):
        """Test getting plugins with train id that not in loader pool."""
        train_id = "./summary0"
        params = dict(train_id=train_id)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        plugins = response.get_json().get('plugins')

        for plugin_name in PluginNameEnum.list_members():
            # Empty list.
            assert not plugins.get(plugin_name)
