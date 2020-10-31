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
"""Test the module of explainer.saliency_encap."""

from mindinsight.explainer.encapsulator.saliency_encap import SaliencyEncap
from .mock_explain_manager import MockExplainManager


def _image_url_formatter(_, image_id, image_type):
    """Return image url."""
    return f"{image_type}-{image_id}"


class TestEvaluationEncap:
    """Test case for EvaluationEncap."""
    def setup(self):
        """Setup the test case."""
        self.encapsulator = SaliencyEncap(_image_url_formatter, MockExplainManager())

    def test_saliency_maps(self):
        """Test query the saliency map results."""
        saliency_maps = \
            self.encapsulator.query_saliency_maps(train_id="./mock_job_1",
                                                  labels=["car"],
                                                  explainers=["Gradient"],
                                                  limit=10,
                                                  offset=0,
                                                  sorted_name="confidence",
                                                  sorted_type="descending")
        expected_result = (1, [
            {
                "id": "123",
                "name": "123",
                "labels": ["car"],
                "image": "original-123",
                "inferences": [
                    {
                        "label": "car",
                        "confidence": 0.75,
                        "saliency_maps": [
                            {
                                "explainer": "Gradient",
                                "overlay": "overlay-4"
                            }
                        ]
                    }
                ]
            }
        ])
        assert saliency_maps == expected_result
