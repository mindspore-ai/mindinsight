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
"""
Function:
    Test train task manager.
Usage:
    pytest tests/ut/datavisual
"""
import tempfile
import time
from unittest.mock import Mock

import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.processors.train_task_manager import TrainTaskManager
from mindinsight.datavisual.utils import crc32

from ....utils.log_operations import LogOperations
from ....utils.tools import check_loading_done, delete_files_or_dirs
from ..mock import MockLogger


class TestTrainTaskManager:
    """Test train task manager."""
    _root_dir = None

    _dir_num = 3
    _plugins_id_map = {'image': [], 'scalar': [], 'graph': []}
    _events_names = []
    _steps_list = [1, 3, 5]
    _steps = len(_steps_list)

    _tag_name = 'tag_name'

    _mock_data_manager = None

    _train_id_list = []

    _generated_path = []

    @classmethod
    def setup_class(cls):
        """
        Mock common environment for train task unittest.
        """
        crc32.CheckValueAgainstData = Mock(return_value=True)
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    @pytest.fixture(scope='function')
    def load_data(self):
        """Load data."""
        log_operation = LogOperations()
        self._plugins_id_map = {'image': [], 'scalar': [], 'graph': [], 'histogram': [], 'tensor': []}
        self._events_names = []
        self._train_id_list = []

        self._root_dir = tempfile.mkdtemp()
        for i in range(self._dir_num):
            dir_path = tempfile.mkdtemp(dir=self._root_dir)
            tmp_tag_name = self._tag_name + '_' + str(i)
            event_name = str(i) + "_name"
            train_id = dir_path.replace(self._root_dir, ".")

            # Pass timestamp to write to the same file.
            log_settings = dict(steps=self._steps_list, tag=tmp_tag_name, time=time.time())
            if i % 3 != 0:
                log_operation.generate_log(PluginNameEnum.IMAGE.value, dir_path, log_settings)
                self._plugins_id_map['image'].append(train_id)
            if i % 3 != 1:
                log_operation.generate_log(PluginNameEnum.SCALAR.value, dir_path, log_settings)
                self._plugins_id_map['scalar'].append(train_id)
            if i % 3 != 2:
                log_operation.generate_log(PluginNameEnum.GRAPH.value, dir_path, log_settings)
                self._plugins_id_map['graph'].append(train_id)
            self._events_names.append(event_name)
            self._train_id_list.append(train_id)

        self._generated_path.append(self._root_dir)

        self._mock_data_manager = data_manager.DataManager(self._root_dir)
        self._mock_data_manager.start_load_data(reload_interval=0)

        check_loading_done(self._mock_data_manager, time_limit=30)

    @pytest.mark.usefixtures('load_data')
    def test_get_single_train_task_with_not_exists_train_id(self):
        """Test getting single train task with not exists train_id."""
        train_task_manager = TrainTaskManager(self._mock_data_manager)
        for plugin_name in PluginNameEnum.list_members():
            test_train_id = "not_exist_id"
            with pytest.raises(TrainJobNotExistError) as exc_info:
                _ = train_task_manager.get_single_train_task(plugin_name, test_train_id)
            assert exc_info.value.message == "Train job is not exist. " \
                                             "Detail: Can not find the train job in data manager."
            assert exc_info.value.error_code == '50545005'

    @pytest.mark.usefixtures('load_data')
    def test_get_single_train_task_with_params(self):
        """Test getting single train task with params."""
        train_task_manager = TrainTaskManager(self._mock_data_manager)
        for plugin_name in PluginNameEnum.list_members():
            for test_train_id in self._train_id_list:
                result = train_task_manager.get_single_train_task(plugin_name, test_train_id)
                tags = result.get("train_jobs")[0].get("tags")

                # if it is a UUID
                if tags:
                    assert test_train_id in self._plugins_id_map.get(plugin_name)
                else:
                    assert test_train_id not in self._plugins_id_map.get(plugin_name)

    @pytest.mark.usefixtures('load_data')
    def test_get_plugins_with_train_id(self):
        """Test getting plugins with train id."""
        train_task_manager = TrainTaskManager(self._mock_data_manager)

        for train_id in self._train_id_list:
            result = train_task_manager.get_plugins(train_id)
            plugins = result.get('plugins')
            for plugin_name in plugins:
                if plugins.get(plugin_name):
                    assert train_id in self._plugins_id_map.get(plugin_name)
                else:
                    assert train_id not in self._plugins_id_map.get(plugin_name)

    @pytest.mark.usefixtures('load_data')
    def test_cache_train_jobs(self):
        """Test caching train jobs with train ids."""
        train_task_manager = TrainTaskManager(self._mock_data_manager)

        cache_result = train_task_manager.cache_train_jobs(self._train_id_list)
        assert len(self._train_id_list) == len(cache_result)
