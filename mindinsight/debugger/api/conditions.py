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

from mindinsight.debugger.api.debugger_tensor import DebuggerTensor


class ConditionBase(ABC):
    """
    Base class for conditions.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change and/or deletion.

    Note:
        - If multiple checking items is specified for one condition instance,
          a tensor needs to trigger all of them to trigger the watchpoint.
    """

    @property
    def name(self):
        """Get the name for the condition."""
        raise NotImplementedError


class WatchpointHit(ABC):
    """
    Watchpoint hit.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change and/or deletion.

    Note:
        - This class is not meant to be instantiated by user.
        - The instances of this class is immutable.

    Args:
        tensor (DebuggerTensor): The tensor which hits the watchpoint.
        condition (ConditionBase): The ConditionBase object initialized with
            user setting value.
        hit_detail (ConditionBase): The ConditionBase object
            initialized with actual value of the Tensor.
        error_code (str): The code describing error.
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

    def __str__(self):
        if self._error_code:
            return f"Watchpoint {self._condition.name} check failed on " \
                   f"slot {self.tensor.slot} of " \
                   f"node {self._tensor.node.name}. " \
                   f"Error detail: error detail."

        return f"Watchpoint {self._condition.name} triggered on " \
               f"slot {self.tensor.slot} of node {self._tensor.node.name}. " \
               f"The setting for watchpoint is mean_gt=0.2, abs_mean_gt=0.3." \
               f"The actual value of the tensor is " \
               f"mean_gt=0.21, abs_mean_gt=0.35."

    @property
    def error_code(self):
        """Get the error code when checking the watchpoint if there is error."""
        return self._error_code

    @property
    def tensor(self) -> DebuggerTensor:
        """Get the tensor for this watchpoint hit."""
        return self._tensor

    def get_threshold(self):
        """Get the threshold set by user."""
        return self._condition

    def get_hit_detail(self):
        """Get the actual values for the thresholds in the watchpoint."""
        return self._hit_detail


class TensorTooLargeCondition(ConditionBase):
    """
    Tensor too large watchpoint.

    When all specified checking conditions were satisfied, this watchpoint would
    be hit after a check.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change and/or deletion.

    Args:
        abs_mean_gt (float, optional): The threshold for mean of the absolute
            value of the tensor. When the actual value was greater than this
            threshold, this checking condition would be satisfied.
        max_gt (float, optional): The threshold for maximum of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied.
        min_gt (float, optional): The threshold for minimum of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied.
        mean_gt (float, optional): The threshold for mean of the tensor. When
            the actual value was greater than this threshold, this checking
            condition would be satisfied.
    """

    def __init__(self,
                 abs_mean_gt=None, max_gt=None, min_gt=None, mean_gt=None):
        self._abs_mean_gt = abs_mean_gt
        self._max_gt = max_gt
        self._min_gt = min_gt
        self._mean_gt = mean_gt

    @property
    def name(self):
        return "TensorTooLarge"


class Watchpoint:
    """
    Watchpoint applies condition to specified tensors.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change and/or deletion.

    Args:
        tensors (Iterable[DebuggerTensor]): The tensors to check.
        condition (ConditionBase): The condition to apply to tensors.
    """

    def __init__(self, tensors, condition):
        self._tensor = tensors
        self._condition = condition

    def check(self, error_on_no_value=False):
        """
        Check the watchpoint against the tensors.

        Returns:
            Iterable[WatchpointHit], the hits of the watchpoint.
        """
