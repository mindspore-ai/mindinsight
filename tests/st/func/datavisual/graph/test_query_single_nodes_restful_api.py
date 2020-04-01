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
    Test search nodes restful api.
Usage:
    pytest tests/st/func/datavisual
"""
import os

import pytest

from .. import globals as gbl
from .....utils.tools import get_url, compare_result_with_file

BASE_URL = '/v1/mindinsight/datavisual/graphs/single-node'


class TestQuerySingleNode:
    """Test query single node restful APIs."""

    graph_results_dir = os.path.join(os.path.dirname(__file__), 'graph_results')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    @pytest.mark.parametrize("node_name, result_file", [
        ('Default/bn1/Reshape1', "test_query_single_node_success_result1.json")
    ])
    def test_query_single_node_success(self, client, node_name, result_file):
        """Query single node."""
        train_id = gbl.get_train_ids()[0]

        params = dict(train_id=train_id,
                      name=node_name)
        url = get_url(BASE_URL, params)
        response = client.get(url)
        assert response.status_code == 200
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(response.get_json(), file_path)
