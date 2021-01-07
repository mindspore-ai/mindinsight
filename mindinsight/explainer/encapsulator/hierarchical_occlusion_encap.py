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
"""Hierarchical Occlusion encapsulator."""

from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.explainer.encapsulator.explain_data_encap import ExplanationEncap


class HierarchicalOcclusionEncap(ExplanationEncap):
    """Hierarchical occlusion encapsulator."""

    def query_hierarchical_occlusion(self,
                                     train_id,
                                     labels,
                                     limit,
                                     offset,
                                     sorted_name,
                                     sorted_type,
                                     prediction_types=None
                                     ):
        """
        Query hierarchical occlusion results.

        Args:
            train_id (str): Job ID.
            labels (list[str]): Label filter.
            limit (int): Maximum number of items to be returned.
            offset (int): Page offset.
            sorted_name (str): Field to be sorted.
            sorted_type (str): Sorting order, 'ascending' or 'descending'.
            prediction_types (list[str]): Prediction types filter.

        Returns:
            tuple[int, list[dict]], total number of samples after filtering and list of sample results.
        """
        job = self.job_manager.get_job(train_id)
        if job is None:
            raise TrainJobNotExistError(train_id)

        samples = self._query_samples(job, labels, sorted_name, sorted_type, prediction_types,
                                      query_type="hoc_layers")
        sample_infos = []
        obj_offset = offset * limit
        count = len(samples)
        end = count
        if obj_offset + limit < end:
            end = obj_offset + limit
        for i in range(obj_offset, end):
            sample = samples[i]
            sample_infos.append(self._touch_sample(sample, job))

        return count, sample_infos

    def _touch_sample(self, sample, job):
        """
        Final edit on single sample info.

        Args:
             sample (dict): Sample info.
             job (ExplainManager): Explain job.

        Returns:
            dict, the edited sample info.
        """
        sample_cp = sample.copy()
        sample_cp["image"] = self._get_image_url(job.train_id, sample["image"], "original")
        for inference_item in sample_cp["inferences"]:
            new_list = []
            for idx, hoc_layer in enumerate(inference_item["hoc_layers"]):
                hoc_layer["outcome"] = self._get_image_url(job.train_id,
                                                           f"{sample['id']}_{inference_item['label']}_{idx}.jpg",
                                                           "outcome")
                new_list.append(hoc_layer)
            inference_item["hoc_layers"] = new_list
        return sample_cp
