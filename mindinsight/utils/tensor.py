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
"""Tensor utils."""

import numpy as np

from mindinsight.utils.exceptions import ParamValueError
from mindinsight.utils.exceptions import ParamTypeError
from mindinsight.utils.log import setup_logger

F32_MIN, F32_MAX = np.finfo(np.float32).min, np.finfo(np.float32).max
MAX_DIMENSIONS_FOR_TENSOR = 2


class Statistics:
    """Statistics data class.

    Args:
        stats (dict): Statistic info of tensor data.

            - is_bool (bool): If the tensor is bool type.
            - max_value (float): Max value of tensor data.
            - min_value (float): Min value of tensor data.
            - avg_value (float): Avg value of tensor data.
            - count (int): Total count of tensor data.
            - nan_count (int): Count of NAN.
            - neg_zero_count (int): Count of negative zero.
            - pos_zero_count (int): Count of positive zero.
            - zero_count (int): Count of zero.
            - neg_inf_count (int): Count of negative INF.
            - pos_inf_count (int): Count of positive INF.
    """

    def __init__(self, stats):
        self._stats = stats

    @property
    def max(self):
        """Get max value of tensor."""
        return float(self._stats.get('max_value', 0))

    @property
    def min(self):
        """Get min value of tensor."""
        return float(self._stats.get('min_value', 0))

    @property
    def avg(self):
        """Get avg value of tensor."""
        return float(self._stats.get('avg_value', 0))

    @property
    def count(self):
        """Get total count of tensor."""
        return int(self._stats.get('count', 0))

    @property
    def nan_count(self):
        """Get count of NAN."""
        return int(self._stats.get('nan_count', 0))

    @property
    def neg_inf_count(self):
        """Get count of negative INF."""
        return int(self._stats.get('neg_inf_count', 0))

    @property
    def pos_inf_count(self):
        """Get count of positive INF."""
        return int(self._stats.get('pos_inf_count', 0))

    @property
    def neg_zero_count(self):
        """Get count of negative zero."""
        return int(self._stats.get('neg_zero_count', 0))

    @property
    def pos_zero_count(self):
        """Get count of positive zero."""
        return int(self._stats.get('pos_zero_count', 0))

    @property
    def zero_count(self):
        """Get count of zero."""
        return int(self._stats.get('zero_count', 0))

    @property
    def true_count(self):
        """Get count of False."""
        return self.pos_zero_count if self.is_bool else 0

    @property
    def false_count(self):
        """Get count of True."""
        return self.zero_count if self.is_bool else 0

    @property
    def is_bool(self):
        """Whether the tensor is bool type."""
        return self._stats.get('is_bool', False)


class TensorComparison:
    """TensorComparison class.

    Args:
        tolerance (float): Tolerance for calculating tensor diff.
        stats (float): Statistics of tensor diff.
        value (numpy.ndarray): Tensor diff.
    """

    def __init__(self, tolerance=0, stats=None, value=None):
        self._tolerance = tolerance
        self._stats = stats
        self._value = value

    @property
    def tolerance(self):
        """Get tolerance of TensorComparison."""
        return self._tolerance

    @property
    def stats(self):
        """Get stats of tensor diff."""
        return self._stats

    def update(self, tolerance, value):
        """update tensor comparisons."""
        self._tolerance = tolerance
        self._value = value

    @property
    def value(self):
        """Get value of tensor diff."""
        return self._value


def str_to_slice_or_int(input_str):
    """
    Translate param from string to slice or int.

    Args:
        input_str (str): The string to be translated.

    Returns:
        Union[int, slice], the transformed param.
    """
    try:
        if ':' in input_str:
            ret = slice(*map(lambda x: int(x.strip()) if x.strip() else None, input_str.split(':')))
        else:
            ret = int(input_str)
    except ValueError:
        raise ParamValueError("Invalid shape. Convert int from str failed. input_str: {}".format(input_str))
    return ret


class TensorUtils:
    """Tensor Utils class."""

    @staticmethod
    def parse_shape(shape, limit=0):
        """
        Parse shape from str.

        Args:
            shape (str): Specify shape of tensor.
            limit (int): The max dimensions specified. Default value is 0 which means that there is no limitation.

        Returns:
            Union[None, tuple], a string like this: "[0, 0, 1:10, :]" will convert to this value:
                (0, 0, slice(1, 10, None), slice(None, None, None)].

        Raises:
            ParamValueError, If type of shape is not str or format is not correct or exceed specified dimensions.
        """
        if shape is None:
            return shape
        if not (isinstance(shape, str) and shape.strip().startswith('[') and shape.strip().endswith(']')):
            raise ParamValueError("Invalid shape. The type of shape should be str and start with `[` and "
                                  "end with `]`. Received: {}.".format(shape))
        shape = shape.strip()[1:-1]
        dimension_size = sum(1 for dim in shape.split(',') if dim.count(':'))
        if limit and dimension_size > limit:
            raise ParamValueError("Invalid shape. At most {} dimensions are specified. Received: {}"
                                  .format(limit, shape))
        parsed_shape = tuple(
            str_to_slice_or_int(dim.strip()) for dim in shape.split(',')) if shape else tuple()
        return parsed_shape

    @staticmethod
    def get_specific_dims_data(ndarray, dims):
        """
        Get specific dims data.

        Args:
            ndarray (numpy.ndarray): An ndarray of numpy.
            dims (tuple): A tuple of specific dims.

        Returns:
            numpy.ndarray, an ndarray of specific dims tensor data.

        Raises:
            ParamValueError, If the length of param dims is not equal to the length of tensor dims.
            IndexError, If the param dims and tensor shape is unmatched.
        """
        if ndarray.size == 0:
            return ndarray
        if len(ndarray.shape) != len(dims):
            raise ParamValueError("Invalid dims. The length of param dims and tensor shape should be the same.")
        try:
            result = ndarray[dims]
        except IndexError:
            raise ParamValueError("Invalid shape. Shape unmatched. Received: {}, tensor shape: {}"
                                  .format(dims, ndarray.shape))
        # Make sure the return type is numpy.ndarray.
        if not isinstance(result, np.ndarray):
            result = np.array(result)
        return result

    @staticmethod
    def get_statistics_from_tensor(tensors):
        """
        Calculates statistics data of tensor.

        Args:
            tensors (numpy.ndarray): An numpy.ndarray of tensor data.

        Returns:
             Statistics, an instance of Statistics.
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
        logger = setup_logger("utils", "utils")
        if not valid:
            logger.warning('There are no valid values in the tensors(size=%d, shape=%s)', total, tensors.shape)
            statistics = Statistics({'max_value': 0,
                                     'min_value': 0,
                                     'avg_value': 0,
                                     'count': total,
                                     'nan_count': nan_count,
                                     'neg_inf_count': neg_inf_count,
                                     'pos_inf_count': pos_inf_count})
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
        with np.errstate(invalid='ignore'):
            neg_zero_count = np.sum(ma_value < 0)
        with np.errstate(invalid='ignore'):
            pos_zero_count = np.sum(ma_value > 0)
        with np.errstate(invalid='ignore'):
            zero_count = np.sum(ma_value == 0)
        statistics = Statistics({'is_bool': tensors.dtype == np.bool,
                                 'max_value': tensor_max,
                                 'min_value': tensor_min,
                                 'avg_value': tensor_sum / valid,
                                 'count': total,
                                 'neg_zero_count': neg_zero_count,
                                 'pos_zero_count': pos_zero_count,
                                 'zero_count': zero_count,
                                 'nan_count': nan_count,
                                 'neg_inf_count': neg_inf_count,
                                 'pos_inf_count': pos_inf_count})
        return statistics

    @staticmethod
    def get_statistics_dict(stats, overall_stats):
        """
        Get statistics dict according to statistics value.

        Args:
            stats (Statistics): An instance of Statistics for sliced tensor.
            overall_stats (Statistics): An instance of Statistics for whole tensor.

        Returns:
            dict, a dict including 'max', 'min', 'avg', 'count',
                'nan_count', 'neg_inf_count', 'pos_inf_count', 'overall_max', 'overall_min'.
        """
        statistics = {
            "max": float(stats.max),
            "min": float(stats.min),
            "avg": float(stats.avg),
            "count": stats.count,
            "nan_count": stats.nan_count,
            "neg_inf_count": stats.neg_inf_count,
            "pos_inf_count": stats.pos_inf_count}
        overall_statistics = TensorUtils.get_overall_statistic_dict(overall_stats)
        statistics.update(overall_statistics)
        return statistics

    @staticmethod
    def get_overall_statistic_dict(overall_stats):
        """
        Get overall statistics dict according to statistics value.

        Args:
            overall_stats (Statistics): An instance of Statistics for whole tensor.

        Returns:
            dict, overall statistics.
        """
        if not overall_stats:
            return {}
        if overall_stats.is_bool:
            res = {
                'overall_count': overall_stats.count,
                'overall_true_count': overall_stats.true_count,
                'overall_false_count': overall_stats.false_count
            }
        else:
            res = {
                "overall_max": float(overall_stats.max),
                "overall_min": float(overall_stats.min),
                "overall_avg": float(overall_stats.avg),
                "overall_count": overall_stats.count,
                "overall_nan_count": overall_stats.nan_count,
                "overall_neg_inf_count": overall_stats.neg_inf_count,
                "overall_pos_inf_count": overall_stats.pos_inf_count,
                "overall_zero_count": float(overall_stats.zero_count),
                "overall_neg_zero_count": float(overall_stats.neg_zero_count),
                "overall_pos_zero_count": float(overall_stats.pos_zero_count)
            }
        return res

    @staticmethod
    def calc_diff_between_two_tensor(first_tensor, second_tensor, tolerance):
        """
        Calculate the difference between the first tensor and the second tensor.

        Args:
            first_tensor (numpy.ndarray): Specify the first tensor.
            second_tensor (numpy.ndarray): Specify the second tensor.
            tolerance (float): The tolerance of difference between the first tensor and the second tensor.
                Its is a percentage. The boundary value is equal to max(abs(min),abs(max)) * tolerance.
                The function of min and max is being used to calculate the min value and max value of
                the result of the first tensor subtract the second tensor. If the absolute value of
                result is less than or equal to boundary value, the result will set to be zero.

        Returns:
            tuple[numpy.ndarray, OverallDiffMetric], numpy.ndarray indicates the value of the first tensor
                subtract the second tensor and set the value to be zero when its less than or equal to tolerance.

        Raises:
            ParamTypeError: If the type of these two tensors is not the numpy.ndarray.
            ParamValueError: If the shape or dtype is not the same of these two tensors or
                the tolerance should be between 0 and 1.
        """
        if not isinstance(first_tensor, np.ndarray):
            raise ParamTypeError('first_tensor', np.ndarray)

        if not isinstance(second_tensor, np.ndarray):
            raise ParamTypeError('second_tensor', np.ndarray)

        if first_tensor.shape != second_tensor.shape:
            raise ParamValueError("the shape: {} of first tensor is not equal to shape: {} of second tensor."
                                  .format(first_tensor.shape, second_tensor.shape))

        if first_tensor.dtype != second_tensor.dtype:
            raise ParamValueError("the dtype: {} of first tensor is not equal to dtype: {} of second tensor."
                                  .format(first_tensor.dtype, second_tensor.dtype))
        # Make sure tolerance is between 0 and 1.
        if tolerance < 0 or tolerance > 1:
            raise ParamValueError("the tolerance should be between 0 and 1, but got {}".format(tolerance))

        diff_tensor = np.subtract(first_tensor, second_tensor)
        stats = TensorUtils.get_statistics_from_tensor(diff_tensor)
        boundary_value = max(abs(stats.max), abs(stats.min)) * tolerance
        is_close = np.isclose(first_tensor, second_tensor, atol=boundary_value, rtol=0)
        result = np.multiply(diff_tensor, ~is_close)
        return result
