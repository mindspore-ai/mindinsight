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
"""Explain job list encapsulator."""

import copy
from datetime import datetime

from mindinsight.utils.exceptions import ParamValueError
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.explainer.encapsulator.explain_data_encap import ExplainDataEncap


class ExplainJobEncap(ExplainDataEncap):
    """Explain job list encapsulator."""

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def query_explain_jobs(self, offset, limit, train_id):
        """
        Query explain job list.
        Args:
            offset (int): offset
            limit (int): max. no. of items to be returned
            train_id (str): job id
        Returns:
            Tuple[int, List[Dict]], total no. of jobs and job list
        """
        watcher = SummaryWatcher()
        total, dir_infos = \
            watcher.list_explain_directories(self.job_manager.summary_base_dir,
                                             offset=offset, limit=limit)
        obj_offset = offset * limit
        job_infos = []

        if train_id is None:
            end = total
            if obj_offset + limit < end:
                end = obj_offset + limit

            for i in range(obj_offset, end):
                job_id = dir_infos[i]["relative_path"]
                job = self.job_manager.get_job(job_id)
                if job is not None:
                    job_infos.append(self._job_2_info(job))
        else:
            job = self.job_manager.get_job(train_id)
            if job is not None:
                job_infos.append(self._job_2_info(job))

        return total, job_infos

    def query_meta(self, train_id):
        """
        Query explain job meta-data
        Args:
            train_id (str): job id
        Returns:
            Dict, the metadata
        """
        job = self.job_manager.get_job(train_id)
        if job is None:
            return None
        return self._job_2_meta(job)

    def query_image_binary(self, train_id, image_id, image_type):
        """
        Query image binary content.
        Args:
            train_id (str): job id
            image_id (str): image id
            image_type (str) 'original' or 'overlay'
        Returns:
            bytes, image binary
        """
        job = self.job_manager.get_job(train_id)

        if job is None:
            return None
        if image_type == "original":
            binary = job.retrieve_image(image_id)
        elif image_type == "overlay":
            binary = job.retrieve_overlay(image_id)
        else:
            raise ParamValueError(f"image_type:{image_type}")

        return binary

    @classmethod
    def _job_2_info(cls, job):
        """Convert ExplainJob object to jsonable info object"""
        info = dict()
        info["train_id"] = job.train_id
        info["create_time"] = datetime.fromtimestamp(job.create_time)\
            .strftime(cls.DATETIME_FORMAT)
        info["update_time"] = datetime.fromtimestamp(job.latest_update_time)\
            .strftime(cls.DATETIME_FORMAT)
        return info

    @classmethod
    def _job_2_meta(cls, job):
        """Convert ExplainJob's meta-data to jsonable info object"""
        info = cls._job_2_info(job)
        info["sample_count"] = job.sample_count
        info["classes"] = copy.deepcopy(job.all_classes)
        saliency_info = dict()
        if job.min_confidence is None:
            saliency_info["min_confidence"] = 0.5
        else:
            saliency_info["min_confidence"] = job.min_confidence
        saliency_info["explainers"] = list(job.explainers)
        saliency_info["metrics"] = list(job.metrics)
        info["saliency"] = saliency_info
        info["uncertainty"] = {"enabled": False}
        return info
