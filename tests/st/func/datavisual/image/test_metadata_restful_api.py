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
Functions:
    Test image metadata restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from mindinsight.conf import settings
from mindinsight.datavisual.common.enums import PluginNameEnum

from .....utils.tools import get_url
from .. import globals as gbl
from ..constants import MULTIPLE_TRAIN_ID, RESERVOIR_TRAIN_ID

BASE_URL = '/v1/mindinsight/datavisual/image/metadata'


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
        """Test getting image metadata."""
        plugin_name = PluginNameEnum.IMAGE.value
        train_id = gbl.get_train_ids()[0]
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_metadata = gbl.get_metadata(train_id, tag_name)

        params = dict(train_id=train_id, tag=tag_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        metadata = response.get_json().get("metadatas")

        assert metadata == expected_metadata

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_metadata_multiple(self, client):
        """Test getting image metadata, mainly test a summary dir with multiple logs."""
        plugin_name = PluginNameEnum.IMAGE.value
        train_id = MULTIPLE_TRAIN_ID
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_metadata = gbl.get_metadata(train_id, tag_name)

        params = dict(train_id=train_id, tag=tag_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        metadata = response.get_json().get("metadatas")

        assert len(metadata) == len(expected_metadata)
        for i in range(len(metadata)):
            assert metadata[i]['step'] == expected_metadata[i]['step'] \
                   and metadata[i]['width'] == expected_metadata[i]['width'] \
                   and metadata[i]['height'] == expected_metadata[i]['height']

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_metadata_reservoir(self, client):
        """Test getting image metadata, mainly test reservoir."""
        plugin_name = PluginNameEnum.IMAGE.value
        train_id = RESERVOIR_TRAIN_ID
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        params = dict(train_id=train_id, tag=tag_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        metadata = response.get_json().get("metadatas")
        assert len(metadata) == settings.MAX_IMAGE_STEP_SIZE_PER_TAG
