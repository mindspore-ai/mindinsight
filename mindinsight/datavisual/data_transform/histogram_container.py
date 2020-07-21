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
"""Histogram data container."""
from mindinsight.datavisual.data_transform.histogram import Histogram, Bucket, mask_invalid_number
from mindinsight.datavisual.proto_files.mindinsight_summary_pb2 import Summary


class HistogramContainer:
    """
        Histogram data container.

        Args:
            histogram_message (Summary.Histogram): Histogram message in summary file.
    """

    def __init__(self, histogram_message: Summary.Histogram):
        original_buckets = [Bucket(bucket.left, bucket.width, bucket.count) for bucket in histogram_message.buckets]
        # Ensure buckets are sorted from min to max.
        original_buckets.sort(key=lambda bucket: bucket.left)
        self._count = sum(bucket.count for bucket in original_buckets)
        self._max = mask_invalid_number(histogram_message.max)
        self._min = mask_invalid_number(histogram_message.min)
        self._histogram = Histogram(tuple(original_buckets), self._max, self._min, self._count)

    @property
    def max(self):
        """Gets max value of the tensor."""
        return self._max

    @property
    def min(self):
        """Gets min value of the tensor."""
        return self._min

    @property
    def count(self):
        """Gets valid number count of the tensor."""
        return self._count

    @property
    def histogram(self):
        """Gets histogram data"""
        return self._histogram

    def buckets(self):
        """Gets histogram buckets"""
        return self._histogram.buckets()
