# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
    Test query nodes restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import os

import pytest

from .. import globals as gbl
from .....utils.tools import get_url, compare_result_with_file

BASE_URL = '/v1/mindinsight/datavisual/graphs/nodes'


class TestQueryNodes:
    """Test query nodes restful APIs."""

    graph_results_dir = os.path.join(os.path.dirname(__file__), 'graph_results')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("node_name, result_file", [
        ('', "test_query_nodes_success_result1.json"),
        ("Default", "test_query_nodes_success_result2.json"),
        ("Default/bn1/Reshape[12]_1", "test_query_nodes_success_result3.json")
    ])
    def test_list_node_success(self, client, node_name, result_file):
        """Query the name scope node."""
        train_id = gbl.get_train_ids()[0]

        params = dict(train_id=train_id,
                      name=node_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        assert response.status_code == 200
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(response.get_json(), file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("node_name, result_file", [
        ('', "test_query_optimized_nodes_success_result1.json"),
        ("Default", "test_query_optimized_nodes_success_result2.json")
    ])
    def test_list_node_for_optimized_graph_success(self, client, node_name, result_file):
        """Query the name scope node for optimized graph."""
        train_id = gbl.get_train_ids()[0]

        params = dict(train_id=train_id,
                      name=node_name,
                      mode="optimize")
        url = get_url(BASE_URL, params)
        response = client.get(url)
        assert response.status_code == 200
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(response.get_json(), file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("node_name", [
        "Default/bn1/Reshape[12]_1"
    ])
    def test_list_node_for_optimized_graph_fail(self, client, node_name):
        """Query the name scope node for optimized graph."""
        train_id = gbl.get_train_ids()[0]

        params = dict(train_id=train_id,
                      name=node_name,
                      mode="optimize")
        url = get_url(BASE_URL, params)
        response = client.get(url)
        assert response.json.get('error_code') == '50545009'
