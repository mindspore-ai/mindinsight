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
"""Test histogram."""
import unittest.mock as mock

from mindinsight.datavisual.data_transform import histogram_container as hist


class TestHistogram:
    """Test histogram."""
    def test_get_buckets(self):
        """Test get buckets."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_input.buckets = [mocked_bucket]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=1, min_val=0, bins=1)
        buckets = histogram.buckets()
        assert len(buckets) == 1