# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Common explain data encapsulator base class."""

import copy

from mindinsight.utils.exceptions import ParamValueError


def _sort_key_min_confidence(sample, labels):
    """Samples sort key by the min. confidence."""
    min_confidence = float("+inf")
    for inference in sample["inferences"]:
        if labels and inference["label"] not in labels:
            continue
        if inference["confidence"] < min_confidence:
            min_confidence = inference["confidence"]
    return min_confidence


def _sort_key_max_confidence(sample, labels):
    """Samples sort key by the max. confidence."""
    max_confidence = float("-inf")
    for inference in sample["inferences"]:
        if labels and inference["label"] not in labels:
            continue
        if inference["confidence"] > max_confidence:
            max_confidence = inference["confidence"]
    return max_confidence


def _sort_key_min_confidence_sd(sample, labels):
    """Samples sort key by the min. confidence_sd."""
    min_confidence_sd = float("+inf")
    for inference in sample["inferences"]:
        if labels and inference["label"] not in labels:
            continue
        confidence_sd = inference.get("confidence_sd", float("+inf"))
        if confidence_sd < min_confidence_sd:
            min_confidence_sd = confidence_sd
    return min_confidence_sd


def _sort_key_max_confidence_sd(sample, labels):
    """Samples sort key by the max. confidence_sd."""
    max_confidence_sd = float("-inf")
    for inference in sample["inferences"]:
        if labels and inference["label"] not in labels:
            continue
        confidence_sd = inference.get("confidence_sd", float("-inf"))
        if confidence_sd > max_confidence_sd:
            max_confidence_sd = confidence_sd
    return max_confidence_sd


class ExplainDataEncap:
    """Explain data encapsulator base class."""

    def __init__(self, job_manager):
        self._job_manager = job_manager

    @property
    def job_manager(self):
        return self._job_manager


class ExplanationEncap(ExplainDataEncap):
    """Base encapsulator for explanation queries."""

    def __init__(self, image_url_formatter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_url_formatter = image_url_formatter

    def _query_samples(self,
                       job,
                       labels,
                       sorted_name,
                       sorted_type,
                       prediction_types=None,
                       query_type="saliency_maps"):
        """
        Query samples.

        Args:
            job (ExplainManager): Explain job to be query from.
            labels (list[str]): Label filter.
            sorted_name (str): Field to be sorted.
            sorted_type (str): Sorting order, 'ascending' or 'descending'.
            prediction_types (list[str]): Prediction type filter.

        Returns:
             list[dict], samples to be queried.
        """

        samples = copy.deepcopy(job.get_all_samples())
        samples = [sample for sample in samples if any(infer[query_type] for infer in sample['inferences'])]
        if labels:
            filtered = []
            for sample in samples:
                infer_labels = [inference["label"] for inference in sample["inferences"]]
                for infer_label in infer_labels:
                    if infer_label in labels:
                        filtered.append(sample)
                        break
            samples = filtered

        if prediction_types and len(prediction_types) < 3:
            filtered = []
            for sample in samples:
                infer_types = [inference["prediction_type"] for inference in sample["inferences"]]
                for infer_type in infer_types:
                    if infer_type in prediction_types:
                        filtered.append(sample)
                        break
            samples = filtered

        reverse = sorted_type == "descending"
        if sorted_name == "confidence":
            if reverse:
                samples.sort(key=lambda x: _sort_key_max_confidence(x, labels), reverse=reverse)
            else:
                samples.sort(key=lambda x: _sort_key_min_confidence(x, labels), reverse=reverse)
        elif sorted_name == "uncertainty":
            if not job.uncertainty_enabled:
                raise ParamValueError("Uncertainty is not enabled, sorted_name cannot be 'uncertainty'")
            if reverse:
                samples.sort(key=lambda x: _sort_key_max_confidence_sd(x, labels), reverse=reverse)
            else:
                samples.sort(key=lambda x: _sort_key_min_confidence_sd(x, labels), reverse=reverse)
        elif sorted_name != "":
            raise ParamValueError("sorted_name")
        return samples

    def _get_image_url(self, train_id, image_path, image_type):
        """Returns image's url."""
        if self._image_url_formatter is None:
            return image_path
        return self._image_url_formatter(train_id, image_path, image_type)
