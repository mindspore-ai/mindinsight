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
    Test scalar metadata restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest
from .. import globals as gbl
from .....utils.tools import get_url

from mindinsight.datavisual.common.enums import PluginNameEnum

BASE_URL = '/v1/mindinsight/datavisual/scalar/metadata'


class TestMetadata:
    """Test Metadata."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_metadata(self, client):
        """Test getting scalar metadata."""
        plugin_name = PluginNameEnum.SCALAR.value
        train_id = gbl.get_train_ids()[0]
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_metadata = gbl.get_metadata(train_id, tag_name)

        params = dict(train_id=train_id, tag=tag_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        metadata = response.get_json().get("metadatas")

        for metadata, expected_metadata in zip(metadata, expected_metadata):
            assert metadata.get("wall_time") == expected_metadata.get("wall_time")
            assert metadata.get("step") == expected_metadata.get("step")
            assert metadata.get("value") - expected_metadata.get("value") < 1e-6
