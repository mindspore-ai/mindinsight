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
"""Test profiler restful api."""
import json
from unittest import TestCase, mock

from flask import Response

from mindinsight.backend.application import APP


class TestProfilerRestfulApi(TestCase):
    """Test the restful api of profiler."""

    def setUp(self):
        """Test init."""
        APP.response_class = Response
        self.app_client = APP.test_client()
        self.url = '/v1/mindinsight/profile/ops/search?train_id=run1&profile=profiler'

    @mock.patch('mindinsight.backend.profiler.profile_api.check_train_job_and_profiler_dir')
    @mock.patch('mindinsight.backend.lineagemgr.lineage_api.settings')
    @mock.patch('mindinsight.profiler.analyser.base_analyser.BaseAnalyser.query')
    def test_ops_search_success(self, *args):
        """Test the success of ops/search."""
        base_dir = '/path/to/test_profiler_base'
        expect_result = {
            'object': ["test"],
            'count': 1
        }
        args[0].return_value = expect_result
        args[1].SUMMARY_BASE_DIR = base_dir

        body_data = {
            "op_type": "aicore_type"
        }
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(200, response.status_code)
        self.assertDictEqual(expect_result, response.get_json())

    @mock.patch('mindinsight.profiler.analyser.base_analyser.BaseAnalyser.query')
    def test_ops_search_failed(self, *args):
        """Test the failed of ops/search."""
        expect_result = {
            'object': ["test"],
            'count': 1
        }
        args[0].return_value = expect_result
        response = self.app_client.post(self.url, data=json.dumps(1))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546082',
            'error_msg': "Param type error. Invalid search_condition type, it should be dict."
        }
        self.assertDictEqual(expect_result, response.get_json())

        body_data = {"op_type": "1"}
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546183',
        }
        result = response.get_json()
        del result["error_msg"]
        self.assertDictEqual(expect_result, result)

        body_data = {"op_type": "aicore_type", "device_id": 1}
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546182',
        }
        result = response.get_json()
        del result["error_msg"]
        self.assertDictEqual(expect_result, result)

    @mock.patch('mindinsight.profiler.analyser.base_analyser.BaseAnalyser.query')
    def test_ops_search_search_condition_failed(self, *args):
        """Test search condition error."""
        expect_result = {
            'object': ["test"],
            'count': 1
        }
        args[0].return_value = expect_result
        body_data = {"op_type": "aicore_type", "device_id": "1", "group_condition": 1}
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546184',
        }
        result = response.get_json()
        del result["error_msg"]
        self.assertDictEqual(expect_result, result)

        body_data = {"op_type": "aicore_type", "device_id": "1", "sort_condition": {"type": 1}}
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546185',
        }
        result = response.get_json()
        del result["error_msg"]
        self.assertDictEqual(expect_result, result)

        body_data = {"op_type": "aicore_type", "device_id": "1",
                     "filter_condition": {"op_type": {"in": ["1", 2]}}}
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50546186',
        }
        result = response.get_json()
        del result["error_msg"]
        self.assertDictEqual(expect_result, result)
