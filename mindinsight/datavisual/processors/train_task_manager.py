# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Train task manager."""

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.enums import CacheStatus
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.processors.base_processor import BaseProcessor
from mindinsight.datavisual.data_transform.data_manager import DATAVISUAL_PLUGIN_KEY, DATAVISUAL_CACHE_KEY


class TrainTaskManager(BaseProcessor):
    """Train task manager."""

    def get_single_train_task(self, plugin_name, train_id):
        """
        get single train task.

        Args:
            plugin_name (str): Plugin name, refer `PluginNameEnum`.
            train_id (str): Specify a training job to query.

        Returns:
            {'train_jobs': list[TrainJob]}, refer to restful api.
        """
        Validation.check_param_empty(plugin_name=plugin_name, train_id=train_id)
        Validation.check_plugin_name(plugin_name=plugin_name)
        train_job = self._data_manager.get_train_job_by_plugin(train_id=train_id, plugin_name=plugin_name)
        if train_job is None:
            raise exceptions.TrainJobNotExistError()
        return dict(train_jobs=[train_job])

    def get_plugins(self, train_id, manual_update=True):
        """
        Queries the plug-in data for the specified training job

        Args:
            train_id (str): Specify a training job to query.
            manual_update (bool): Specifies whether to refresh automatically.

        Returns:
            dict, refer to restful api.
        """
        Validation.check_param_empty(train_id=train_id)

        if manual_update:
            self._data_manager.cache_train_job(train_id)

        train_job = self._data_manager.get_train_job(train_id)

        try:
            data_visual_content = train_job.get_detail(DATAVISUAL_CACHE_KEY)
            plugins = data_visual_content.get(DATAVISUAL_PLUGIN_KEY)
        except exceptions.TrainJobDetailNotInCacheError:
            plugins = []

        if not plugins:
            default_result = dict()
            for plugin_name in PluginNameEnum.list_members():
                default_result.update({plugin_name: list()})
            return dict(plugins=default_result)

        return dict(
            plugins=plugins
        )

    def query_train_jobs(self, offset=0, limit=10):
        """
        Query train jobs.

        Args:
            offset (int): Specify page number. Default is 0.
            limit (int): Specify page size. Default is 10.

        Returns:
            tuple, return quantity of total train jobs and list of train jobs specified by offset and limit.
        """
        brief_cache = self._data_manager.get_brief_cache()
        brief_train_jobs = list(brief_cache.get_train_jobs().values())
        brief_train_jobs.sort(key=lambda x: x.basic_info.update_time, reverse=True)
        total = len(brief_train_jobs)

        start = offset * limit
        end = (offset + 1) * limit
        train_jobs = []

        train_ids = [train_job.basic_info.train_id for train_job in brief_train_jobs[start:end]]

        for train_id in train_ids:
            try:
                train_job = self._data_manager.get_train_job(train_id)
            except exceptions.TrainJobNotExistError:
                logger.warning('Train job %s not existed', train_id)
                continue

            basic_info = train_job.get_basic_info()
            train_job_item = dict(
                train_id=basic_info.train_id,
                relative_path=basic_info.train_id,
                create_time=basic_info.create_time.strftime('%Y-%m-%d %H:%M:%S'),
                update_time=basic_info.update_time.strftime('%Y-%m-%d %H:%M:%S'),
                profiler_dir=basic_info.profiler_dir,
                cache_status=train_job.cache_status.value,
            )

            if train_job.cache_status == CacheStatus.CACHED:
                plugins = self.get_plugins(train_id)
            else:
                plugins = dict(plugins={
                    'graph': [],
                    'scalar': [],
                    'image': [],
                    'histogram': [],
                })

            train_job_item.update(plugins)
            train_jobs.append(train_job_item)

        return total, train_jobs

    def cache_train_jobs(self, train_ids):
        """
        Cache train jobs.

        Args:
            train_ids (list): Specify list of train_ids to be cached.

        Returns:
            dict, indicates train job ID and its current cache status.
        """
        cache_result = []
        for train_id in train_ids:
            try:
                train_job = self._data_manager.get_train_job(train_id)
            except exceptions.TrainJobNotExistError:
                logger.warning('Train job %s not existed', train_id)
                continue

            if train_job.cache_status == CacheStatus.NOT_IN_CACHE:
                self._data_manager.cache_train_job(train_id)
                # Update loader cache status to CACHING for consistency in response.
                train_job.cache_status = CacheStatus.CACHING

            cache_result.append(dict(
                train_id=train_id,
                cache_status=train_job.cache_status.value,
            ))

        return cache_result
