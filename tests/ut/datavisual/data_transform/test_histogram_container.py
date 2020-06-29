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
        """Tests get buckets."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_input.buckets = [mocked_bucket]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=1, min_val=0, bins=1)
        buckets = histogram.buckets()
        assert buckets == ((0.0, 1.0, 1),)

    def test_re_sample_buckets_split_original(self):
        """Tests splitting original buckets when re-sampling."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_input.buckets = [mocked_bucket]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=1, min_val=0, bins=3)
        buckets = histogram.buckets()
        assert buckets == ((0.0, 0.3333333333333333, 1), (0.3333333333333333, 0.3333333333333333, 1),
                           (0.6666666666666666, 0.3333333333333333, 1))

    def test_re_sample_buckets_zero_bucket(self):
        """Tests zero bucket when re-sampling."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_bucket2 = mock.MagicMock()
        mocked_bucket2.left = 1
        mocked_bucket2.width = 1
        mocked_bucket2.count = 2
        mocked_input.buckets = [mocked_bucket, mocked_bucket2]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=3, min_val=-1, bins=4)
        buckets = histogram.buckets()
        assert buckets == ((-1.0, 1.0, 0), (0.0, 1.0, 1), (1.0, 1.0, 2), (2.0, 1.0, 0))

    def test_re_sample_buckets_merge_bucket(self):
        """Tests merging counts from two buckets when re-sampling."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_bucket2 = mock.MagicMock()
        mocked_bucket2.left = 1
        mocked_bucket2.width = 1
        mocked_bucket2.count = 10
        mocked_input.buckets = [mocked_bucket, mocked_bucket2]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=3, min_val=-1, bins=5)
        buckets = histogram.buckets()
        assert buckets == (
            (-1.0, 0.8, 0), (-0.19999999999999996, 0.8, 1), (0.6000000000000001, 0.8, 5), (1.4000000000000004, 0.8, 6),
            (2.2, 0.8, 0))

    def test_re_sample_buckets_zero_width(self):
        """Test zero width bucket when re-sampling."""
        mocked_input = mock.MagicMock()
        mocked_bucket = mock.MagicMock()
        mocked_bucket.left = 0
        mocked_bucket.width = 1
        mocked_bucket.count = 1
        mocked_bucket2 = mock.MagicMock()
        mocked_bucket2.left = 1
        mocked_bucket2.width = 0
        mocked_bucket2.count = 2
        mocked_input.buckets = [mocked_bucket, mocked_bucket2]
        histogram = hist.HistogramContainer(mocked_input)
        histogram.set_visual_range(max_val=2, min_val=0, bins=3)
        buckets = histogram.buckets()
        assert buckets == (
            (0.0, 0.6666666666666666, 1),
            (0.6666666666666666, 0.6666666666666666, 3),
            (1.3333333333333333, 0.6666666666666666, 0))
