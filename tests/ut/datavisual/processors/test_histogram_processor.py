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
"""
Function:
    Test histogram processor.
Usage:
    pytest tests/ut/datavisual
"""
import tempfile

import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.common.exceptions import HistogramNotExistError
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.processors.histogram_processor import HistogramProcessor

from ....utils.log_operations import LogOperations
from ....utils.tools import delete_files_or_dirs
from ..mock import MockLogger


class TestHistogramProcessor:
    """Test histogram processor api."""
    _steps_list = [1, 3, 5]
    _tag_name = 'tag_name'
    _plugin_name = 'histogram'
    _complete_tag_name = f'{_tag_name}/{_plugin_name}'

    _temp_path = None
    _histograms = None
    _mock_data_manager = None
    _train_id = None

    _generated_path = []

    @classmethod
    def setup_class(cls):
        """Mock common environment for histograms unittest."""
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    @pytest.fixture(scope='function')
    def load_histogram_record(self):
        """Load histogram record."""
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)
        self._train_id = log_dir.replace(summary_base_dir, ".")

        log_operation = LogOperations()
        self._temp_path, self._histograms, _ = log_operation.generate_log(
            PluginNameEnum.HISTOGRAM.value, log_dir, dict(step=self._steps_list, tag=self._tag_name))
        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager(summary_base_dir)
        thread, brief_thread = self._mock_data_manager.start_load_data()
        thread.join()
        brief_thread.join()

    @pytest.mark.usefixtures('load_histogram_record')
    def test_get_histograms_with_not_exist_id(self):
        """Get histogram data with not exist id."""
        test_train_id = 'not_exist_id'
        processor = HistogramProcessor(self._mock_data_manager)
        with pytest.raises(TrainJobNotExistError) as exc_info:
            processor.get_histograms(test_train_id, self._tag_name)

        assert exc_info.value.error_code == '50545005'
        assert exc_info.value.message == "Train job is not exist. Detail: Can not find the given train job in cache."

    @pytest.mark.usefixtures('load_histogram_record')
    def test_get_histograms_with_not_exist_tag(self):
        """Get histogram data with not exist tag."""
        test_tag_name = 'not_exist_tag_name'

        processor = HistogramProcessor(self._mock_data_manager)

        with pytest.raises(HistogramNotExistError) as exc_info:
            processor.get_histograms(self._train_id, test_tag_name)

        assert exc_info.value.error_code == '5054500F'
        assert "Can not find any data in this train job by given tag." in exc_info.value.message

    @pytest.mark.usefixtures('load_histogram_record')
    def test_get_histograms_success(self):
        """Get histogram data success."""
        test_tag_name = self._complete_tag_name

        processor = HistogramProcessor(self._mock_data_manager)
        results = processor.get_histograms(self._train_id, test_tag_name)

        recv_metadata = results.get('histograms')

        for recv_values, expected_values in zip(recv_metadata, self._histograms):
            assert recv_values.get('wall_time') == expected_values.get('wall_time')
            assert recv_values.get('step') == expected_values.get('step')
