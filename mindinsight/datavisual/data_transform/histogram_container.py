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
import math

from mindinsight.datavisual.proto_files.mindinsight_summary_pb2 import Summary


def _mask_invalid_number(num):
    """Mask invalid number to 0."""
    if math.isnan(num) or math.isinf(num):
        return type(num)(0)

    return num


class HistogramContainer:
    """
    Histogram data container.

    Args:
        histogram_message (Summary.Histogram): Histogram message in summary file.
    """
    def __init__(self, histogram_message: Summary.Histogram):
        self._msg = histogram_message
        self._original_buckets = tuple((bucket.left, bucket.width, bucket.count) for bucket in self._msg.buckets)
        self._max = _mask_invalid_number(histogram_message.max)
        self._min = _mask_invalid_number(histogram_message.min)
        self._visual_max = self._max
        self._visual_min = self._min
        # default bin number
        self._visual_bins = 10
        self._count = self._msg.count
        # Note that tuple is immutable, so sharing tuple is often safe.
        self._re_sampled_buckets = self._original_buckets

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
    def original_msg(self):
        """Get original proto message"""
        return self._msg

    def set_visual_range(self, max_val: float, min_val: float, bins: int) -> None:
        """
        Sets visual range for later re-sampling.

        It's caller's duty to ensure input is valid.

        Args:
            max_val (float): Max value for visual histogram.
            min_val (float): Min value for visual histogram.
            bins (int): Bins number for visual histogram.
        """
        self._visual_max = max_val
        self._visual_min = min_val
        self._visual_bins = bins

        # mark _re_sampled_buckets to empty
        self._re_sampled_buckets = ()

    def _re_sample_buckets(self):
        # Will call re-sample logic in later PR.
        self._re_sampled_buckets = self._original_buckets

    def buckets(self):
        """
        Get visual buckets instead of original buckets.
        """
        if not self._re_sampled_buckets:
            self._re_sample_buckets()

        return self._re_sampled_buckets
