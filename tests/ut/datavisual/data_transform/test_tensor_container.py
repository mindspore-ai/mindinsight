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
"""Test tensor container."""
import unittest.mock as mock

import numpy as np

from mindinsight.datavisual.data_transform import tensor_container as tensor
from mindinsight.utils.tensor import TensorUtils


class TestTensorContainer:
    """Test Tensor Container."""

    def test_get_ndarray(self):
        """Tests get ndarray."""
        mocked_input = mock.MagicMock()
        mocked_input.float_data = [1, 2, 3, 4]
        mocked_input.dims = [2, 2]
        tensor_container = tensor.TensorContainer(mocked_input)
        result = tensor_container.get_ndarray(mocked_input.float_data)
        for res_array, literal_array in zip(result, [[1, 2], [3, 4]]):
            assert all(res_array == literal_array)

    def test_get_statistics_from_tensor(self):
        """Tests get statistics from tensor."""
        ndarray = np.array([1, 2, 3, 4, 5, float('-INF'), float('INF'), float('NAN')]).reshape(
            [2, 2, 2])
        statistics = TensorUtils.get_statistics_from_tensor(ndarray)
        assert (statistics.max, statistics.min, statistics.avg, statistics.count,
                statistics.nan_count, statistics.neg_inf_count, statistics.pos_inf_count) == \
               (5, 1, 3, 8,
                1, 1, 1)

    def test_calc_original_buckets(self):
        """Tests calculate original buckets."""
        ndarray = np.array([1, 2, 3, 4, 5, float('-INF'), float('INF'), float('NAN')]).reshape(
            [2, 2, 2])
        statistics = TensorUtils.get_statistics_from_tensor(ndarray)
        buckets = tensor.calc_original_buckets(ndarray, statistics)

        assert (buckets[0].left, buckets[0].width, buckets[0].count) == (1, 2, 2)
        assert (buckets[1].left, buckets[1].width, buckets[1].count) == (3, 2, 3)
