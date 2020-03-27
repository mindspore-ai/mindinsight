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
    Test workflow to query image metadata.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from tests.st.func.datavisual.utils import globals as gbl
from tests.st.func.datavisual.utils.utils import get_url

from mindinsight.datavisual.common.enums import PluginNameEnum

TRAIN_JOB_URL = '/v1/mindinsight/datavisual/train-jobs'
PLUGIN_URL = '/v1/mindinsight/datavisual/plugins'
METADATA_URL = '/v1/mindinsight/datavisual/image/metadata'


class TestImageMetadataFlow:
    """Test Image Metadata."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_image_metadata(self, client):
        """Test getting image metadata."""
        plugin_name = PluginNameEnum.IMAGE.value

        # Get train id by restful api `train-jobs`.
        response = client.get(get_url(TRAIN_JOB_URL, dict()))
        train_jobs = response.get_json()
        train_id = train_jobs.get('train_jobs')[-1].get('train_id')

        # Get tag by restful api `plugins`.
        params = dict(train_id=train_id, plugin=plugin_name)
        response = client.get(get_url(PLUGIN_URL, params))
        plugins = response.get_json().get('plugins')
        test_image_tag = plugins.get(plugin_name)[0]

        expected_metadata = gbl.get_metadata(train_id, test_image_tag)

        # Query image metadata.
        params = dict(train_id=train_id, tag=test_image_tag)
        response = client.get(get_url(METADATA_URL, params))
        metadata = response.get_json().get("metadatas")

        assert metadata == expected_metadata
