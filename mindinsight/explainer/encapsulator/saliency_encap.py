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
"""Saliency map encapsulator."""

import copy

from mindinsight.utils.exceptions import ParamValueError
from mindinsight.explainer.encapsulator.explain_data_encap import ExplainDataEncap
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError


def _sort_key_min_confidence(sample):
    """Samples sort key by the min. confidence."""
    min_confidence = float("+inf")
    for inference in sample["inferences"]:
        if inference["confidence"] < min_confidence:
            min_confidence = inference["confidence"]
    return min_confidence


def _sort_key_max_confidence(sample):
    """Samples sort key by the max. confidence."""
    max_confidence = float("-inf")
    for inference in sample["inferences"]:
        if inference["confidence"] > max_confidence:
            max_confidence = inference["confidence"]
    return max_confidence


def _sort_key_min_confidence_sd(sample):
    """Samples sort key by the min. confidence_sd."""
    min_confidence_sd = float("+inf")
    for inference in sample["inferences"]:
        confidence_sd = inference.get("confidence_sd", float("+inf"))
        if confidence_sd < min_confidence_sd:
            min_confidence_sd = confidence_sd
    return min_confidence_sd


def _sort_key_max_confidence_sd(sample):
    """Samples sort key by the max. confidence_sd."""
    max_confidence_sd = float("-inf")
    for inference in sample["inferences"]:
        confidence_sd = inference.get("confidence_sd", float("-inf"))
        if confidence_sd > max_confidence_sd:
            max_confidence_sd = confidence_sd
    return max_confidence_sd


class SaliencyEncap(ExplainDataEncap):
    """Saliency map encapsulator."""

    def __init__(self, image_url_formatter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._image_url_formatter = image_url_formatter

    def query_saliency_maps(self,
                            train_id,
                            labels,
                            explainers,
                            limit,
                            offset,
                            sorted_name,
                            sorted_type):
        """
        Query saliency maps.
        Args:
            train_id (str): Job ID.
            labels (list[str]): Label filter.
            explainers (list[str]): Explainers of saliency maps to be shown.
            limit (int): Max. no. of items to be returned.
            offset (int): Page offset.
            sorted_name (str): Field to be sorted.
            sorted_type (str): Sorting order, 'ascending' or 'descending'.

        Returns:
            tuple[int, list[dict]], total no. of samples after filtering and
                list of sample result.
        """
        job = self.job_manager.get_job(train_id)
        if job is None:
            raise TrainJobNotExistError(train_id)

        samples = copy.deepcopy(job.get_all_samples())
        if labels:
            filtered = []
            for sample in samples:
                infer_labels = [inference["label"] for inference in sample["inferences"]]
                for infer_label in infer_labels:
                    if infer_label in labels:
                        filtered.append(sample)
                        break
            samples = filtered

        reverse = sorted_type == "descending"
        if sorted_name == "confidence":
            if reverse:
                samples.sort(key=_sort_key_max_confidence, reverse=reverse)
            else:
                samples.sort(key=_sort_key_min_confidence, reverse=reverse)
        elif sorted_name == "uncertainty":
            if not job.uncertainty_enabled:
                raise ParamValueError("Uncertainty is not enabled, sorted_name cannot be 'uncertainty'")
            if reverse:
                samples.sort(key=_sort_key_max_confidence_sd, reverse=reverse)
            else:
                samples.sort(key=_sort_key_min_confidence_sd, reverse=reverse)
        elif sorted_name != "":
            raise ParamValueError("sorted_name")

        sample_infos = []
        obj_offset = offset*limit
        count = len(samples)
        end = count
        if obj_offset + limit < end:
            end = obj_offset + limit
        for i in range(obj_offset, end):
            sample = samples[i]
            sample_infos.append(self._touch_sample(sample, job, explainers))

        return count, sample_infos

    def _touch_sample(self, sample, job, explainers):
        """
        Final editing the sample info.
        Args:
            sample (dict): Sample info.
            job (ExplainJob): Explain job.
            explainers (list[str]): Explainer names.
        Returns:
            dict, the edited sample info.
        """
        sample["image"] = self._get_image_url(job.train_id, sample['image'], "original")
        for inference in sample["inferences"]:
            new_list = []
            for saliency_map in inference["saliency_maps"]:
                if explainers and saliency_map["explainer"] not in explainers:
                    continue
                saliency_map["overlay"] = self._get_image_url(job.train_id, saliency_map['overlay'], "overlay")
                new_list.append(saliency_map)
            inference["saliency_maps"] = new_list
        return sample

    def _get_image_url(self, train_id, image_path, image_type):
        """Returns image's url."""
        if self._image_url_formatter is None:
            return image_path
        return self._image_url_formatter(train_id, image_path, image_type)
