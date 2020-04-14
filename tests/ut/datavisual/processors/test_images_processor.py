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
    Test images processor.
Usage:
    pytest tests/ut/datavisual
"""
import tempfile
from unittest.mock import Mock

import pytest

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.common.exceptions import ImageNotExistError
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.loader_generators.data_loader_generator import DataLoaderGenerator
from mindinsight.datavisual.processors.images_processor import ImageProcessor
from mindinsight.datavisual.utils import crc32

from ....utils.log_operations import LogOperations
from ....utils.tools import check_loading_done, delete_files_or_dirs, get_image_tensor_from_bytes
from ..mock import MockLogger


class TestImagesProcessor:
    """Test images processor api."""
    _steps_list = [1, 3, 5, 7, 8]
    _more_steps_list = list(range(30))
    _cross_steps_list = [1, 3, 5, 7, 9, 2, 3, 4, 15]

    _tag_name = 'tag_name'
    _plugin_name = 'image'
    _complete_tag_name = f'{_tag_name}/{_plugin_name}'

    _temp_path = None
    _images_values = None
    _images_metadata = None
    _mock_data_manager = None
    _train_id = None

    _generated_path = []

    @classmethod
    def setup_class(cls):
        """Mock common environment for images unittest."""
        crc32.CheckValueAgainstData = Mock(return_value=True)
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    def _init_data_manager(self, steps_list):
        """
        Generate log and init data_manager.

        Args:
            steps_list (list): Init steps.

        """
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)
        self._train_id = log_dir.replace(summary_base_dir, ".")

        log_operation = LogOperations()
        self._temp_path, self._images_metadata, self._images_values = log_operation.generate_log(
            PluginNameEnum.IMAGE.value, log_dir, dict(steps=steps_list, tag=self._tag_name))
        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager([DataLoaderGenerator(summary_base_dir)])
        self._mock_data_manager.start_load_data(reload_interval=0)

        # wait for loading done
        check_loading_done(self._mock_data_manager, time_limit=5)

    @pytest.fixture(scope='function')
    def load_image_record(self):
        """Load image record."""
        self._init_data_manager(self._steps_list)

    @pytest.fixture(scope='function')
    def load_more_than_limit_image_record(self):
        """Load image record."""
        self._init_data_manager(self._more_steps_list)

    @pytest.fixture(scope='function')
    def load_reservoir_remove_sample_image_record(self):
        """Load image record."""
        self._init_data_manager(self._cross_steps_list)

    @pytest.mark.usefixtures('load_image_record')
    def test_get_metadata_list_with_not_exist_id(self):
        """Test getting metadata list with not exist id."""
        test_train_id = 'not_exist_id'
        image_processor = ImageProcessor(self._mock_data_manager)
        with pytest.raises(TrainJobNotExistError) as exc_info:
            image_processor.get_metadata_list(test_train_id, self._tag_name)

        assert exc_info.value.error_code == '50545005'
        assert exc_info.value.message == "Train job is not exist. Detail: Can not find the given train job in cache."

    @pytest.mark.usefixtures('load_image_record')
    def test_get_metadata_list_with_not_exist_tag(self):
        """Test get metadata list with not exist tag."""
        test_tag_name = 'not_exist_tag_name'

        image_processor = ImageProcessor(self._mock_data_manager)

        with pytest.raises(ImageNotExistError) as exc_info:
            image_processor.get_metadata_list(self._train_id, test_tag_name)

        assert exc_info.value.error_code == '5054500D'
        assert "Can not find any data in this train job by given tag." in exc_info.value.message

    @pytest.mark.usefixtures('load_image_record')
    def test_get_metadata_list_success(self):
        """Test getting metadata list success."""
        test_tag_name = self._complete_tag_name

        image_processor = ImageProcessor(self._mock_data_manager)
        results = image_processor.get_metadata_list(self._train_id, test_tag_name).get('metadatas')

        assert results == self._images_metadata

    @pytest.mark.usefixtures('load_image_record')
    def test_get_single_image_with_not_exist_id(self):
        """Test getting single image with not exist id."""
        test_train_id = 'not_exist_id'
        test_tag_name = self._complete_tag_name
        test_step = self._steps_list[0]
        image_processor = ImageProcessor(self._mock_data_manager)

        with pytest.raises(TrainJobNotExistError) as exc_info:
            image_processor.get_single_image(test_train_id, test_tag_name, test_step)

        assert exc_info.value.error_code == '50545005'
        assert exc_info.value.message == "Train job is not exist. Detail: Can not find the given train job in cache."

    @pytest.mark.usefixtures('load_image_record')
    def test_get_single_image_with_not_exist_tag(self):
        """Test getting single image with not exist tag."""
        test_tag_name = 'not_exist_tag_name'
        test_step = self._steps_list[0]

        image_processor = ImageProcessor(self._mock_data_manager)

        with pytest.raises(ImageNotExistError) as exc_info:
            image_processor.get_single_image(self._train_id, test_tag_name, test_step)

        assert exc_info.value.error_code == '5054500D'
        assert "Can not find any data in this train job by given tag." in exc_info.value.message

    @pytest.mark.usefixtures('load_image_record')
    def test_get_single_image_with_not_exist_step(self):
        """Test getting single image with not exist step."""
        test_tag_name = self._complete_tag_name
        test_step = 10000

        image_processor = ImageProcessor(self._mock_data_manager)

        with pytest.raises(ImageNotExistError) as exc_info:
            image_processor.get_single_image(self._train_id, test_tag_name, test_step)

        assert exc_info.value.error_code == '5054500D'
        assert exc_info.value.message == "Image is not exist. " \
               "Detail: Can not find the step with given train job id and tag."

    @pytest.mark.usefixtures('load_image_record')
    def test_get_single_image_success(self):
        """Test getting single image successfully."""
        test_tag_name = self._complete_tag_name
        test_step_index = 0
        test_step = self._steps_list[test_step_index]

        expected_image_tensor = self._images_values.get(test_step)
        image_processor = ImageProcessor(self._mock_data_manager)
        results = image_processor.get_single_image(self._train_id, test_tag_name, test_step)
        recv_image_tensor = get_image_tensor_from_bytes(results)

        assert recv_image_tensor.any() == expected_image_tensor.any()

    @pytest.mark.usefixtures('load_more_than_limit_image_record')
    def test_reservoir_add_sample(self):
        """Test adding sample in reservoir."""
        test_tag_name = self._complete_tag_name

        cnt = 0

        for step in self._more_steps_list:
            test_step = step

            image_processor = ImageProcessor(self._mock_data_manager)

            try:
                image_processor.get_single_image(self._train_id, test_tag_name, test_step)
            except ImageNotExistError:
                cnt += 1
        assert len(self._more_steps_list) - cnt == 10

    @pytest.mark.usefixtures('load_reservoir_remove_sample_image_record')
    def test_reservoir_remove_sample(self):
        """
        Test removing sample in reservoir.

        If step list is [1, 3, 5, 7, 9, 2, 3, 4, 15],
        and then [3, 5, 7, 9] will be deleted.
        Results will be [1, 2, 3, 4, 15].
        """
        test_tag_name = self._complete_tag_name

        not_found_step_list = []
        current_step_list = []

        steps_list = set(self._cross_steps_list)
        for step in steps_list:
            test_step = step

            image_processor = ImageProcessor(self._mock_data_manager)

            try:
                image_processor.get_single_image(self._train_id, test_tag_name, test_step)
                current_step_list.append(test_step)
            except ImageNotExistError:
                not_found_step_list.append(test_step)

        assert current_step_list == [1, 2, 3, 4, 15]
        assert not_found_step_list == [5, 7, 9]
