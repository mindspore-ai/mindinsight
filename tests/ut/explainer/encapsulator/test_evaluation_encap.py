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
"""Test the module of explainer.evaluation_encap."""

from mindinsight.explainer.encapsulator.evaluation_encap import EvaluationEncap
from .mock_explain_manager import MockExplainManager


class TestEvaluationEncap:
    """Test case for EvaluationEncap."""
    def setup(self):
        """Setup the test case."""
        self.encapsulator = EvaluationEncap(MockExplainManager())

    def test_query_explainer_scores(self):
        """Test query the explainer evaluation scores."""
        explainer_scores = self.encapsulator.query_explainer_scores("./mock_job_1")
        expected_result = [
            {
                "explainer": "Gradient",
                "evaluations": [
                    {
                        "metric": "Localization",
                        "Score": 0.5
                    }
                ],
                "class_scores": [
                    {
                        "label": "car",
                        "evaluations": [
                            {
                                "metric": "Localization",
                                "score": 0.5
                            }
                        ]
                    }
                ]
            }
        ]
        assert explainer_scores == expected_result
