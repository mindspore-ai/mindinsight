# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Test DataLoader of offline debugger."""
import os
import shutil

import pytest

from mindinsight.debugger.stream_cache.data_loader import DataLoader
from tests.st.func.debugger.conftest import GRAPH_PROTO_FILE
from tests.st.func.debugger.utils import build_dump_file_structure
from tests.utils.tools import compare_result_with_file, compare_result_with_binary_file


class TestDataLoader:
    """Test DataLoader."""

    @classmethod
    def setup_class(cls):
        """Init TestDataLoader for DataLoader unittest."""
        cls.debugger_tmp_dir, cls.dump_files_dir = build_dump_file_structure()
        cls.expected_results_dir = os.path.join(os.path.dirname(__file__),
                                                'expect_results/offline_debugger')
        cls.dump_files_dir_ascend = os.path.join(cls.dump_files_dir,
                                                 'Ascend/sync')
        cls.data_loader_ascend = DataLoader(cls.dump_files_dir_ascend)
        cls.data_loader_ascend.initialize()
        cls.dump_files_dir_gpu = os.path.join(cls.dump_files_dir,
                                              'GPU/sync')
        cls.data_loader_gpu = DataLoader(cls.dump_files_dir_gpu)
        cls.data_loader_gpu.initialize()
        cls.dump_files_dir_ascend_async = os.path.join(cls.dump_files_dir,
                                                       'Ascend/async')
        cls.data_loader_ascend_async = DataLoader(cls.dump_files_dir_ascend_async)
        cls.data_loader_ascend_async.initialize()

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.level
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_graphs_ascend(self):
        """Test load_graphs function of offline-debugger."""
        res = self.data_loader_ascend.load_graphs()
        expected_result0 = GRAPH_PROTO_FILE
        res0 = res[0]['graph_protos'][0].SerializeToString()
        compare_result_with_binary_file(res0, expected_result0)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_device_info_ascend(self):
        """Test load_device_info of ascend chip for offline-debugger."""
        res = self.data_loader_ascend.load_device_info()
        expected_result = os.path.join(self.expected_results_dir, 'load_device_info_ascend.json')
        compare_result_with_file(res, expected_result)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_step_num_ascend(self):
        """Test load_step_num of ascend chip for offline-debugger."""
        res = self.data_loader_ascend.load_step_number()
        expected_result = {0: 4, 1: 4}
        assert res == expected_result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_net_name_ascend(self):
        """Test get_net_name of ascend chip for offline-debugger."""
        res = self.data_loader_ascend.get_net_name()
        assert res == 'Lenet'

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_sync_flag(self):
        """Test get_sync_flag of ascend chip for offline-debugger."""
        res = self.data_loader_ascend.get_sync_flag()
        assert res

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_graphs_gpu(self):
        """Test load_graphs function of offline-debugger."""
        res = self.data_loader_gpu.load_graphs()
        expected_result0 = GRAPH_PROTO_FILE
        res0 = res[0]['graph_protos'][0].SerializeToString()
        compare_result_with_binary_file(res0, expected_result0)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_step_num_gpu(self):
        """Test load_step_num of ascend chip for offline-debugger."""
        res = self.data_loader_gpu.load_step_number()
        expected_result = {0: 3, 1: 3}
        assert res == expected_result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_step_num_ascend_async(self):
        """Test load_step_num of ascend chip for offline-debugger."""
        res = self.data_loader_ascend_async.load_step_number()
        expected_result = {0: 3, 1: 3}
        assert res == expected_result
