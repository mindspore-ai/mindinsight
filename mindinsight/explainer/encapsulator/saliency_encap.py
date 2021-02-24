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
"""Saliency map encapsulator."""

from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.explainer.common.enums import ExplanationKeys, ImageQueryTypes
from mindinsight.explainer.encapsulator.explain_data_encap import ExplanationEncap


class SaliencyEncap(ExplanationEncap):
    """Saliency map encapsulator."""

    def query_saliency_maps(self,
                            train_id,
                            labels,
                            explainers,
                            limit,
                            offset,
                            sorted_name,
                            sorted_type,
                            prediction_types=None):
        """
        Query saliency maps.

        Args:
            train_id (str): Job ID.
            labels (list[str]): Label filter.
            explainers (list[str]): Explainers of saliency maps to be shown.
            limit (int): Maximum number of items to be returned.
            offset (int): Page offset.
            sorted_name (str): Field to be sorted.
            sorted_type (str): Sorting order, 'ascending' or 'descending'.
            prediction_types (list[str]): Prediction types filter. Default: None.

        Returns:
            tuple[int, list[dict]], total number of samples after filtering and list of sample result.
        """
        job = self.job_manager.get_job(train_id)
        if job is None:
            raise TrainJobNotExistError(train_id)

        samples = self._query_samples(job, labels, sorted_name, sorted_type, prediction_types)

        sample_infos = []
        obj_offset = offset * limit
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
        Final edit on single sample info.

        Args:
            sample (dict): Sample info.
            job (ExplainJob): Explain job.
            explainers (list[str]): Explainer names.

        Returns:
            dict, the edited sample info.
        """
        original = ImageQueryTypes.ORIGINAL.value
        overlay = ImageQueryTypes.OVERLAY.value

        sample_cp = sample.copy()
        sample_cp["image"] = self._get_image_url(job.train_id, sample['image'], original)
        for inference in sample_cp["inferences"]:
            new_list = []
            for saliency_map in inference[ExplanationKeys.SALIENCY.value]:
                if explainers and saliency_map["explainer"] not in explainers:
                    continue
                saliency_map[overlay] = self._get_image_url(job.train_id, saliency_map[overlay], overlay)
                new_list.append(saliency_map)
            inference[ExplanationKeys.SALIENCY.value] = new_list
        return sample_cp
