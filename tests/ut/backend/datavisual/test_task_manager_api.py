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
    Test train task restful api.
Usage:
    pytest tests/ut/datavisual
"""
from unittest.mock import patch

import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.processors.train_task_manager import TrainTaskManager

from ....utils.log_generators.images_log_generator import ImagesLogGenerator
from ....utils.log_generators.scalars_log_generator import ScalarsLogGenerator
from ....utils.tools import get_url
from .conftest import TRAIN_ROUTES


class TestTrainTask:
    """Test train task api."""

    _scalar_log_generator = ScalarsLogGenerator()
    _image_log_generator = ImagesLogGenerator()

    @pytest.mark.parametrize("plugin_name", ['no_plugin_name', 'not_exist_plugin_name'])
    def test_query_single_train_task_with_plugin_name_not_exist(self, client, plugin_name):
        """
        Parsing unavailable plugin name to single train task.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/single-job').
        request params: plugin_name.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50540002',
            'error_message': "Invalid parameter value. 'plugin_name' only can
                             be one of ['graph', 'image', 'scalar']"
        }
        """
        plugin_name_list = PluginNameEnum.list_members()

        params = dict(plugin_name=plugin_name, train_id="not_exist")
        url = get_url(TRAIN_ROUTES['single_job'], params)

        response = client.get(url)

        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540002'
        assert response['error_msg'] == "Invalid parameter value. 'plugin_name' " \
                                        "only can be one of {}".format(plugin_name_list)

    @patch.object(TrainTaskManager, 'get_single_train_task')
    def test_query_single_train_task_with_plugin_name_exists(self, mock_train_task_manager, client):
        """
        Parsing unavailable plugin name to get single train task.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/single-job').
        request params: plugin_name.

        Expect:
        response status code: 200.
        response json: plugin_name and train_id.
        """

        def get_single_train_task(plugin_name, train_id):
            return f'{plugin_name}{train_id}'

        mock_train_task_manager.side_effect = get_single_train_task

        plugin_name = PluginNameEnum.IMAGE.value
        train_id = "test_id"

        params = dict(plugin_name=plugin_name, train_id=train_id)
        url = get_url(TRAIN_ROUTES['single_job'], params)

        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == f'{plugin_name}{train_id}'

    def test_query_single_train_task_with_param_miss(self, client):
        """
        Parsing unavailable plugin name to get single train task.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/single-job').
        request params: plugin_name.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50540003',
            'error_message': "Param missing. 'plugin_name' is required."
        }
        """
        params = dict()
        url = get_url(TRAIN_ROUTES['single_job'], params)

        response = client.get(url)

        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540003'
        assert response['error_msg'] == "Param missing. 'plugin_name' is required."

    def test_query_plugins_with_manual_update_wrong(self, client):
        """
        Parsing unavailable manual_update to get plugins.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/plugins').
        request params: manual_update.

        Expect:
        response status code: 400.
        response json: {
            'error_code': '50540002',
            'error_message': "Invalid parameter value. The value of manual_update
                must be 'false' or 'true'."
        }
        """
        params = dict(train_id="test_id", manual_update="hhh")
        url = get_url(TRAIN_ROUTES['plugins'], params)

        response = client.get(url)

        assert response.status_code == 400

        response = response.get_json()
        assert response['error_code'] == '50540002'
        assert response['error_msg'] == "Invalid parameter value. The value of manual_update " \
                                        "must be 'false' or 'true'."

    @patch.object(TrainTaskManager, 'get_plugins')
    def test_query_plugins_success(self, mock_train_task_manager, client):
        """
        Parsing unavailable run plugin to get train jobs.

        Test Params:
        request route: GET('/v1/mindinsight/datavisual/train-plugins').
        request params: plugin_name.
        request params: manual_update.

        Expect:
        response status code: 200.
        response json: plugin_name.
        """

        def get_plugins(train_id, manual_update):
            update_str = "false"
            if manual_update:
                update_str = "true"
            return f'{train_id}{update_str}'

        train_id = "test_id"
        manual_update = "true"
        mock_train_task_manager.side_effect = get_plugins

        params = dict(train_id=train_id, manual_update=manual_update)
        url = get_url(TRAIN_ROUTES['plugins'], params)

        response = client.get(url)
        assert response.status_code == 200
        results = response.get_json()
        assert results == f'{train_id}{manual_update}'
