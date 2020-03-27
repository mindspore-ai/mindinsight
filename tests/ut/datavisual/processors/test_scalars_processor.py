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
    Test scalars processor.
Usage:
    pytest tests/ut/datavisual
"""
import tempfile
from unittest.mock import Mock

import pytest
from tests.ut.datavisual.mock import MockLogger
from tests.ut.datavisual.utils.log_operations import LogOperations
from tests.ut.datavisual.utils.utils import check_loading_done, delete_files_or_dirs

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.loader_generators.data_loader_generator import DataLoaderGenerator
from mindinsight.datavisual.processors.scalars_processor import ScalarsProcessor
from mindinsight.datavisual.utils import crc32
from mindinsight.utils.exceptions import ParamValueError


class TestScalarsProcessor:
    """Test scalar processor api."""
    _steps_list = [1, 3, 5]
    _tag_name = 'tag_name'
    _plugin_name = 'scalar'
    _complete_tag_name = f'{_tag_name}/{_plugin_name}'

    _temp_path = None
    _scalars_values = None
    _scalars_metadata = None
    _mock_data_manager = None
    _train_id = None

    _generated_path = []

    @classmethod
    def setup_class(cls):
        """Mock common environment for scalars unittest."""
        crc32.GetValueFromStr = Mock(return_value=0)
        crc32.GetMaskCrc32cValue = Mock(return_value=0)
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    @pytest.fixture(scope='function')
    def load_scalar_record(self):
        """Load scalar record."""
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)

        self._train_id = log_dir.replace(summary_base_dir, ".")

        self._temp_path, self._scalars_metadata, self._scalars_values = LogOperations.generate_log(
            PluginNameEnum.SCALAR.value, log_dir, dict(step=self._steps_list, tag=self._tag_name))

        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager([DataLoaderGenerator(summary_base_dir)])
        self._mock_data_manager.start_load_data(reload_interval=0)

        # wait for loading done
        check_loading_done(self._mock_data_manager, time_limit=5)

    def test_get_metadata_list_with_not_exist_id(self, load_scalar_record):
        """Get metadata list with not exist id."""
        test_train_id = 'not_exist_id'
        scalar_processor = ScalarsProcessor(self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            scalar_processor.get_metadata_list(test_train_id, self._tag_name)

        assert exc_info.value.error_code == '50540002'
        assert "Can not find any data in loader pool about the train job." in exc_info.value.message

    def test_get_metadata_list_with_not_exist_tag(self, load_scalar_record):
        """Get metadata list with not exist tag."""
        test_tag_name = 'not_exist_tag_name'

        scalar_processor = ScalarsProcessor(self._mock_data_manager)

        with pytest.raises(ParamValueError) as exc_info:
            scalar_processor.get_metadata_list(self._train_id, test_tag_name)

        assert exc_info.value.error_code == '50540002'
        assert "Can not find any data in this train job by given tag." in exc_info.value.message

    def test_get_metadata_list_success(self, load_scalar_record):
        """Get metadata list success."""
        test_tag_name = self._complete_tag_name

        scalar_processor = ScalarsProcessor(self._mock_data_manager)
        results = scalar_processor.get_metadata_list(self._train_id, test_tag_name)

        recv_metadata = results.get('metadatas')

        for recv_values, expected_values in zip(recv_metadata, self._scalars_metadata):
            assert recv_values.get('wall_time') == expected_values.get('wall_time')
            assert recv_values.get('step') == expected_values.get('step')
            assert abs(recv_values.get('value') - expected_values.get('value')) < 1e-6
