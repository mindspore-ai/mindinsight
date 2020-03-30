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
    Test image single image restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum

from .....utils.tools import get_image_tensor_from_bytes, get_url
from .. import globals as gbl

BASE_URL = '/v1/mindinsight/datavisual/image/single-image'


class TestSingleImage:
    """Test query single image."""

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_single_image(self, client):
        """Test getting single image."""
        step = 1
        plugin_name = PluginNameEnum.IMAGE.value
        train_id = gbl.get_train_ids()[0]
        tag_name = gbl.get_tags(train_id, plugin_name)[0]
        expected_image_tensor = gbl.get_single_image(train_id, tag_name, step)

        params = dict(train_id=train_id, tag=tag_name, step=step)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        recv_image_tensor = get_image_tensor_from_bytes(response.data)

        assert expected_image_tensor.any() == recv_image_tensor.any()

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_single_image_no_train_id(self, client):
        """Test getting single image without train id."""
        params = dict(tag="tag_name_0/image", step=1)
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
    def test_single_image_no_tag(self, client):
        """Test getting single image without tag."""
        params = dict(train_id="./summary0", step=1)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'tag' is required."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_single_image_no_step(self, client):
        """Test getting single image without step."""
        params = dict(train_id="./summary0", tag="tag_name_0/image")
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'step' is required."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("train_id", ["@#$", "./summary_x", dict()])
    def test_single_image_with_special_train_id(self, client, train_id):
        """Test passing train_id with special character, invalid value, and wrong type."""
        params = dict(train_id=train_id, tag="tag_name_0/image", step=1)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50545005'
        assert response['error_msg'] == "Train job is not exist. Detail: Can not find the given train job in cache."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("tag", ["@#$", "tag_name_xxx/image", dict()])
    def test_single_image_with_special_tag(self, client, tag):
        """Test passing tag with special character, invalid value, and wrong type."""
        train_id = gbl.get_train_ids()[0]
        params = dict(train_id=train_id, tag=tag, step=1)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '5054500D'
        assert response['error_msg'] == "Image is not exist. Detail: Invalid parameter value. " \
                                        "Can not find any data in this train job by given tag."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_single_image_with_invalid_step(self, client):
        """Test getting single image with invalid step."""
        train_id = gbl.get_train_ids()[0]
        params = dict(train_id=train_id, tag="tag_name_0/image", step=1000)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '5054500D'
        assert response['error_msg'] == "Image is not exist. Detail: " \
                                        "Can not find the step with given train job id and tag."

    @pytest.mark.level1
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("step", ["@#$", dict()])
    def test_single_image_with_special_step(self, client, step):
        """Test getting single image with special step."""
        params = dict(train_id="./summary0", tag="tag_name_0/image", step=step)
        url = get_url(BASE_URL, params)

        response = client.get(url)
        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540001'
        assert response['error_msg'] == "Invalid parameter type. 'step' expect Integer type."
