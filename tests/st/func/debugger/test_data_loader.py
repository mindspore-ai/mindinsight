# Copyright 2021-2022 Huawei Technologies Co., Ltd
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

from mindinsight.debugger.common.exceptions.exceptions import DebuggerNodeTooLarge
from mindinsight.debugger.stream_cache.data_loader import DataLoader
from tests.st.func.debugger.conftest import GRAPH_PROTO_FILE
from tests.st.func.debugger.utils import build_dump_file_structure, build_multi_net_dump_structure
from tests.utils.tools import compare_result_with_file, compare_result_with_binary_file


class TestDataLoader:
    """Test DataLoader."""

    @classmethod
    def setup_class(cls):
        """Init TestDataLoader for DataLoader unittest."""
        cls.debugger_tmp_dir = build_dump_file_structure()
        cls.expected_results_dir = os.path.join(os.path.dirname(__file__),
                                                'expect_results/offline_debugger')
        cls.dump_files_dir_ascend = os.path.join(cls.debugger_tmp_dir,
                                                 'Ascend/sync')
        cls.data_loader_ascend = DataLoader(cls.dump_files_dir_ascend)
        cls.dump_files_dir_gpu = os.path.join(cls.debugger_tmp_dir,
                                              'GPU/sync')
        cls.data_loader_gpu = DataLoader(cls.dump_files_dir_gpu)
        cls.dump_files_dir_ascend_async = os.path.join(cls.debugger_tmp_dir,
                                                       'Ascend/async')
        cls.data_loader_ascend_async = DataLoader(cls.dump_files_dir_ascend_async)

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.level0
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
    def test_load_graphs_ascend_except(self):
        """Test load_graphs function of offline-debugger when node too large."""
        with pytest.raises(DebuggerNodeTooLarge) as exc_info:
            self.data_loader_ascend.load_graphs(321)
        assert "Node limit: 321, current node num: 322." in exc_info.value.message

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
        res = self.data_loader_ascend.load_dumped_step()
        expected_result = {0: {0: [0, 1, 2, 3]}, 1: {0: [0, 1, 2, 3]}}
        self._compare_dumped_steps(res, expected_result)

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
        res = self.data_loader_gpu.load_dumped_step()
        expected_result = {0: {0: [0, 1, 2]}, 1: {0: [0, 1, 2]}}
        self._compare_dumped_steps(res, expected_result)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_load_step_num_ascend_async(self):
        """Test load_step_num of ascend chip for offline-debugger."""
        res = self.data_loader_ascend_async.load_dumped_step()
        expected_result = {0: {1: [0, 1, 2]}, 1: {1: [0, 1, 2]}}
        self._compare_dumped_steps(res, expected_result)

    @staticmethod
    def _compare_dumped_steps(actual_res, expect_res):
        """Compare dumped steps."""
        convert_res = {}
        for key, value in actual_res.items():
            convert_res[key] = {}
            for graph_id, step_ids in value.items():
                convert_res[key][graph_id] = list(step_ids)
                convert_res[key][graph_id].sort()
        assert convert_res == expect_res


class TestMultiNetDataLoader:
    """Test MultiNet DataLoader."""

    @classmethod
    def setup_class(cls):
        """Init TestDataLoader for DataLoader unittest."""
        cls.debugger_tmp_dir = build_multi_net_dump_structure()
        cls.data_loader = DataLoader(cls.debugger_tmp_dir)

    @classmethod
    def teardown_class(cls):
        """Run after test this class."""
        if os.path.exists(cls.debugger_tmp_dir):
            shutil.rmtree(cls.debugger_tmp_dir)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_graph_history(self):
        """Test load graph history."""
        res = self.data_loader.load_graph_history()
        expect = {0: {0: {0, 2, 4}, 3: {1, 3, 5, 6}},
                  1: {0: {0, 2, 4}, 3: {1, 3, 5, 6}}}
        assert res == expect

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.parametrize("step, rank, result", [
        (0, None, True),
        (1, 0, True),
        (7, 1, False),
    ])
    def test_has_data(self, step, rank, result):
        """Test has data in specific step."""
        res = self.data_loader.has_data(step, rank)
        assert res == result
