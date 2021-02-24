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
"""Explain job list encapsulator."""

from datetime import datetime

from mindinsight.explainer.encapsulator.explain_data_encap import ExplainDataEncap
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError


class ExplainJobEncap(ExplainDataEncap):
    """Explain job list encapsulator."""

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DEFAULT_MIN_CONFIDENCE = 0.5

    def query_explain_jobs(self, offset, limit):
        """
        Query explain job list.

        Args:
            offset (int): Page offset.
            limit (int): Maximum number of items to be returned.

        Returns:
            tuple[int, list[Dict]], total number of jobs and job list.
        """
        total, dir_infos = self.job_manager.get_job_list(offset=offset, limit=limit)
        job_infos = [self._dir_2_info(dir_info) for dir_info in dir_infos]

        return total, job_infos

    def query_meta(self, train_id):
        """
        Query explain job meta-data.

        Args:
            train_id (str): Job ID.

        Returns:
            dict, the metadata.
        """
        job = self.job_manager.get_job(train_id)
        if job is None:
            raise TrainJobNotExistError(train_id)
        return self._job_2_meta(job)

    @classmethod
    def _dir_2_info(cls, dir_info):
        """Convert ExplainJob object to jsonable info object."""
        info = dict()
        info["train_id"] = dir_info["relative_path"]
        info["create_time"] = dir_info["create_time"].strftime(cls.DATETIME_FORMAT)
        info["update_time"] = dir_info["update_time"].strftime(cls.DATETIME_FORMAT)
        info["saliency_map"] = dir_info["saliency_map"]
        info["hierarchical_occlusion"] = dir_info["hierarchical_occlusion"]

        return info

    @classmethod
    def _job_2_info(cls, job):
        """Convert ExplainJob object to jsonable info object."""
        info = dict()
        info["train_id"] = job.train_id
        info["create_time"] = datetime.fromtimestamp(job.create_time)\
            .strftime(cls.DATETIME_FORMAT)
        info["update_time"] = datetime.fromtimestamp(job.update_time)\
            .strftime(cls.DATETIME_FORMAT)
        return info

    @classmethod
    def _job_2_meta(cls, job):
        """Convert ExplainJob's meta-data to jsonable info object."""
        info = cls._job_2_info(job)
        info["sample_count"] = job.sample_count
        info["classes"] = job.all_classes
        saliency_info = dict()
        if job.min_confidence is None:
            saliency_info["min_confidence"] = cls.DEFAULT_MIN_CONFIDENCE
        else:
            saliency_info["min_confidence"] = job.min_confidence
        saliency_info["explainers"] = list(job.explainers)
        saliency_info["metrics"] = list(job.metrics)
        info["saliency"] = saliency_info
        info["uncertainty"] = {"enabled": job.uncertainty_enabled}
        info["status"] = job.status
        return info
