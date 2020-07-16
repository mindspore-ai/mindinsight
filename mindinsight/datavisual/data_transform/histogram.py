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
"""Histogram data."""
import math

from mindinsight.utils.exceptions import ParamValueError
from mindinsight.datavisual.utils.utils import calc_histogram_bins


def mask_invalid_number(num):
    """Mask invalid number to 0."""
    if math.isnan(num) or math.isinf(num):
        return type(num)(0)

    return num


class Bucket:
    """
    Bucket data class.

    Args:
        left (double): Left edge of the histogram bucket.
        width (double): Width of the histogram bucket.
        count (int): Count of numbers fallen in the histogram bucket.
    """
    def __init__(self, left, width, count):
        self._left = left
        self._width = width
        self._count = count

    @property
    def left(self):
        """Gets left edge of the histogram bucket."""
        return self._left

    @property
    def count(self):
        """Gets count of numbers fallen in the histogram bucket."""
        return self._count

    @property
    def width(self):
        """Gets width of the histogram bucket."""
        return self._width

    @property
    def right(self):
        """Gets right edge of the histogram bucket."""
        return self._left + self._width

    def as_tuple(self):
        """Gets the bucket as tuple."""
        return self._left, self._width, self._count

    def __repr__(self):
        """Returns repr(self)."""
        return "Bucket(left={}, width={}, count={})".format(self._left, self._width, self._count)


class Histogram:
    """
    Histogram data class.

    Args:
        buckets (tuple[Bucket]): The buckets of histogram data.
        max_val (number): The max value of histogram data.
        min_val (number): The min value of histogram data.
        count (int): The count of histogram data.
    """

    # Max quantity of original buckets.
    MAX_ORIGINAL_BUCKETS_COUNT = 90

    def __init__(self, buckets, max_val, min_val, count):
        self._visual_max = max_val
        self._visual_min = min_val
        self._count = count
        self._original_buckets = buckets
        # default bin number
        self._visual_bins = calc_histogram_bins(count)
        # Note that tuple is immutable, so sharing tuple is often safe.
        self._re_sampled_buckets = ()

    @property
    def original_buckets_count(self):
        """Gets original buckets quantity."""
        return len(self._original_buckets)

    def set_visual_range(self, max_val: float, min_val: float, bins: int) -> None:
        """
        Sets visual range for later re-sampling.

        It's caller's duty to ensure input is valid.

        Why we need visual range for histograms? Aligned buckets between steps can help users know about the trend of
        tensors. Miss aligned buckets between steps might miss-lead users about the trend of a tensor. Because for
        given tensor, if you have thinner buckets, count of every bucket will get lower, however, if you have
        thicker buckets, count of every bucket will get higher.  When they are displayed together, user might think
        the histogram with thicker buckets has more values. This is miss-leading. So we need to unify buckets across
        steps. Visual range for histogram is a technology for unifying buckets.

        Args:
            max_val (float): Max value for visual histogram.
            min_val (float): Min value for visual histogram.
            bins (int): Bins number for visual histogram.
        """
        if max_val < min_val:
            raise ParamValueError(
                "Invalid input. max_val({}) is less or equal than min_val({}).".format(max_val, min_val))

        if bins < 1:
            raise ParamValueError("Invalid input bins({}). Must be greater than 0.".format(bins))

        self._visual_max = max_val
        self._visual_min = min_val
        self._visual_bins = bins

        # mark _re_sampled_buckets to empty
        self._re_sampled_buckets = ()

    def _calc_intersection_len(self, max1, min1, max2, min2):
        """Calculates intersection length of [min1, max1] and [min2, max2]."""
        if max1 < min1:
            raise ParamValueError(
                "Invalid input. max1({}) is less than min1({}).".format(max1, min1))

        if max2 < min2:
            raise ParamValueError(
                "Invalid input. max2({}) is less than min2({}).".format(max2, min2))

        if min1 <= min2:
            if max1 <= min2:
                # return value must be calculated by max1.__sub__
                return max1 - max1
            if max1 <= max2:
                return max1 - min2
            # max1 > max2
            return max2 - min2

        # min1 > min2
        if max2 <= min1:
            return max2 - max2
        if max2 <= max1:
            return max2 - min1
        return max1 - min1

    def _re_sample_buckets(self):
        """Re-samples buckets according to visual_max, visual_min and visual_bins."""
        if self._visual_max == self._visual_min:
            # Adjust visual range if max equals min.
            self._visual_max += 0.5
            self._visual_min -= 0.5

        width = (self._visual_max - self._visual_min) / self._visual_bins

        if not self._count:
            self._re_sampled_buckets = tuple(
                Bucket(self._visual_min + width * i, width, 0)
                for i in range(self._visual_bins))
            return

        re_sampled = []
        original_pos = 0
        original_bucket = self._original_buckets[original_pos]
        for i in range(self._visual_bins):
            cur_left = self._visual_min + width * i
            cur_right = cur_left + width
            cur_estimated_count = 0.0

            # Skip no bucket range.
            if cur_right <= original_bucket.left:
                re_sampled.append(Bucket(cur_left, width, math.ceil(cur_estimated_count)))
                continue

            # Skip no intersect range.
            while cur_left >= original_bucket.right:
                original_pos += 1
                if original_pos >= len(self._original_buckets):
                    break
                original_bucket = self._original_buckets[original_pos]

            # entering with this condition: cur_right > original_bucket.left and cur_left < original_bucket.right
            while True:
                if original_pos >= len(self._original_buckets):
                    break
                original_bucket = self._original_buckets[original_pos]

                intersection = self._calc_intersection_len(
                    min1=cur_left, max1=cur_right,
                    min2=original_bucket.left, max2=original_bucket.right)
                if not original_bucket.width:
                    estimated_count = original_bucket.count
                else:
                    estimated_count = (intersection / original_bucket.width) * original_bucket.count

                cur_estimated_count += estimated_count
                if cur_right > original_bucket.right:
                    # Need to sample next original bucket to this visual bucket.
                    original_pos += 1
                else:
                    # Current visual bucket has taken all intersect buckets into account.
                    break

            re_sampled.append(Bucket(cur_left, width, math.ceil(cur_estimated_count)))

        self._re_sampled_buckets = tuple(re_sampled)

    def buckets(self, convert_to_tuple=True):
        """
        Get visual buckets instead of original buckets.

        Args:
            convert_to_tuple (bool): Whether convert bucket object to tuple.

        Returns:
            tuple, contains buckets.
        """
        if not self._re_sampled_buckets:
            self._re_sample_buckets()

        if not convert_to_tuple:
            return self._re_sampled_buckets

        return tuple(bucket.as_tuple() for bucket in self._re_sampled_buckets)
