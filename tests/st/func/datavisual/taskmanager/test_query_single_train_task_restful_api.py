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
    Test query single train task module.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest
from tests.st.func.datavisual.utils import globals as gbl
from tests.st.func.datavisual.utils.utils import get_url

from mindinsight.datavisual.common.enums import PluginNameEnum

BASE_URL = '/v1/mindinsight/datavisual/single-job'


class TestQuerySingleTrainTask:
    """Test Query Single Train Task."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_query_single_train_task(self, client):
        """"Test query single train task."""
        for train_id in gbl.summaries_metadata:
            expected = gbl.summaries_metadata.get(train_id).get("plugins")
            for plugin_name in PluginNameEnum.list_members():
                params = dict(train_id=train_id, plugin_name=plugin_name)
                url = get_url(BASE_URL, params)
                response = client.get(url)
                result = response.get_json()
                tags = result["train_jobs"][0]["tags"]
                if plugin_name == PluginNameEnum.GRAPH.value:
                    assert len(tags) == len(expected[plugin_name])
                else:
                    assert sorted(tags) == sorted(expected[plugin_name])
