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
"""Test reservoir."""
import unittest.mock as mock

import mindinsight.datavisual.data_transform.reservoir as reservoir


class TestHistogramReservoir:
    """Test histogram reservoir."""
    def test_samples(self):
        """Test get samples."""
        my_reservoir = reservoir.ReservoirFactory().create_reservoir(reservoir.PluginNameEnum.HISTOGRAM.value, size=10)
        sample1 = mock.MagicMock()
        sample1.value.count = 1
        sample1.value.max = 102
        sample1.value.min = 101
        sample1.step = 2
        sample1.filename = 'filename'
        sample2 = mock.MagicMock()
        sample2.value.count = 2
        sample2.value.max = 102
        sample2.value.min = 101
        sample2.step = 1
        sample2.filename = 'filename'
        my_reservoir.add_sample(sample1)
        my_reservoir.add_sample(sample2)
        samples = my_reservoir.samples()
        assert len(samples) == 2
