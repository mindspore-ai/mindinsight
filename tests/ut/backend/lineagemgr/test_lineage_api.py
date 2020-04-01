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
"""Test the module of lineage_api."""
import json
import os
from unittest import TestCase, mock

from flask import Response

from mindinsight.backend.application import APP
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageQuerySummaryDataError

LINEAGE_FILTRATION_BASE = {
    'accuracy': None,
    'mae': None,
    'mse': None,
    'loss_function': 'SoftmaxCrossEntropyWithLogits',
    'train_dataset_path': None,
    'train_dataset_count': 64,
    'test_dataset_path': None,
    'test_dataset_count': None,
    'network': 'str',
    'optimizer': 'Momentum',
    'learning_rate': 0.11999999731779099,
    'epoch': 12,
    'batch_size': 32,
    'loss': 0.029999999329447746,
    'model_size': 128
}
LINEAGE_FILTRATION_RUN1 = {
    'accuracy': 0.78,
    'mae': None,
    'mse': None,
    'loss_function': 'SoftmaxCrossEntropyWithLogits',
    'train_dataset_path': None,
    'train_dataset_count': 64,
    'test_dataset_path': None,
    'test_dataset_count': 64,
    'network': 'str',
    'optimizer': 'Momentum',
    'learning_rate': 0.11999999731779099,
    'epoch': 14,
    'batch_size': 32,
    'loss': 0.029999999329447746,
    'model_size': 128
}


class TestSearchModel(TestCase):
    """Test the restful api of search_model."""

    def setUp(self):
        """Test init."""
        APP.response_class = Response
        self.app_client = APP.test_client()
        self.url = '/v1/mindinsight/models/model_lineage'

    @mock.patch('mindinsight.backend.lineagemgr.lineage_api.settings')
    @mock.patch('mindinsight.backend.lineagemgr.lineage_api.filter_summary_lineage')
    def test_search_model_success(self, *args):
        """Test the success of model_success."""
        base_dir = '/path/to/test_lineage_summary_dir_base'
        args[0].return_value = {
            'object': [
                {
                    'summary_dir': base_dir,
                    **LINEAGE_FILTRATION_BASE
                },
                {
                    'summary_dir': os.path.join(base_dir, 'run1'),
                    **LINEAGE_FILTRATION_RUN1
                }
            ],
            'count': 2
        }
        args[1].SUMMARY_BASE_DIR = base_dir

        body_data = {
            'limit': 10,
            'offset': 0,
            'sorted_name': 'summary_dir',
            'sorted_type': None
        }
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(200, response.status_code)
        expect_result = {
            'object': [
                {
                    'summary_dir': './',
                    **LINEAGE_FILTRATION_BASE
                },
                {
                    'summary_dir': './run1',
                    **LINEAGE_FILTRATION_RUN1
                }
            ],
            'count': 2
        }
        self.assertDictEqual(expect_result, response.get_json())

    @mock.patch('mindinsight.backend.lineagemgr.lineage_api.settings')
    @mock.patch('mindinsight.backend.lineagemgr.lineage_api.filter_summary_lineage')
    def test_search_model_fail(self, *args):
        """Test the function of model_lineage with exception."""
        response = self.app_client.post(self.url, data='xxx')
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50540002',
            'error_msg': 'Invalid parameter value. Json data parse failed.'
        }
        self.assertDictEqual(expect_result, response.get_json())

        args[0].side_effect = LineageQuerySummaryDataError('xxx')
        args[1].SUMMARY_BASE_DIR = '/path/to/test_lineage_summary_dir_base'
        body_data = {
            'limit': 10,
            'offset': 0,
            'sorted_name': 'summary_dir',
            'sorted_type': None
        }
        response = self.app_client.post(self.url, data=json.dumps(body_data))
        self.assertEqual(400, response.status_code)
        expect_result = {
            'error_code': '50542215',
            'error_msg': 'Query summary data error: xxx'
        }
        self.assertDictEqual(expect_result, response.get_json())
