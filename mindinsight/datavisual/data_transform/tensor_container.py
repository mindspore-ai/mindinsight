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
"""Tensor data container."""
import numpy as np

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_transform.histogram import Histogram, Bucket
from mindinsight.datavisual.utils.utils import calc_histogram_bins
from mindinsight.utils.exceptions import ParamValueError

F32_MIN, F32_MAX = np.finfo(np.float32).min, np.finfo(np.float32).max
MAX_TENSOR_COUNT = 10000000


class Statistics:
    """Statistics data class.

    Args:
        max_value (float): max value of tensor data.
        min_value (float): min value of tensor data.
        avg_value (float): avg value of tensor data.
        count (int): total count of tensor data.
        nan_count (int): count of NAN.
        neg_inf_count (int): count of negative INF.
        pos_inf_count (int): count of positive INF.
    """

    def __init__(self, max_value=0, min_value=0, avg_value=0,
                 count=0, nan_count=0, neg_inf_count=0, pos_inf_count=0):
        self._max = max_value
        self._min = min_value
        self._avg = avg_value
        self._count = count
        self._nan_count = nan_count
        self._neg_inf_count = neg_inf_count
        self._pos_inf_count = pos_inf_count

    @property
    def max(self):
        """Get max value of tensor."""
        return self._max

    @property
    def min(self):
        """Get min value of tensor."""
        return self._min

    @property
    def avg(self):
        """Get avg value of tensor."""
        return self._avg

    @property
    def count(self):
        """Get total count of tensor."""
        return self._count

    @property
    def nan_count(self):
        """Get count of NAN."""
        return self._nan_count

    @property
    def neg_inf_count(self):
        """Get count of negative INF."""
        return self._neg_inf_count

    @property
    def pos_inf_count(self):
        """Get count of positive INF."""
        return self._pos_inf_count


def get_statistics_from_tensor(tensors):
    """
    Calculates statistics data of tensor.

    Args:
        tensors (numpy.ndarray): An numpy.ndarray of tensor data.

    Returns:
         an instance of Statistics.
    """
    ma_value = np.ma.masked_invalid(tensors)
    total, valid = tensors.size, ma_value.count()
    invalids = []
    for isfn in np.isnan, np.isposinf, np.isneginf:
        if total - valid > sum(invalids):
            count = np.count_nonzero(isfn(tensors))
            invalids.append(count)
        else:
            invalids.append(0)

    nan_count, pos_inf_count, neg_inf_count = invalids
    if not valid:
        logger.warning('There are no valid values in the tensors(size=%d, shape=%s)', total, tensors.shape)
        statistics = Statistics(max_value=0,
                                min_value=0,
                                avg_value=0,
                                count=total,
                                nan_count=nan_count,
                                neg_inf_count=neg_inf_count,
                                pos_inf_count=pos_inf_count)
        return statistics

    # BUG: max of a masked array with dtype np.float16 returns inf
    # See numpy issue#15077
    if issubclass(tensors.dtype.type, np.floating):
        tensor_min = ma_value.min(fill_value=np.PINF)
        tensor_max = ma_value.max(fill_value=np.NINF)
        if tensor_min < F32_MIN or tensor_max > F32_MAX:
            logger.warning('Values(%f, %f) are too large, you may encounter some undefined '
                           'behaviours hereafter.', tensor_min, tensor_max)
    else:
        tensor_min = ma_value.min()
        tensor_max = ma_value.max()
    tensor_sum = ma_value.sum(dtype=np.float64)
    statistics = Statistics(max_value=tensor_max,
                            min_value=tensor_min,
                            avg_value=tensor_sum / valid,
                            count=total,
                            nan_count=nan_count,
                            neg_inf_count=neg_inf_count,
                            pos_inf_count=pos_inf_count)
    return statistics


def calc_original_buckets(np_value, stats):
    """
    Calculate buckets from tensor data.

    Args:
        np_value (numpy.ndarray): An numpy.ndarray of tensor data.
        stats (Statistics): An instance of Statistics about tensor data.

    Returns:
        list, a list of bucket about tensor data.

    Raises:
        ParamValueError, If np_value or stats is None.
    """
    if np_value is None or stats is None:
        raise ParamValueError("Invalid input. np_value or stats is None.")
    valid_count = stats.count - stats.nan_count - stats.neg_inf_count - stats.pos_inf_count
    if not valid_count:
        return []

    bins = calc_histogram_bins(valid_count)
    first_edge, last_edge = stats.min, stats.max

    if not first_edge < last_edge:
        first_edge -= 0.5
        last_edge += 0.5

    bins = np.linspace(first_edge, last_edge, bins + 1, dtype=np_value.dtype)
    hists, edges = np.histogram(np_value, bins=bins)

    buckets = []
    for hist, edge1, edge2 in zip(hists, edges, edges[1:]):
        bucket = Bucket(edge1, edge2 - edge1, hist)
        buckets.append(bucket)

    return buckets


class TensorContainer:
    """
    Tensor data container.

    Args:
        tensor_message (Summary.TensorProto): Tensor message in summary file.
    """

    def __init__(self, tensor_message):
        # Original dims can not be pickled to transfer to other process, so tuple is used.
        self._dims = tuple(tensor_message.dims)
        self._data_type = tensor_message.data_type
        self._np_array = self.get_ndarray(tensor_message.float_data)
        self._stats = get_statistics_from_tensor(self._np_array)
        original_buckets = calc_original_buckets(self._np_array, self._stats)
        self._count = sum(bucket.count for bucket in original_buckets)
        self._max = self._stats.max
        self._min = self._stats.min
        self._histogram = Histogram(tuple(original_buckets), self._max, self._min, self._count)

    @property
    def size(self):
        """Get size of tensor."""
        return self._np_array.size

    @property
    def dims(self):
        """Get dims of tensor."""
        return self._dims

    @property
    def data_type(self):
        """Get data type of tensor."""
        return self._data_type

    @property
    def ndarray(self):
        """Get ndarray of tensor."""
        return self._np_array

    @property
    def max(self):
        """Get max value of tensor."""
        return self._max

    @property
    def min(self):
        """Get min value of tensor."""
        return self._min

    @property
    def stats(self):
        """Get statistics data of tensor."""
        return self._stats

    @property
    def count(self):
        """Get count value of tensor."""
        return self._count

    @property
    def histogram(self):
        """Get histogram data."""
        return self._histogram

    def buckets(self):
        """Get histogram buckets."""
        return self._histogram.buckets()

    def get_ndarray(self, tensor):
        """
        Get ndarray of tensor.

        Args:
            tensor (mindinsight_anf_ir.proto.DataType): tensor data.

        Returns:
            numpy.ndarray, ndarray of tensor.
        """
        return np.array(tuple(tensor)).reshape(self.dims)
