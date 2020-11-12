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
"""Test the module of backend/explainer/explainer_api."""
import json

from unittest.mock import patch

from mindinsight.explainer.encapsulator.explain_job_encap import ExplainJobEncap
from mindinsight.explainer.encapsulator.saliency_encap import SaliencyEncap
from mindinsight.explainer.encapsulator.evaluation_encap import EvaluationEncap
from mindinsight.explainer.encapsulator.datafile_encap import DatafileEncap
from .conftest import EXPLAINER_ROUTES


class TestExplainerApi:
    """Test the restful api of search_model."""

    @patch("mindinsight.backend.explainer.explainer_api.settings")
    @patch.object(ExplainJobEncap, "query_explain_jobs")
    def test_query_explain_jobs(self, mock_query_explain_jobs, mock_settings, client):
        """Test query all explain jobs information in the SUMMARY_BASE_DIR."""
        mock_settings.SUMMARY_BASE_DIR = "mock_base_dir"

        job_list = [
            {
                "train_id": "./mock_job_1",
                "create_time": "2020-10-01 20:21:23",
                "update_time": "2020-10-01 20:21:23",
            },
            {
                "train_id": "./mock_job_2",
                "create_time": "2020-10-02 20:21:23",
                "update_time": "2020-10-02 20:21:23",
            }
        ]

        mock_query_explain_jobs.return_value = (2, job_list)

        response = client.get(f"{EXPLAINER_ROUTES['explain_jobs']}?limit=10&offset=0")
        assert response.status_code == 200

        expect_result = {
            "name": mock_settings.SUMMARY_BASE_DIR,
            "total": 2,
            "explain_jobs": job_list
        }

        assert response.get_json() == expect_result

    @patch.object(ExplainJobEncap, "query_meta")
    def test_query_explain_job(self, mock_query_meta, client):
        """Test query a explain jobs' meta-data."""

        job_meta = {
            "train_id": "./mock_job_1",
            "create_time": "2020-10-01 20:21:23",
            "update_time": "2020-10-01 20:21:23",
            "sample_count": 1999,
            "classes": [
                {
                    "id": 0,
                    "label": "car",
                    "sample_count": 1000
                },
                {
                    "id": 0,
                    "label": "person",
                    "sample_count": 999
                }
            ],
            "saliency": {
                "min_confidence": 0.5,
                "explainers": ["Gradient", "GradCAM"],
                "metrics": ["Localization", "ClassSensitivity"]
            },
            "uncertainty": {
                "enabled": False
            }
        }

        mock_query_meta.return_value = job_meta

        response = client.get(f"{EXPLAINER_ROUTES['job_metadata']}?train_id=.%2Fmock_job_1")
        assert response.status_code == 200

        expect_result = job_meta

        assert response.get_json() == expect_result

    @patch.object(SaliencyEncap, "query_saliency_maps")
    def test_query_saliency_maps(self, mock_query_saliency_maps, client):
        """Test query saliency map results."""

        samples = [
            {
                "name": "sample_1",
                "labels": "car",
                "image": "/image",
                "inferences": [
                    {
                        "label": "car",
                        "confidence": 0.85,
                        "saliency_maps": [
                            {
                                "explainer": "Gradient",
                                "overlay": "/overlay"
                            },
                            {
                                "explainer": "GradCAM",
                                "overlay": "/overlay"
                            },
                        ]
                    }
                ]
            }
        ]

        mock_query_saliency_maps.return_value = (1999, samples)

        body_data = {
            "train_id": "./mock_job_1",
            "explainers": ["Gradient", "GradCAM"],
            "offset": 0,
            "limit": 1,
            "sorted_name": "confidence",
            "sorted_type": "descending"
        }

        response = client.post(EXPLAINER_ROUTES["saliency"], data=json.dumps(body_data))
        assert response.status_code == 200

        expect_result = {
            "count": 1999,
            "samples": samples
        }

        assert response.get_json() == expect_result

    @patch.object(EvaluationEncap, "query_explainer_scores")
    def test_query_query_evaluation(self, mock_query_explainer_scores, client):
        """Test query explainers' evaluation results."""

        explainer_scores = [
            {
                "explainer": "Gradient",
                "evaluations": [
                    {
                        "metric": "Localization",
                        "score": 0.5
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
            },
        ]

        mock_query_explainer_scores.return_value = explainer_scores

        response = client.get(f"{EXPLAINER_ROUTES['evaluation']}?train_id=.%2Fmock_job_1")
        assert response.status_code == 200

        expect_result = {"explainer_scores": explainer_scores}
        assert response.get_json() == expect_result

    @patch.object(DatafileEncap, "query_image_binary")
    def test_query_image(self, mock_query_image_binary, client):
        """Test query a image's binary content."""

        mock_query_image_binary.return_value = b'123'

        response = client.get(f"{EXPLAINER_ROUTES['image']}?train_id=.%2Fmock_job_1&path=1&type=original")

        assert response.status_code == 200
        assert response.data == b'123'
