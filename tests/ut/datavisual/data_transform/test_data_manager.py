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
    Test mindinsight.datavisual.data_transform.data_manager.
Usage:
    pytest tests/ut/datavisual
"""
import os
import shutil
import tempfile
import time
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from mindinsight.datavisual.common.enums import DataManagerStatus, PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.data_transform import data_manager, ms_data_loader
from mindinsight.datavisual.data_transform.data_loader import DataLoader
from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.datavisual.data_transform.events_data import EventsData
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import MAX_DATA_LOADER_SIZE
from mindinsight.datavisual.data_transform.loader_generators.loader_struct import LoaderStruct
from mindinsight.datavisual.data_transform.ms_data_loader import MSDataLoader
from mindinsight.utils.exceptions import ParamValueError

from ..mock import MockLogger


class TestDataManager:
    """Test data_manager."""
    _plugin_name = PluginNameEnum.IMAGE.value
    _train_id_suffix = "_test_data_manager"

    @pytest.fixture(scope="function")
    def crc_pass(self):
        """Mock the crc to pass the check."""
        ms_data_loader.crc32.CheckValueAgainstData = Mock(return_value=True)

    def _make_path_and_file_list(self, dir_name):
        """Utils function for tests."""
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        with open(os.path.join(dir_name, 'summary.001'), 'w'):
            pass

    def _make_loader_dict(self, summary_base_dir, dir_num, start_index=0):
        """Utils function for making loader dict."""
        if os.path.exists(summary_base_dir):
            shutil.rmtree(summary_base_dir)
        os.mkdir(summary_base_dir)
        loader_dict = dict()
        for i in range(dir_num):
            log_dir = os.path.join(summary_base_dir, f'job{start_index+i}')
            os.mkdir(log_dir)
            data_loader = DataLoader(log_dir)
            loader_id = log_dir.replace(summary_base_dir, ".")
            loader = LoaderStruct(loader_id=loader_id,
                                  name=loader_id,
                                  path=log_dir,
                                  latest_update_time=time.time() + i,
                                  data_loader=data_loader)
            loader_dict.update({loader_id: loader})
        return loader_dict

    def test_start_load_data_success(self):
        """Test start_load_data method success."""
        summary_base_dir = tempfile.mkdtemp()
        dir_num = 3
        train_ids = []
        for i in range(dir_num):
            log_path = os.path.join(summary_base_dir, f'dir{i}')
            self._make_path_and_file_list(log_path)
            train_ids.append(f'./dir{i}')

        data_manager.logger = MockLogger
        mock_manager = data_manager.DataManager(summary_base_dir)
        mock_manager.start_load_data().join()

        assert MockLogger.log_msg['info'] == "Load brief data end, and loader pool size is '3'."
        shutil.rmtree(summary_base_dir)

    def test_list_tensors_success(self):
        """Test list_tensors method success."""
        summary_base_dir = tempfile.mkdtemp()
        train_job_01 = 'train_01'
        name_01 = 'train_job_01'
        log_path_01 = os.path.join(summary_base_dir, 'dir1')
        self._make_path_and_file_list(log_path_01)
        modify_time_01 = 1575460551.9777446
        loader_01 = DataLoader(log_path_01)

        ms_loader = MSDataLoader(log_path_01)
        event_data = EventsData()
        mock_obj = mock.MagicMock()
        mock_obj.samples.return_value = {'test result'}
        tag = 'image'
        event_data._reservoir_by_tag = {tag: mock_obj}
        ms_loader._events_data = event_data
        loader_01._loader = ms_loader

        loader = LoaderStruct(loader_id=train_job_01,
                              name=name_01,
                              path=log_path_01,
                              latest_update_time=modify_time_01,
                              data_loader=loader_01)
        loader_pool = {train_job_01: loader}
        d_manager = DataManager(summary_base_dir)
        d_manager._status = DataManagerStatus.LOADING.value
        d_manager._detail_cache._loader_pool = loader_pool

        res = d_manager.list_tensors(train_job_01, tag)
        assert res == {'test result'}

        shutil.rmtree(summary_base_dir)

    def test_list_tensors_with_keyerror(self):
        """Test list_tensors method with parameter tag raises keyerror."""
        summary_base_dir = tempfile.mkdtemp()
        train_job_01 = 'train_01'
        name_01 = 'train_job_01'
        log_path_01 = os.path.join(summary_base_dir, 'dir1')
        self._make_path_and_file_list(log_path_01)
        modify_time_01 = 1575460551.9777446
        ms_loader = MSDataLoader(log_path_01)
        loader_01 = DataLoader(log_path_01)
        loader_01._loader = ms_loader

        loader = LoaderStruct(loader_id=train_job_01,
                              name=name_01,
                              path=log_path_01,
                              latest_update_time=modify_time_01,
                              data_loader=loader_01)
        loader_pool = {train_job_01: loader}
        d_manager = DataManager(summary_base_dir)
        d_manager._status = DataManagerStatus.LOADING.value
        d_manager._detail_cache._loader_pool = loader_pool
        tag = 'image'
        with pytest.raises(ParamValueError):
            d_manager.list_tensors(train_job_01, tag)

        shutil.rmtree(summary_base_dir)

    def test_list_tensors_with_not_exist_train_job(self):
        """Test list_tensors method with parameter train_id not found in loader_pool."""
        summary_base_dir = tempfile.mkdtemp()
        d_manager = DataManager(summary_base_dir)
        d_manager._status = DataManagerStatus.LOADING.value
        tag = 'image'
        train_job_01 = 'train_01'
        with pytest.raises(TrainJobNotExistError) as ex_info:
            d_manager.list_tensors(train_job_01, tag)
        shutil.rmtree(summary_base_dir)
        assert ex_info.value.message == 'Train job is not exist. Detail: Can not find the given train job in cache.'

    @patch.object(data_manager.DataLoaderGenerator, "generate_loaders")
    def test_caching(self, mock_generate_loaders):
        """Test caching."""
        # Load summaries the first time.
        job_num = 10
        summary_base_dir = tempfile.NamedTemporaryFile().name
        loader_dict = self._make_loader_dict(summary_base_dir, job_num)
        expected_loader_ids = list(loader_dict.keys())

        mock_generate_loaders.return_value = loader_dict
        mock_data_manager = data_manager.DataManager(summary_base_dir)
        mock_data_manager._detail_cache._execute_loader = Mock()

        mock_data_manager.start_load_data().join()
        current_loader_ids = mock_data_manager._detail_cache._loader_pool.keys()

        assert sorted(current_loader_ids) == sorted(expected_loader_ids)

        # Add new summaries.
        new_loader_dict = self._make_loader_dict(summary_base_dir, 6, job_num)
        loader_dict.update(new_loader_dict)
        expected_loader_ids.extend(list(loader_dict.keys()))
        expected_loader_ids = expected_loader_ids[-MAX_DATA_LOADER_SIZE:]

        mock_generate_loaders.return_value = loader_dict
        mock_data_manager.start_load_data().join()
        current_loader_ids = mock_data_manager._detail_cache._loader_pool.keys()

        assert sorted(current_loader_ids) == sorted(expected_loader_ids)

        shutil.rmtree(summary_base_dir)
