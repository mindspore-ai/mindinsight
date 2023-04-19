# Copyright 2021 Huawei Technologies Co., Ltd
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
# ==============================================================================
"""Watchpoints."""
from abc import ABC
from enum import Enum

from mindinsight.debugger.api.debugger_tensor import DebuggerTensor
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError
from mindinsight.debugger.common.utils import validate_type
from mindinsight.debugger.conditionmgr.condition import ParamNameEnum


class ConditionBase(ABC):
    """
    Base class for watch conditions.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Note:
        - If multiple checking parameters are specified for one condition instance,
          a `WatchpointHit` happens for the parameters that the tensor triggered for the watchpoint.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
            >>> from mindinsight.debugger import DumpAnalyzer
            >>> from mindinsight.debugger import (TensorTooLargeCondition,
            ...                                   Watchpoint)
            >>>
            >>> def test_condition_base():
            ...     my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
            ...     tensors = my_run.select_tensors(query_string="Conv2D-op13")
            ...     watchpoint = Watchpoint(tensors=tensors,
            ...                             condition=TensorTooLargeCondition(abs_mean_gt=0.0, max_gt=0.0))
            ...     hit = list(my_run.check_watchpoints(watchpoints=[watchpoint]))[0]
            ...     # print(hit.get_hit_detail())
            ...     # the print result is as follows
            ...     # The setting for watchpoint is abs_mean_gt = 0.0, max_gt = 0.0.
            ...     # The actual value of the tensor is abs_mean_gt = 0.06592023578438996, max_gt = 0.449951171875.
            ...     watchpoint = Watchpoint(tensors=tensors,
            ...                             condition=TensorTooLargeCondition(abs_mean_gt=0.0, max_gt=1.0))
            ...     # the check_watchpoints function start a new process needs to be called through the main entry
            ...     hit = list(my_run.check_watchpoints(watchpoints=[watchpoint]))[0]
            ...     # print(hit.get_hit_detail())
            ...     # the print result is as follows
            ...     # The setting for watchpoint is abs_mean_gt = 0.0.
            ...     # The actual value of the tensor is abs_mean_gt = 0.06592023578438996.
            ...
            >>> if __name__ == "__main__":
            ...     test_condition_base()
            ...
    """

    @property
    def name(self):
        """
        Get the id for watch condition.

        Returns:
            str, the name of the watch condition.
        """
        raise NotImplementedError

    @property
    def condition_id(self):
        """
        Get the name for the watch condition Id.

        Returns:
            int, the id of the watch condition.
        """
        raise NotImplementedError

    @property
    def param_dict(self):
        """
        Get the parameters list.

        Returns:
            dict, the parameter dict of the watch condition.
        """
        return {}

    def __str__(self):
        return str(self.param_dict)


class WatchpointHit(ABC):
    """
    Watchpoint hit.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Note:
        - This class is not meant to be instantiated by user.
        - The instances of this class is immutable.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
        >>> from mindinsight.debugger import DumpAnalyzer
        >>> from mindinsight.debugger import TensorTooLargeCondition, Watchpoint
        >>>
        >>> def test_watch_point_hit():
        ...     my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
        ...     tensor_list = my_run.select_tensors(
        ...                                         query_string="Conv",
        ...                                         use_regex=True,
        ...                                         iterations=[0],
        ...                                         ranks=[0],
        ...                                         slots=[0]
        ...                                         )
        ...     watchpoint = Watchpoint(tensors=tensor_list,
        ...                             condition=TensorTooLargeCondition(abs_mean_gt=0.0))
        ...     # the check_watchpoints function start a new process needs to be called through the main entry
        ...     hits = my_run.check_watchpoints(watchpoints=[watchpoint])
        ...     hit = list(hits)[0]
        ...     # print(str(hit))
        ...     # the print result is as follows
        ...     # Watchpoint TensorTooLarge triggered on tensor:
        ...     # rank: 0
        ...     # graph_name: kernel_graph_0
        ...     # node_name: Default/network-WithLossCell/_backbone-AlexNet/conv1-Conv2d/Cast-op7
        ...     # slot: 0
        ...     # iteration: 0
        ...     # Threshold: {'abs_mean_gt': 0.0}
        ...     # Hit detail: The setting for watchpoint is abs_mean_gt = 0.0.
        ...     # The actual value of the tensor is abs_mean_gt = 0.007956420533235841.
        ...     # print(hit.error_code)
        ...     # the print result is as follows
        ...     # 0
        ...     # print(hit.tensor)
        ...     # the print result is as follows
        ...     # rank: 0
        ...     # graph_name: kernel_graph_0
        ...     # node_name: Default/network-WithLossCell/_backbone-AlexNet/conv1-Conv2d/Cast-op7
        ...     # slot: 0
        ...     # iteration: 0
        ...     # print(hit.get_hit_detail())
        ...     # the print result is as follows
        ...     # The setting for watchpoint is abs_mean_gt = 0.0.
        ...     # The actual value of the tensor is abs_mean_gt = 0.007956420533235841.
        ...
        >>> if __name__ == "__main__":
        ...     test_watch_point_hit()
        ...
    """

    @property
    def error_code(self):
        """
        Get the error code when checking the watchpoint if there is error.

        Returns:
            int, the error number.
        """
        raise NotImplementedError

    @property
    def error_msg(self):
        """
        Get the error msg when checking the watchpoint if there is error.

        Returns:
            list[str], the error message list.
        """
        raise NotImplementedError

    @property
    def tensor(self) -> DebuggerTensor:
        """
        Get the tensor for this watchpoint hit.

        Returns:
            DebuggerTensor, the triggered tensor.
        """
        raise NotImplementedError

    def get_threshold(self):
        """
        Get the condition set by user.

        Returns:
            ConditionBase, the condition with user threshold.
        """
        raise NotImplementedError

    def get_hit_detail(self):
        """
        Get the corresponding watch condition，including the actual values.
        For example, if the corresponding watch condition is `TensorTooLargeCondition(max_gt=None)` ,
        watching whether the max value of the tensor greater than 0, the `get_hit_detail` return
        a `TensorTooLargeCondition` object including the max value of the tensor.
        If error_code is not zero, None will be returned.

        Returns:
            Union[ConditionBase, None], the condition with hit detail, If error_code is not zero,
            None will be returned.
        """
        raise NotImplementedError


class WatchpointHitImpl(WatchpointHit):
    """
    Watchpoint hit.

    Args:
        tensor (DebuggerTensor): The tensor which hits the watchpoint.
        condition (ConditionBase): The ConditionBase object initialized with
            user setting value.
        hit_detail (ConditionBase): The ConditionBase object
            initialized with actual value of the Tensor.
        error_code (int): The code describing error.
    """

    def __init__(self,
                 tensor: DebuggerTensor,
                 condition: ConditionBase,
                 hit_detail: ConditionBase,
                 error_code):
        self._tensor = tensor
        self._condition = condition
        self._error_code = error_code
        self._hit_detail = hit_detail

    @property
    def error_code(self):
        """
        Get the error code when checking the watchpoint if there is error.

        Returns:
            int, the error number.
        """
        return self._error_code

    @property
    def error_msg(self):
        """
        Get the error msg when checking the watchpoint if there is error.

        Returns:
            list[str], the error message list.
        """
        error_code = self._error_code
        all_error_list = [
            "Tensor contains NaN.",
            "A tensor contains +/-INF.",
            "The previous step value cannot be found.",
            "The tensor size exceeds the memory limit.",
            "Graph history file is not available.",
            "Tensor has no value."
        ]
        error_list = []
        for i, error_str in enumerate(all_error_list):
            error = (error_code >> i) & 1
            if error == 1:
                error_list.append(error_str)

        return error_list

    @property
    def tensor(self) -> DebuggerTensor:
        """Get the tensor for this watchpoint hit."""
        return self._tensor

    def get_threshold(self):
        """Get the threshold set by user."""
        return self._condition

    def get_hit_detail(self):
        """
        Get the actual values for the thresholds in the watchpoint.
        If error_code is not zero or None, None will be returned.
        """
        if self._error_code:
            return None
        return self._hit_detail

    def __str__(self):
        if self._error_code:
            msg = f"Watchpoint {self._condition.name} check failed on tensor:\n" \
                  f"{str(self.tensor)}" \
                  f"Threshold: {self.get_threshold()}\n" \
                  f"Error detail: {self.error_msg}"
            return msg
        msg = f"Watchpoint {self._condition.name} triggered on tensor:\n" \
              f"{str(self.tensor)}" \
              f"Threshold: {self.get_threshold()}\n" \
              f"Hit detail: {str(self._hit_detail)}"
        return msg


class HitDetail(ConditionBase):
    """Hit Detail."""

    def __init__(self, param_list, condition):
        self._param_list = param_list
        self._condition = condition

    @property
    def name(self):
        """Get the name for the condition."""
        return self._condition.name

    @property
    def condition_id(self):
        """Get the name for the condition Id."""
        return self._condition.condition_id

    @property
    def param_dict(self):
        """Get the parameters list."""
        return self._param_list

    def __str__(self):
        show_actual_value = bool(self._condition.param_dict)
        if self._condition.condition_id == WatchpointConditionId.UNCHANGED_TENSOR.value:
            show_actual_value = False
        # list of the parameters with disabled = False and hit = 1
        hit_param_list = []
        for param in self._param_list:
            if not param.disabled and param.hit:
                hit_param_list.append(param)

        result = ""
        param_size = len(hit_param_list)
        if show_actual_value and hit_param_list:
            setting_detail = "The setting for watchpoint is "
            value_detail = " The actual value of the tensor is "
            for idx, param in enumerate(hit_param_list):
                setting_detail += f"{param.name} = {param.value}"
                value_detail += f"{param.name} = {param.actual_value}"
                if idx == param_size - 1:
                    setting_detail += "."
                    value_detail += "."
                else:
                    setting_detail += ", "
                    value_detail += ", "
            result = setting_detail + value_detail

        if not result:
            result = "None."
        return result


class TensorTooLargeCondition(ConditionBase):
    """
    Watch contion for tensor value too large. At least one parameter should be specified.

    If multiple checking parameters are specified, a `WatchpointHit` happens for the parameters
    that the tensor triggered for the watchpoint.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        abs_mean_gt (float, optional): The threshold for mean of the absolute
            value of the tensor. When the actual value was greater than this
            threshold, this checking condition would be satisfied. Default: ``None``.
        max_gt (float, optional): The threshold for maximum of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied. Default: ``None``.
        min_gt (float, optional): The threshold for minimum of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied. Default: ``None``.
        mean_gt (float, optional): The threshold for mean of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied. Default: ``None``.

    Examples:
        >>> from mindinsight.debugger import TensorTooLargeCondition
        >>> my_condition = TensorTooLargeCondition(abs_mean_gt=0.0)
        >>> print(my_condition.name)
        TensorTooLarge
    """

    def __init__(self,
                 abs_mean_gt=None, max_gt=None, min_gt=None, mean_gt=None):
        self._abs_mean_gt = abs_mean_gt
        self._max_gt = max_gt
        self._min_gt = min_gt
        self._mean_gt = mean_gt
        self._param_dict = self._get_param_dict()

    @property
    def name(self):
        return "TensorTooLarge"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_TOO_LARGE.value

    @property
    def param_dict(self):
        return self._param_dict

    def _get_param_dict(self):
        """Get normalized param dict."""
        param_dict = {}
        if self._abs_mean_gt is not None:
            validate_type(self._abs_mean_gt, 'abs_mean_gt', [int, float], 'float')
            param_dict[ParamNameEnum.ABS_MEAN_GT.value] = float(self._abs_mean_gt)
        if self._max_gt is not None:
            validate_type(self._max_gt, 'max_gt', [int, float], 'float')
            param_dict[ParamNameEnum.MAX_GT.value] = float(self._max_gt)
        if self._min_gt is not None:
            validate_type(self._min_gt, 'min_gt', [int, float], 'float')
            param_dict[ParamNameEnum.MIN_GT.value] = float(self._min_gt)
        if self._mean_gt is not None:
            validate_type(self._mean_gt, 'mean_gt', [int, float], 'float')
            param_dict[ParamNameEnum.MEAN_GT.value] = float(self._mean_gt)
        if not param_dict:
            msg = "Please specify at least one of the parameters for TensorTooLargeCondition."
            raise DebuggerParamValueError(msg)
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.ABS_MEAN_GT.value,
            ParamNameEnum.MAX_GT.value,
            ParamNameEnum.MIN_GT.value,
            ParamNameEnum.MEAN_GT.value
        ]
        return names


class TensorTooSmallCondition(ConditionBase):
    """
    Watch contion for tensor value too small. At least one parameter should be specified.

    If multiple checking parameters are specified, a `WatchpointHit` happens for the parameters
    that the tensor triggered for the watchpoint.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        abs_mean_lt (float, optional): The threshold for mean of the absolute
            value of the tensor. When the actual value was less than this
            threshold, this checking condition would be satisfied. Default: ``None``.
        max_lt (float, optional): The threshold for maximum of the tensor. When
            the actual value was less than this threshold, this checking
            condition would be satisfied. Default: ``None``.
        min_lt (float, optional): The threshold for minimum of the tensor. When
            the actual value was less than this threshold, this checking
            condition would be satisfied. Default: ``None``.
        mean_lt (float, optional): The threshold for mean of the tensor. When
            the actual value was less than this threshold, this checking
            condition would be satisfied. Default: ``None``.

    Examples:
        >>> from mindinsight.debugger import TensorTooSmallCondition
        >>> my_condition = TensorTooSmallCondition(abs_mean_lt=0.2)
        >>> print(my_condition.name)
        TensorTooSmall
    """

    def __init__(self,
                 abs_mean_lt=None, max_lt=None, min_lt=None, mean_lt=None):
        self._abs_mean_lt = abs_mean_lt
        self._max_lt = max_lt
        self._min_lt = min_lt
        self._mean_lt = mean_lt
        self._param_dict = self._get_param_dict()

    @property
    def name(self):
        return "TensorTooSmall"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_TOO_SMALL.value

    @property
    def param_dict(self):
        return self._param_dict

    def _get_param_dict(self):
        """Get normalized param dict."""
        param_dict = {}
        if self._abs_mean_lt is not None:
            validate_type(self._abs_mean_lt, 'abs_mean_lt', [int, float], 'float')
            param_dict[ParamNameEnum.ABS_MEAN_LT.value] = float(self._abs_mean_lt)
        if self._max_lt is not None:
            validate_type(self._max_lt, 'max_lt', [int, float], 'float')
            param_dict[ParamNameEnum.MAX_LT.value] = float(self._max_lt)
        if self._min_lt is not None:
            validate_type(self._min_lt, 'min_lt', [int, float], 'float')
            param_dict[ParamNameEnum.MIN_LT.value] = float(self._min_lt)
        if self._mean_lt is not None:
            validate_type(self._mean_lt, 'mean_lt', [int, float], 'float')
            param_dict[ParamNameEnum.MEAN_LT.value] = float(self._mean_lt)
        if not param_dict:
            msg = "Please specify at least one of the parameters for TensorTooSmallCondition."
            raise DebuggerParamValueError(msg)
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.ABS_MEAN_LT.value,
            ParamNameEnum.MAX_LT.value,
            ParamNameEnum.MIN_LT.value,
            ParamNameEnum.MEAN_LT.value
        ]
        return names


class TensorRangeCondition(ConditionBase):
    """
    Watch condition for tensor value range.

    Set a threshold to check the tensor value range. There are four options:
    `range_percentage_lt` , `range_percentage_gt` , `max_min_lt` and `max_min_gt` .
    At least one of the four options should be specified.
    If the threshold is set to one of the first two options,
    both `range_start_inclusive` and `range_end_inclusive` must be set.
    If multiple checking parameters are specified, a `WatchpointHit` happens for the parameters
    that the tensor triggered for the watchpoint.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        range_start_inclusive (float, optional): The start of the specified range. Default: ``None``.
        range_end_inclusive (float, optional): The end of the specified range. Default: ``None``.
        range_percentage_lt (float, optional): The threshold for the percentage of the tensor
            in the range `[range_start_inclusive, range_end_inclusive]` . The checking condition
            will be satisfied when the percentage of the tensor in the specified range is less than this value.
            Default: ``None``.
        range_percentage_gt (float, optional): The threshold for the percentage of the tensor
            in the range `[range_start_inclusive, range_end_inclusive]` . The checking condition
            will be satisfied when the percentage of the tensor in the specified range is greater than this value.
            Default: ``None``.
        max_min_lt (float, optional): Lowwer threshold for the difference
            between the maximum and minimum values of a tensor. Default: ``None``.
        max_min_gt (float, optional): Upper threshold for the difference
            between the maximum and minimum values of a tensor. Default: ``None``.

    Examples:
        >>> from mindinsight.debugger import TensorRangeCondition
        >>> my_condition = TensorRangeCondition(max_min_gt=0.05)
        >>> print(my_condition.name)
        TensorRange
    """

    def __init__(self,
                 range_start_inclusive=None, range_end_inclusive=None, range_percentage_lt=None,
                 range_percentage_gt=None, max_min_lt=None, max_min_gt=None):
        self._range_start_inclusive = range_start_inclusive
        self._range_end_inclusive = range_end_inclusive
        self._range_percentage_lt = range_percentage_lt
        self._range_percentage_gt = range_percentage_gt
        self._max_min_lt = max_min_lt
        self._max_min_gt = max_min_gt
        self._param_dict = self._get_param_dict()

    @property
    def name(self):
        return "TensorRange"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_RANGE.value

    @property
    def param_dict(self):
        return self._param_dict

    def _get_param_dict(self):
        """Get normalized param dict."""
        param_dict = {}
        if self._range_start_inclusive is not None:
            validate_type(self._range_start_inclusive, 'range_start_inclusive', [int, float], 'float')
            param_dict[ParamNameEnum.RANGE_START_INCLUSIVE.value] = float(self._range_start_inclusive)
        if self._range_end_inclusive is not None:
            validate_type(self._range_end_inclusive, 'range_end_inclusive', [int, float], 'float')
            param_dict[ParamNameEnum.RANGE_END_INCLUSIVE.value] = float(self._range_end_inclusive)
        if self._range_percentage_lt is not None:
            validate_type(self._range_percentage_lt, 'range_percentage_lt', [int, float], 'float')
            param_dict[ParamNameEnum.RANGE_PERCENTAGE_LT.value] = float(self._range_percentage_lt)
        if self._range_percentage_gt is not None:
            validate_type(self._range_percentage_gt, 'range_range_percentage_gt', [int, float], 'float')
            param_dict[ParamNameEnum.RANGE_PERCENTAGE_GT.value] = float(self._range_percentage_gt)
        if self._max_min_lt is not None:
            validate_type(self._max_min_lt, 'max_min_lt', [int, float], 'float')
            param_dict[ParamNameEnum.MAX_MIN_LT.value] = float(self._max_min_lt)
        if self._max_min_gt is not None:
            validate_type(self._max_min_gt, 'max_min_gt', [int, float], 'float')
            param_dict[ParamNameEnum.MAX_MIN_GT.value] = float(self._max_min_gt)
        if not self._has_threshold_param(param_dict):
            msg = "Please specify at least one of the parameters " \
                  "[range_percentage_lt, range_percentage_gt, max_min_lt, max_min_gt] " \
                  "for TensorRangeCondition."
            raise DebuggerParamValueError(msg)
        # check supported parameter
        if (ParamNameEnum.RANGE_PERCENTAGE_LT.value in param_dict.keys() or
                ParamNameEnum.RANGE_PERCENTAGE_GT.value in param_dict.keys()):
            if (ParamNameEnum.RANGE_START_INCLUSIVE.value not in param_dict.keys() or
                    ParamNameEnum.RANGE_END_INCLUSIVE.value not in param_dict.keys()):
                msg = ("Please specify both range_start_inclusive and "
                       "range_end_inclusive parameters for TensorRangeCondition.")
                raise DebuggerParamValueError(msg)
        return param_dict

    @staticmethod
    def _has_threshold_param(param_dict):
        """Check if threshold parameter is set."""
        threshold_param_name = [
            ParamNameEnum.RANGE_PERCENTAGE_LT.value,
            ParamNameEnum.RANGE_PERCENTAGE_GT.value,
            ParamNameEnum.MAX_MIN_LT.value,
            ParamNameEnum.MAX_MIN_GT.value
        ]
        for param_name in threshold_param_name:
            if param_name in param_dict:
                return True
        return False

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.RANGE_START_INCLUSIVE.value,
            ParamNameEnum.RANGE_END_INCLUSIVE.value,
            ParamNameEnum.RANGE_PERCENTAGE_LT.value,
            ParamNameEnum.RANGE_PERCENTAGE_GT.value,
            ParamNameEnum.MAX_MIN_LT.value,
            ParamNameEnum.MAX_MIN_GT.value
        ]
        return names


class TensorOverflowCondition(ConditionBase):
    """
    Watch condition for tensor overflow.

    Tensor overflow whatchpoint checks for `inf` and `nan` tensors.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Examples:
        >>> from mindinsight.debugger import TensorOverflowCondition
        >>> my_condition = TensorOverflowCondition()
        >>> print(my_condition.name)
        TensorOverflow
    """

    def __init__(self):
        pass

    @property
    def name(self):
        return "TensorOverflow"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_OVERFLOW.value

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        return []


class OperatorOverflowCondition(ConditionBase):
    """
    Operator overflow watch condition.

    Operator overflow whatchpoint checks whether overflow occurs during operator computation.
    Only Ascend AI processor is supported.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Examples:
        >>> from mindinsight.debugger import OperatorOverflowCondition
        >>> my_condition = OperatorOverflowCondition()
        >>> print(my_condition.name)
        OperatorOverflow
    """

    def __init__(self):
        pass

    @property
    def name(self):
        return "OperatorOverflow"

    @property
    def condition_id(self):
        return WatchpointConditionId.OPERATOR_OVERFLOW.value

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        return []


class TensorAllZeroCondition(ConditionBase):
    """
    Watch condition for tensor value is all zero .

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        zero_percentage_ge (float): The threshold to check if the percentage of
            zero tensor values are greater than this value.

    Examples:
        >>> from mindinsight.debugger import TensorAllZeroCondition
        >>> my_condition = TensorAllZeroCondition(zero_percentage_ge=0.0)
        >>> print(my_condition.name)
        TensorAllZero
    """

    def __init__(self, zero_percentage_ge):
        validate_type(zero_percentage_ge, 'zero_percentage_ge', [int, float], 'float')
        self._zero_percentage_ge = float(zero_percentage_ge)

    @property
    def name(self):
        return "TensorAllZero"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_ALL_ZERO.value

    @property
    def param_dict(self):
        param_dict = {ParamNameEnum.ZERO_PERCENTAGE_GE.value: self._zero_percentage_ge}
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        return [ParamNameEnum.ZERO_PERCENTAGE_GE.value]


class TensorUnchangedCondition(ConditionBase):
    r"""
    Watch condition for tensor value unchanged.

    Check allclose function on previous and current tensor. Only when every element in tensor
    satisfies the equation :math:`|element\_in\_current\_tensor - element\_in\_previous\_tensor|
    \leq atol + rtol\times |previous\_tensor|` , this watchpoint will be hit.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        rtol (float, optional): The relative tolerance parameter. Default: ``1e-5``.
        atol (float, optional): The absolute tolerance parameter. Default: ``1e-8``.

    Examples:
        >>> from mindinsight.debugger import TensorUnchangedCondition
        >>> my_condition = TensorUnchangedCondition(rtol=1000.0)
        >>> print(my_condition.name)
        TensorUnchanged
    """

    def __init__(self, rtol=1e-5, atol=1e-8):
        validate_type(rtol, 'rtol', [float, int], 'float or int')
        validate_type(atol, 'atol', [float, int], 'float or int')
        self._rtol = float(rtol)
        self._atol = float(atol)

    @property
    def name(self):
        return "TensorUnchanged"

    @property
    def condition_id(self):
        return WatchpointConditionId.UNCHANGED_TENSOR.value

    @property
    def param_dict(self):
        param_dict = {
            ParamNameEnum.RTOL.value: self._rtol,
            ParamNameEnum.ATOL.value: self._atol}
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.RTOL.value,
            ParamNameEnum.ATOL.value,
            ParamNameEnum.EQUAL_NAN.value
        ]
        return names


class TensorChangeBelowThresholdCondition(ConditionBase):
    r"""
    Watch condition for tensor changing below threshold.

    When the tensor changing satisfies equation :math:`\frac {abs\_mean(current\_tensor
    - previous\_tensor)} {abs\_mean(previous\_tensor)} + epsilon < mean\_update\_ratio\_lt` ,
    the watchpoint would be hit.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        abs_mean_update_ratio_lt (float): The threshold value for mean update ration.
            If the mean update ratio is less that this value the watchpoint will be triggered.
        epsilon (float, optional): Epsilon value. Default: ``1e-9``.

    Examples:
        >>> from mindinsight.debugger import TensorChangeBelowThresholdCondition
        >>> my_condition = TensorChangeBelowThresholdCondition(abs_mean_update_ratio_lt=2.0)
        >>> print(my_condition.name)
        TensorChangeBelowThreshold
    """

    def __init__(self, abs_mean_update_ratio_lt, epsilon=1e-9):
        validate_type(abs_mean_update_ratio_lt, 'abs_mean_update_ratio_lt', [float, int], 'float')
        validate_type(epsilon, 'epsilon', [float, int], 'float')
        self._abs_mean_update_ratio_lt = float(abs_mean_update_ratio_lt)
        self._epsilon = float(epsilon)

    @property
    def name(self):
        return "TensorChangeBelowThreshold"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_CHANGE_TOO_SMALL.value

    @property
    def param_dict(self):
        param_dict = {
            ParamNameEnum.ABS_MEAN_UPDATE_RATIO_LT.value: self._abs_mean_update_ratio_lt,
            ParamNameEnum.EPSILON.value: self._epsilon
        }
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.ABS_MEAN_UPDATE_RATIO_LT.value,
            ParamNameEnum.EPSILON.value
        ]
        return names


class TensorChangeAboveThresholdCondition(ConditionBase):
    r"""
    Watch condition for tensor changing above threshold.

    When the tensor changing satisfies equation :math:`\frac {abs\_mean(current\_tensor -
    previous\_tensor)} {abs\_mean(previous\_tensor)} + epsilon > mean\_update\_ratio\_lt` ,
    the watchpoint would be hit.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        abs_mean_update_ratio_gt (float): The threshold value for mean update ratio,
            if the mean update ratio is greater than this value the watchpoint will be triggered.
        epsilon (float, optional): Epsilon value. Default: ``1e-9``.

    Examples:
        >>> from mindinsight.debugger import TensorChangeAboveThresholdCondition
        >>> my_condition = TensorChangeAboveThresholdCondition(abs_mean_update_ratio_gt=0.0)
        >>> print(my_condition.name)
        TensorChangeAboveThreshold
    """

    def __init__(self, abs_mean_update_ratio_gt, epsilon=1e-9):
        validate_type(abs_mean_update_ratio_gt, 'abs_mean_update_ratio_gt', [float, int], 'float')
        validate_type(epsilon, 'epsilon', [float, int], 'float')
        self._abs_mean_update_ratio_gt = float(abs_mean_update_ratio_gt)
        self._epsilon = float(epsilon)

    @property
    def name(self):
        return "TensorChangeAboveThreshold"

    @property
    def condition_id(self):
        return WatchpointConditionId.TENSOR_CHANGE_TOO_LARGE.value

    @property
    def param_dict(self):
        param_dict = {
            ParamNameEnum.ABS_MEAN_UPDATE_RATIO_GT.value: self._abs_mean_update_ratio_gt,
            ParamNameEnum.EPSILON.value: self._epsilon
        }
        return param_dict

    @property
    def param_names(self):
        """
        Return the list of parameter names.

        Returns:
            list[str], the parameter names.
        """
        names = [
            ParamNameEnum.ABS_MEAN_UPDATE_RATIO_GT.value,
            ParamNameEnum.EPSILON.value
        ]
        return names


class Watchpoint:
    """
    Watchpoint applies condition to specified tensors.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or delete.

    Args:
        tensors (Iterable[DebuggerTensor]): The tensors to check.
        condition (ConditionBase): The watch condition to apply to tensors.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
        >>> from mindinsight.debugger import DumpAnalyzer
        >>> from mindinsight.debugger import TensorTooLargeCondition, Watchpoint
        >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
        >>> tensor_list = my_run.select_tensors(
        ...                                     query_string="Conv",
        ...                                     use_regex=True,
        ...                                     iterations=[0],
        ...                                     ranks=[0],
        ...                                     slots=[0]
        ...                                     )
        >>> watchpoint = Watchpoint(tensors=tensor_list,
        ...                         condition=TensorTooLargeCondition(abs_mean_gt=0.0))
        >>> tensor = list(watchpoint.tensors)[0]
        >>> print(tensor.node.name)
        Default/network-WithLossCell/_backbone-AlexNet/conv1-Conv2d/Cast-op7
        >>> print(watchpoint.condition.name)
        TensorTooLarge
    """

    def __init__(self, tensors, condition):
        validate_tensor_list(tensors, 'tensors')
        validate_type(condition, 'condition', ConditionBase, 'ConditionBase')
        self._tensors = tensors
        self._condition = condition

    @property
    def tensors(self):
        """
        Get tensors to check.

        Returns:
            Iterable[DebuggerTensor], the tensors to check.
        """
        return self._tensors

    @property
    def condition(self):
        """
        Get the watch condition to apply to tensors.

        Returns:
            ConditionBase, the watch condition to apply to tensors.
        """
        return self._condition


class WatchpointHandle:
    """Watchpoint handle."""

    def __init__(self, watchpoint_id, watchpoint):
        validate_type(watchpoint, 'watchpoint', Watchpoint, 'Watchpoint')
        self.watchpoint_id = watchpoint_id
        self.condition = watchpoint.condition
        self.sorted_tensors = self._organize_tensor(watchpoint.tensors)
        self.tensors = watchpoint.tensors

    @staticmethod
    def _get_value(default_map, key, default_value):
        """Get key in default map."""
        value = default_map.get(key)
        if value is None:
            value = default_value
            default_map[key] = value
        return value

    def _organize_tensor(self, tensors):
        """Sort out the tensor and remove the duplication."""
        sorted_tensor = {}
        for tensor in tensors:
            validate_type(tensor, 'tensors', DebuggerTensor, 'List[DebuggerTensor]')
            node_map = self._get_value(sorted_tensor, tensor.iteration, {})
            slot_map = self._get_value(node_map, tensor.node.unique_id, {
                'node': tensor.node,
                'slot_map': {}
            }).get('slot_map')
            slot_map[tensor.slot] = tensor
        return sorted_tensor

    def get_iterations(self):
        """Get iterations to be check in this watchpoint."""
        return list(self.sorted_tensors.keys())

    def need_check(self, tensor):
        """Check if the tensor need to be checked."""
        slot_map = self.sorted_tensors.get(tensor.iteration,
                                           {}).get(tensor.node.unique_id, {}).get('slot_map')
        if slot_map.get(tensor.slot) is not None:
            return True
        return False

    def get_check_nodes(self, iteration):
        """Get check nodes."""
        if iteration is None:
            return {}
        check_nodes = {}
        for node_info in self.sorted_tensors.get(iteration, {}).values():
            node = node_info.get('node')
            node_name = node.full_name_with_graph
            check_node = self._get_value(check_nodes, node_name, {
                "rank_id": [node.rank],
                "is_output": True,
                "root_graph_id": [node.root_graph_id]
            })
            if node.rank not in check_node.get('rank_id'):
                check_node["rank_id"].append(node.rank)
        return check_nodes

    def add_watchpoint(self, iteration, debugger_engine):
        """
        Add watchpoint for the selected iteration.
        """
        check_nodes = self.get_check_nodes(iteration)
        # check if watchpoint must be added for the current iteration
        if check_nodes:
            params = self._get_param_list(debugger_engine.dbg_services_module.Parameter)
            debugger_engine.dbg_service.add_watchpoint(
                watchpoint_id=self.watchpoint_id,
                watch_condition=self.condition.condition_id,
                check_node_list=check_nodes,
                parameter_list=params
            )

    def _get_param_list(self, parameter_class):
        """Get param list."""
        params = []
        set_params = self.condition.param_dict
        for param_name in self.condition.param_names:
            set_value = set_params.get(param_name)
            if set_value is not None:
                param = parameter_class(name=param_name, disabled=False, value=set_value)
            else:
                param = parameter_class(name=param_name, disabled=True, value=0.0)
            params.append(param)
        return params

    def watchpoint_hit_on_no_value(self, iteration):
        """
        Returns list of WatchpointHit if tensors' npy files are missing,
        when error_on_no_value =True
        """
        no_value_hit_list = []
        node_map = self.sorted_tensors.get(iteration)
        if not node_map:
            return no_value_hit_list
        for node_info in node_map.values():
            for tensor in node_info.get('slot_map', {}).values():
                if tensor.has_value() is False:
                    hit_params = []
                    hit_detail = HitDetail(hit_params, self.condition)
                    # 32 means there is no value found
                    error_no_value_code = 32
                    no_value_hit = WatchpointHitImpl(tensor=tensor,
                                                     condition=self.condition,
                                                     hit_detail=hit_detail,
                                                     error_code=error_no_value_code)
                    no_value_hit_list.append(no_value_hit)
        return no_value_hit_list


class WatchpointConditionId(Enum):
    """Watchpoint condition ID."""
    OPERATOR_OVERFLOW = 2
    TENSOR_OVERFLOW = 13
    INITIAL_WEIGHT = 14
    TENSOR_TOO_LARGE = 15
    TENSOR_TOO_SMALL = 16
    TENSOR_ALL_ZERO = 17
    TENSOR_CHANGE_TOO_LARGE = 18
    TENSOR_CHANGE_TOO_SMALL = 19
    UNCHANGED_TENSOR = 20
    TENSOR_RANGE = 21


def validate_tensor_list(param, param_name):
    """Validate list."""
    if not isinstance(param, list):
        raise DebuggerParamTypeError(f"The type of {param_name} should be list of DebuggerTensor. "
                                     f"But the actual type is {type(param)}")
    for i, value in enumerate(param):
        if not isinstance(value, DebuggerTensor):
            raise DebuggerParamTypeError(f"The type of {param_name} should be list of DebuggerTensor. "
                                         f"But the {i} value is {type(value)}.")
