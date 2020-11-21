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
"""Test the module of explainer.explain_job_encap."""

from mindinsight.explainer.encapsulator.explain_job_encap import ExplainJobEncap
from .mock_explain_manager import MockExplainManager


class TestExplainJobEncap:
    """Test case of ExplainJobEncap."""
    def setup(self):
        """Setup the test case."""
        self.encapsulator = ExplainJobEncap(MockExplainManager())

    def test_query_explain_jobs(self):
        """Test query the explain job list."""
        job_list = self.encapsulator.query_explain_jobs(offset=0, limit=10)
        expected_result = (1, [
            {
                "train_id": "./mock_job_1",
                "create_time": "2020-10-01 20:21:23",
                "update_time": "2020-10-01 20:21:23"
            }
        ])
        assert job_list == expected_result

    def test_query_meta(self):
        """Test query a explain job's meta-data."""
        job = self.encapsulator.query_meta("./mock_job_1")
        assert job is not None
        assert job["train_id"] == "./mock_job_1"
