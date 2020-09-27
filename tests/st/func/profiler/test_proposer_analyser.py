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
    Test profiler to watch the performance of training.
Usage:
    pytest tests/st/func/profiler
"""
import os
import pytest

from mindinsight.profiler.proposer.compose_proposer import ComposeProposal

from .conftest import BASE_SUMMARY_DIR_RUN_2


class TestProposerAnalyser:
    """Test minddata  analyser module."""

    @classmethod
    def setup_class(cls):
        """Generate parsed files."""
        cls.summary_dir = os.path.join(BASE_SUMMARY_DIR_RUN_2, 'normal_run')
        cls.profiler = os.path.join(cls.summary_dir, 'profiler')

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_analyser_proposal(self):
        """Test the function of querying the proposals from multiple different proposers"""
        expect_result = {
            "minddata_device_queue": [1, 1, 0, 1],
            "minddata_get_next_queue": [0, 3],
            "minddata_pipeline-dataset_op": ["ImageFolderOp_3"],
            "minddata_pipeline-general": ["ImageFolderOp_3"]
        }

        step_trace_condition = {"filter_condition": {"mode": "proc",
                                                     "proc_name": "iteration_interval",
                                                     "step_id": 0}}
        options = {'step_trace': {"iter_interval": step_trace_condition}}
        proposal_type_list = ['step_trace', 'minddata', 'minddata_pipeline', 'common']
        proposal_obj = ComposeProposal(self.profiler, '1', proposal_type_list)
        proposal_info = proposal_obj.get_proposal(options)
        assert expect_result["minddata_device_queue"] == proposal_info["minddata_device_queue"]
        assert expect_result["minddata_get_next_queue"] == proposal_info["minddata_get_next_queue"]
        assert expect_result["minddata_pipeline-dataset_op"] == proposal_info["minddata_pipeline-dataset_op"]
        assert expect_result["minddata_pipeline-general"] == proposal_info["minddata_pipeline-general"]
