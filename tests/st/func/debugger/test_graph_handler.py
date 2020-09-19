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
Description: This file is used for testing graph handler.
"""
import os

import pytest

from ....utils.tools import compare_result_with_file
from .conftest import init_graph_handler


class TestGraphHandler:
    """Test GraphHandler."""
    graph_results_dir = os.path.join(os.path.dirname(__file__), 'expect_results')
    graph_handler = init_graph_handler()

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("filter_condition, result_file", [
        (None, "graph_handler_get_1_no_filter_condintion.json"),
        ({'name': 'Default'}, "graph_handler_get_2_list_nodes.json"),
        ({'name': 'Default/network-WithLossCell/_backbone-LeNet5/conv1-Conv2d/Cast-op190', 'single_node': True},
         "graph_handler_get_3_single_node.json")
    ])
    def test_get(self, filter_condition, result_file):
        """Test get."""
        result = self.graph_handler.get(filter_condition)
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(result, file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("node_name, result_file", [
        ("Default/network-WithLossCell/_backbone-LeNet5/conv1-Conv2d/Cast-op190",
         "tenor_hist_0.json"),
        ("Default/optimizer-Momentum/ApplyMomentum[8]_1/ApplyMomentum-op22",
         "tensor_hist_1.json")
    ])
    def test_get_tensor_history(self, node_name, result_file):
        """Test get tensor history."""
        result = self.graph_handler.get_tensor_history(node_name)
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(result, file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("pattern, result_file", [
        ("withlogits", "search_nodes_0.json"),
        ("cst", "search_node_1.json")
    ])
    def test_search_nodes(self, pattern, result_file):
        """Test search nodes."""
        result = self.graph_handler.search_nodes(pattern)
        file_path = os.path.join(self.graph_results_dir, result_file)
        compare_result_with_file(result, file_path)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("node_name, expect_type", [
        ("Default/network-WithLossCell/_loss_fn-SoftmaxCrossEntropyWithLogits/cst1", 'Const'),
        ("Default/TransData-op99", "TransData")
    ])
    def test_get_node_type(self, node_name, expect_type):
        """Test get node type."""
        node_type = self.graph_handler.get_node_type(node_name)
        assert node_type == expect_type

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("node_name, expect_full_name", [
        (None, ""),
        ("Default/make_tuple[9]_3/make_tuple-op284", "Default/make_tuple-op284"),
        ("Default/args0", "Default/args0")
    ])
    def test_get_full_name(self, node_name, expect_full_name):
        """Test get full name."""
        full_name = self.graph_handler.get_full_name(node_name)
        assert full_name == expect_full_name

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("full_name, expect_node_name", [
        (None, ""),
        ("Default/make_tuple-op284", "Default/make_tuple[9]_3/make_tuple-op284"),
        ("Default/args0", "Default/args0")
    ])
    def test_get_node_name_by_full_name(self, full_name, expect_node_name):
        """Test get node name by full name."""
        node_name = self.graph_handler.get_node_name_by_full_name(full_name)
        assert node_name == expect_node_name

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("node_name, ascend, expect_next", [
        (None, True, "Default/network-WithLossCell/_loss_fn-SoftmaxCrossEntropyWithLogits/OneHot-op0"),
        (None, False, None),
        ("Default/tuple_getitem[10]_0/tuple_getitem-op206", True,
         "Default/network-WithLossCell/_backbone-LeNet5/relu-ReLU/ReLUV2-op89"),
        ("Default/tuple_getitem[10]_0/tuple_getitem-op206", False,
         "Default/network-WithLossCell/_backbone-LeNet5/max_pool2d-MaxPool2d/Cast-op205")
    ])
    def test_get_node_by_bfs_order(self, node_name, ascend, expect_next):
        """Test get node by BFS order."""
        next_node = self.graph_handler.get_node_by_bfs_order(node_name, ascend)
        assert next_node == expect_next
