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
    Test workflow to query single image.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from tests.st.func.datavisual.utils import globals as gbl
from tests.st.func.datavisual.utils.utils import get_url, get_image_tensor_from_bytes

from mindinsight.datavisual.common.enums import PluginNameEnum

TRAIN_JOB_URL = '/v1/mindinsight/datavisual/train-jobs'
PLUGIN_URL = '/v1/mindinsight/datavisual/plugins'
METADATA_URL = '/v1/mindinsight/datavisual/image/metadata'
SINGLE_IMAGE_URL = '/v1/mindinsight/datavisual/image/single-image'


class TestSingleImageFlow:
    """Test Single Image."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_single_image(self, client):
        """Test getting single image."""
        plugin_name = PluginNameEnum.IMAGE.value

        # Get train id by restful api `train-jobs`.
        response = client.get(get_url(TRAIN_JOB_URL, dict()))
        train_jobs = response.get_json()
        train_id = train_jobs.get('train_jobs')[0].get('train_id')

        # Get tag by restful api `plugins`.
        params = dict(train_id=train_id, plugin=plugin_name)
        response = client.get(get_url(PLUGIN_URL, params))
        plugins = response.get_json().get('plugins')
        test_image_tag = plugins.get(plugin_name)[0]

        # Get step by restful api `metadata`.
        params = dict(train_id=train_id, tag=test_image_tag)
        response = client.get(get_url(METADATA_URL, params))
        metadata = response.get_json().get("metadatas")
        test_step = metadata[0].get('step')

        # Query single image.
        expected_image_tensor = gbl.get_single_image(train_id, test_image_tag, test_step)

        params = dict(train_id=train_id, tag=test_image_tag, step=test_step)
        url = get_url(SINGLE_IMAGE_URL, params)
        response = client.get(url)
        recv_image_tensor = get_image_tensor_from_bytes(response.data)

        assert expected_image_tensor.any() == recv_image_tensor.any()
