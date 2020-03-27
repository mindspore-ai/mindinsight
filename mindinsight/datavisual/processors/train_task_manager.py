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

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.processors.base_processor import BaseProcessor


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
            raise exceptions.SummaryLogPathInvalid()
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
        train_job = self._data_manager.get_single_train_job(train_id, manual_update=manual_update)
        if not train_job:
            default_result = dict()
            for plugin_name in PluginNameEnum.list_members():
                default_result.update({plugin_name: list()})
            return dict(plugins=default_result)

        return dict(
            plugins=train_job['tag_mapping']
        )
