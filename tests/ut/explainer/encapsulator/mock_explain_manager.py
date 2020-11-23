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
"""Mock ExplainManager and ExplainJob classes for UT."""
from datetime import datetime

from mindinsight.explainer.encapsulator.explain_job_encap import ExplainJobEncap


class MockExplainJob:
    """Mock ExplainJob."""
    def __init__(self, train_id):
        self.train_id = train_id
        self.create_time = datetime.timestamp(
            datetime.strptime("2020-10-01 20:21:23",
                              ExplainJobEncap.DATETIME_FORMAT))
        self.update_time = self.create_time
        self.sample_count = 1999
        self.min_confidence = 0.5
        self.explainers = ["Gradient"]
        self.metrics = ["Localization"]
        self.uncertainty_enabled = False
        self.all_classes = [
            {
                "id": 0,
                "label": "car",
                "sample_count": 1999
            }
        ]
        self.explainer_scores = [
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

    def retrieve_image(self, image_id):
        """Get original image binary."""
        if image_id == "1":
            return b'123'
        return None

    def retrieve_overlay(self, image_id):
        """Get overlay image binary."""
        if image_id == "4":
            return b'456'
        return None

    def get_all_samples(self):
        """Get all mock samples."""
        sample = {
            "id": "123",
            "name": "123",
            "image": "123",
            "labels": ["car"],
            "inferences": [
                {
                    "label": "car",
                    "confidence": 0.75,
                    "saliency_maps": [
                        {
                            "explainer": "Gradient",
                            "overlay": "4"
                        }
                    ]
                }
            ]
        }
        return [sample]


class MockExplainManager:
    """Mock ExplainManger."""
    def get_job_list(self, offset, limit):
        """Get all mock jobs."""
        del offset, limit
        job_list = [
            {
                "relative_path": "./mock_job_1",
                "create_time": datetime.strptime("2020-10-01 20:21:23", ExplainJobEncap.DATETIME_FORMAT),
                "update_time": datetime.strptime("2020-10-01 20:21:23", ExplainJobEncap.DATETIME_FORMAT)
            }
        ]
        return 1, job_list

    def get_job(self, train_id):
        """Get a mock job."""
        if train_id == "./mock_job_1":
            return MockExplainJob(train_id)
        return None
