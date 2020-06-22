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
"""Utils."""
import math
from mindinsight.datavisual.common.log import logger


def calc_histogram_bins(count):
    """
    Calculates experience-based optimal bins number for histogram.

    To suppress re-sample bias, there should be enough number in each bin. So we calc bin numbers according to
    count. For very small count(1 - 10), we assign carefully chosen number. For large count, we tried to make
    sure there are 9-10 numbers in each bucket on average. Too many bins will also distract users, so we set max
    number of bins to 30.

    Args:
        count (int): Valid number count for the tensor.

    Returns:
        int, number of histogram bins.
    """
    number_per_bucket = 10
    max_bins = 30

    if not count:
        return 1
    if count <= 5:
        return 2
    if count <= 10:
        return 3
    if count <= 280:
        # note that math.ceil(281/10) + 1 equals 30
        return math.ceil(count / number_per_bucket) + 1

    return max_bins


def contains_null_byte(**kwargs):
    """
    Check if arg contains null byte.

    Args:
        kwargs (Any): Check if arg contains null byte.

    Returns:
        bool, indicates if any arg contains null byte.
    """
    for key, value in kwargs.items():
        if not isinstance(value, str):
            continue
        if '\x00' in value:
            logger.warning('%s contains null byte \\x00.', key)
            return True

    return False
