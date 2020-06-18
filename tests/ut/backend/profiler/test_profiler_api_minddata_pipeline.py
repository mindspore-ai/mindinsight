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
"""Test profiler restful api of minddata pipeline."""
import json
from unittest import mock

from flask import Response
from marshmallow import ValidationError

from mindinsight.backend.application import APP


class TestMinddataPipelineApi:
    """Test the minddata pipeline restful api of profiler."""
    def setup_method(self):
        """Test init."""
        APP.response_class = Response
        self._app_client = APP.test_client()
        self._url_op_queue = '/v1/mindinsight/profile/minddata-pipeline/op-queue'
        self._url_queue = '/v1/mindinsight/profile/minddata-pipeline/queue'

    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    @mock.patch('mindinsight.profiler.analyser.base_analyser.BaseAnalyser.query')
    def test_get_minddata_pipeline_op_queue_info_1(self, *args):
        """Test the function of querying operator and queue information."""
        expect_result = {
            'col_name': [
                'op_id', 'op_type', 'output_queue_average_size',
                'output_queue_length', 'output_queue_usage_rate',
                'sample_interval', 'parent_id', 'children_id'],
            'object': [],
            'size': 0
        }
        args[0].return_value = expect_result
        args[1].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'

        url = self._url_op_queue + '?train_id=run1&profile=profiler'
        body_data = {}
        response = self._app_client.post(url, data=json.dumps(body_data))
        assert response.status_code == 200
        assert expect_result == response.get_json()

    def test_get_minddata_pipeline_op_queue_info_2(self):
        """Test the function of querying operator and queue information."""
        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. No profiler_dir or train_id.'
        }

        url = self._url_op_queue + '?train_id=run1'
        body_data = {}
        response = self._app_client.post(url, data=json.dumps(body_data))
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.validate_and_normalize_path')
    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    def test_get_minddata_pipeline_op_queue_info_3(self, *args):
        """Test the function of querying operator and queue information."""
        args[0].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'
        args[1].side_effect = ValidationError('xxx')

        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. Invalid profiler dir.'
        }

        url = self._url_op_queue + '?train_id=run1&profile=profiler'
        body_data = {}
        response = self._app_client.post(url, data=json.dumps(body_data))
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    def test_get_minddata_pipeline_op_queue_info_4(self, *args):
        """Test the function of querying operator and queue information."""
        args[0].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'

        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. Json data parse failed.'
        }

        url = self._url_op_queue + '?train_id=run1&profile=profiler'
        response = self._app_client.post(url, data='xxx')
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    @mock.patch('mindinsight.profiler.analyser.minddata_pipeline_analyser.'
                'MinddataPipelineAnalyser.get_op_and_parent_op_info')
    def test_get_minddata_pipeline_queue_info_1(self, *args):
        """Test the function of querying queue information."""
        expect_result = {
            'current_op': {
                'op_id': 1,
                'op_type': 'Shuffle',
                'num_workers': 1
            },
            'queue_info': {
                'output_queue_size': [10, 20, 30],
                'output_queue_average_size': 20.0,
                'output_queue_length': 64,
                'output_queue_usage_rate': 0.3125,
                'sample_interval': 10
            },
            'parent_op': {
                'op_id': 0,
                'op_type': 'Batch',
                'num_workers': 4
            }
        }
        args[0].return_value = expect_result
        args[1].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'
        url = self._url_queue + '?train_id=run1&profile=profiler&device_id=0&op_id=1'
        response = self._app_client.get(url)
        assert response.status_code == 200
        assert expect_result == response.get_json()

    def test_get_minddata_pipeline_queue_info_2(self):
        """Test the function of querying queue information."""
        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. No profiler_dir or train_id.'
        }

        url = self._url_queue + '?profile=profiler&device_id=0&op_id=1'
        response = self._app_client.get(url)
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.validate_and_normalize_path')
    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    def test_get_minddata_pipeline_queue_info_3(self, *args):
        """Test the function of querying queue information."""
        args[0].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'
        args[1].side_effect = ValidationError('xxx')

        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. Invalid profiler dir.'
        }

        url = self._url_queue + '?train_id=run1&profile=profiler&device_id=0&op_id=1'
        response = self._app_client.get(url)
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    def test_get_minddata_pipeline_queue_info_4(self, *args):
        """Test the function of querying queue information."""
        args[0].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'

        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. '
                         'Invalid operator id or operator id does not exist.'
        }

        url = self._url_queue + '?train_id=run1&profile=profiler&device_id=0'
        response = self._app_client.get(url)
        assert response.status_code == 400
        assert expect_result == response.get_json()

    @mock.patch('mindinsight.backend.profiler.profile_api.settings')
    def test_get_minddata_pipeline_queue_info_5(self, *args):
        """Test the function of querying queue information."""
        args[0].SUMMARY_BASE_DIR = '/path/to/summary_base_dir'

        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. '
                         'Invalid operator id or operator id does not exist.'
        }

        url = self._url_queue + '?train_id=run1&profile=profiler&device_id=0&op_id=xx'
        response = self._app_client.get(url)
        assert response.status_code == 400
        assert expect_result == response.get_json()
