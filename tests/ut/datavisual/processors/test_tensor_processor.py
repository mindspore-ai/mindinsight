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
"""
Function:
    Test tensor processor.
Usage:
    pytest tests/ut/datavisual
"""
import tempfile
from unittest.mock import Mock

import pytest
import numpy as np

from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.common.exceptions import TensorNotExistError
from mindinsight.datavisual.data_transform import data_manager
from mindinsight.datavisual.data_transform.tensor_container import calc_original_buckets
from mindinsight.datavisual.processors.tensor_processor import TensorProcessor
from mindinsight.utils.tensor import TensorUtils
from mindinsight.datavisual.utils import crc32
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.utils.exceptions import ParamMissError

from ....utils.log_operations import LogOperations
from ....utils.tools import delete_files_or_dirs
from ..mock import MockLogger


class TestTensorProcessor:
    """Test tensor processor api."""
    _steps_list = [1, 3, 5]
    _tag_name = 'tag_name'
    _plugin_name = 'tensor'
    _complete_tag_name = f'{_tag_name}/{_plugin_name}'

    _temp_path = None
    _tensors = None
    _mock_data_manager = None
    _train_id = None

    _generated_path = []

    @classmethod
    def setup_class(cls):
        """Mock common environment for tensors unittest."""
        crc32.CheckValueAgainstData = Mock(return_value=True)
        data_manager.logger = MockLogger

    def teardown_class(self):
        """Delete temp files."""
        delete_files_or_dirs(self._generated_path)

    @pytest.fixture(scope='function')
    def load_tensor_record(self):
        """Load tensor record."""
        summary_base_dir = tempfile.mkdtemp()
        log_dir = tempfile.mkdtemp(dir=summary_base_dir)
        self._train_id = log_dir.replace(summary_base_dir, ".")

        log_operation = LogOperations()
        self._temp_path, self._tensors, _ = log_operation.generate_log(
            PluginNameEnum.TENSOR.value, log_dir, dict(step=self._steps_list, tag=self._tag_name))
        self._generated_path.append(summary_base_dir)

        self._mock_data_manager = data_manager.DataManager(summary_base_dir)
        self._mock_data_manager.start_load_data().join()

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensors_with_not_exist_id(self):
        """Get tensor data with not exist id."""
        test_train_id = 'not_exist_id'
        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(TrainJobNotExistError) as exc_info:
            processor.get_tensors([test_train_id], [self._tag_name], None, None, None)

        assert exc_info.value.error_code == '50545005'
        assert exc_info.value.message == "Train job is not exist. Detail: Can not find the given train job in cache."

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensors_with_not_exist_tag(self):
        """Get tensor data with not exist tag."""
        test_tag_name = 'not_exist_tag_name'

        processor = TensorProcessor(self._mock_data_manager)

        with pytest.raises(TensorNotExistError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], None, None, None)

        assert exc_info.value.error_code == '50545012'
        assert "Can not find any data in this train job by given tag." in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensors_with_not_support_detail(self):
        """Get tensor data with not support detail."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], None, None, detail='data1')

        assert exc_info.value.error_code == '50540002'
        assert "Invalid parameter value. Can not support this value: data1 of detail." \
               in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_data_with_not_step(self):
        """Get tensor data with not step."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(ParamMissError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], None, None, detail='data')

        assert exc_info.value.error_code == '50540003'
        assert "Param missing. 'step' is required." in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_data_with_not_dims(self):
        """Get tensor data with not dims."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(ParamMissError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], step='1', dims=None, detail='data')

        assert exc_info.value.error_code == '50540003'
        assert "Param missing. 'dims' is required." in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_data_with_wrong_dims(self):
        """Get tensor data with wrong dims."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], step='1', dims='[0,:]', detail='data')

        assert exc_info.value.error_code == '50540002'
        assert "The length of param dims and tensor shape should be the same" in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_data_with_exceed_two_dims(self):
        """Get tensor data with exceed two dims."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        with pytest.raises(ParamValueError) as exc_info:
            processor.get_tensors([self._train_id], [test_tag_name], step='1', dims='[0,:,:,:]', detail='data')

        assert exc_info.value.error_code == '50540002'
        assert "Invalid shape. At most 2 dimensions are specified" in exc_info.value.message

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_data_success(self):
        """Get tensor data success."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        results = processor.get_tensors([self._train_id], [test_tag_name], step='1', dims='[0,0,:-1,:]', detail='data')

        recv_metadata = results.get('tensors')[0].get("values")

        for recv_values, expected_values in zip(recv_metadata, self._tensors):
            assert recv_values.get('wall_time') == expected_values.get('wall_time')
            assert recv_values.get('step') == expected_values.get('step')
            dims = expected_values.get('value').get("dims")
            expected_data = np.array(expected_values.get('value').get("float_data")).reshape(dims)
            recv_tensor = np.array(recv_values.get('value').get("data"))
            expected_tensor = TensorUtils.get_specific_dims_data(
                expected_data, (0, 0, slice(None, -1, None), slice(None)))
            # Compare tensor shape when recv_tensor shape is not empty.
            if recv_tensor.shape != (0,):
                assert recv_tensor.shape == expected_tensor.shape
            assert np.sum(np.isclose(recv_tensor, expected_tensor, rtol=1e-6) == 0) == 0

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_stats_success(self):
        """Get tensor stats success."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        results = processor.get_tensors([self._train_id], [test_tag_name], None, None, detail='stats')

        recv_metadata = results.get('tensors')[0].get("values")

        for recv_values, expected_values in zip(recv_metadata, self._tensors):
            assert recv_values.get('wall_time') == expected_values.get('wall_time')
            assert recv_values.get('step') == expected_values.get('step')
            expected_data = expected_values.get('value').get("float_data")
            expected_statistic_instance = TensorUtils.get_statistics_from_tensor(expected_data)
            expected_statistic = TensorUtils.get_statistics_dict(stats=expected_statistic_instance,
                                                                 overall_stats=expected_statistic_instance)
            recv_statistic = recv_values.get('value').get("statistics")
            assert recv_statistic.get("max") - expected_statistic.get("max") < 1e-6
            assert recv_statistic.get("min") - expected_statistic.get("min") < 1e-6
            assert recv_statistic.get("avg") - expected_statistic.get("avg") < 1e-6
            assert recv_statistic.get("count") - expected_statistic.get("count") < 1e-6

    @pytest.mark.usefixtures('load_tensor_record')
    def test_get_tensor_histogram_success(self):
        """Get tensor histogram success."""
        test_tag_name = self._complete_tag_name

        processor = TensorProcessor(self._mock_data_manager)
        results = processor.get_tensors([self._train_id], [test_tag_name], None, None, detail='histogram')

        recv_metadata = results.get('tensors')[0].get("values")

        for recv_values, expected_values in zip(recv_metadata, self._tensors):
            assert recv_values.get('wall_time') == expected_values.get('wall_time')
            assert recv_values.get('step') == expected_values.get('step')
            expected_data = expected_values.get('value').get("float_data")
            expected_statistic = TensorUtils.get_statistics_from_tensor(expected_data)
            expected_buckets = calc_original_buckets(expected_data, expected_statistic)
            recv_buckets = recv_values.get('value').get("histogram_buckets")

            for recv_bucket, expected_bucket in zip(recv_buckets, expected_buckets):
                assert recv_bucket[0] - expected_bucket.left < 1e-6
                assert recv_bucket[1] - expected_bucket.width < 1e-6
                assert recv_bucket[2] - expected_bucket.count <= 1
