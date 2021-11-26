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
"""
Function:
    Test the data of parallel analyser.
Usage:
    pytest tests/st/func/profiler
"""
import os

import pytest

from mindinsight.profiler.proposer.proposer_factory import ProposerFactory
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.st.func.profiler import RAW_DATA_BASE


PARALLEL_PROPOSE_RESULT = {
    "step_interval": {
        "rank_id": 2,
        "val": 2.4318,
        "percent": 22.23
    },
    "cluster_link": [
        {
            "src_rank": 0,
            "des_rank": 1,
            "link_type": "SDMA",
            "val": 107910491.8874,
            "percent": 74.26
        }
    ],
    "parallel_strategy": {
        "pipeline_parallel_between_stage": {
            "val": 25.82,
            "threshold": 10.0
        },
        "pipeline_parallel_within_stage": {
            "val": 60.3,
            "threshold": 10.0,
            "stage": 1
        },
        "pipeline_parallel_flops": {
            "stage": 2,
            "val": 329610.3845,
            "percent": 50.94
        }
    }
}


class TestParallelProposer:
    """Test parallel propose module."""

    @classmethod
    def setup_class(cls):
        """Get parsed file path."""
        cls.profiler_dir = os.path.join(RAW_DATA_BASE, 'cluster_propose')

    def setup_method(self):
        """Create proposer."""
        proposer_type = 'parallel'
        self.proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiler_dir, 0)

        self._parallel_analyser = AnalyserFactory.instance().get_analyser(
            'parallel', self.profiler_dir, 0)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_step_interval(self):
        """Test the function of get step interval."""
        expect_result = [
            {
                "rank_id": 0,
                "step_interval": 1.57225
            },
            {
                "rank_id": 1,
                "step_interval": 1.55882
            },
            {
                "rank_id": 2,
                "step_interval": 2.4318
            },
            {
                "rank_id": 3,
                "step_interval": 2.39538
            }
        ]
        result = self._parallel_analyser.get_step_interval()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_rank_flops(self):
        """Test the function of get rank flops."""
        expect_result = [
            {
                "rank_id": 0,
                "FLOPs": 107146.763
            },
            {
                "rank_id": 1,
                "FLOPs": 107145.034
            },
            {
                "rank_id": 2,
                "FLOPs": 329608.369
            },
            {
                "rank_id": 3,
                "FLOPs": 329612.4
            }
        ]
        result = self._parallel_analyser.get_rank_flops()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_rank_flops_per_second(self):
        """Test the function of get rank flops per second."""
        expect_result = [
            {
                "rank_id": 0,
                "FLOPS": 5385.552
            },
            {
                "rank_id": 1,
                "FLOPS": 5386.261
            },
            {
                "rank_id": 2,
                "FLOPS": 4859.39
            },
            {
                "rank_id": 3,
                "FLOPS": 4897.642
            }
        ]
        result = self._parallel_analyser.get_rank_flops_per_second()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_rank_link_summary(self):
        """Test the function of get rank link summary."""
        expect_result = [
            [
                "1-0",
                "SDMA",
                2.200693333333333,
                46069.41866666666,
                188040273.54802418
            ],
            [
                "0-0",
                "SDMA",
                0.06816166666666665,
                554.9653333333334,
                275806635.05770296
            ],
            [
                "0-1",
                "SDMA",
                0.21956333333333333,
                1109.9306666666669,
                107910491.88737924
            ],
            [
                "1-1",
                "SDMA",
                2.061693333333333,
                45514.45333333334,
                356004676.4480063
            ],
            [
                "1-0",
                "SDMA",
                2.781570000000002,
                48309.248000000276,
                656740006.8032151
            ],
            [
                "0-0",
                "SDMA",
                1.997394999999999,
                62691.32799999992,
                1109248782.654752
            ],
            [
                "0-1",
                "SDMA",
                4.482249999999995,
                86845.95200000014,
                724225040.2054026
            ],
            [
                "1-1",
                "SDMA",
                0.3052400000000004,
                24154.624000000138,
                1045243926.9584681
            ]
        ]

        result = self._parallel_analyser.get_rank_link_summary()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_between_stage_communication_rate(self):
        """Test the function of get between stage communication rate."""
        expect_result = 0.2582
        result = self._parallel_analyser.get_between_stage_communication_rate()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_get_within_stage_communication_rate(self):
        """Test the function of get within stage communication rate."""
        expect_result = [
            {
                "stage_id": 1,
                "rate": 0.6029851045963494
            },
            {
                "stage_id": 2,
                "rate": 0.23437938457647858
            }
        ]
        result = self._parallel_analyser.get_within_stage_communication_rate()
        assert expect_result == result

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    def test_analyze(self):
        """Test the analyze function."""
        options = None
        propose_info = self.proposer.analyze(options)
        assert PARALLEL_PROPOSE_RESULT == propose_info
