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
"""
Management of all conditions.

This module is used to register all conditions, as well as their parameters.
This module also provide the available conditions to condition_collections api.
"""
from enum import Enum
from mindinsight.debugger.conditionmgr.log import logger


class ParamNameEnum(Enum):
    """Param names."""
    ABS_MEAN_GT = "abs_mean_gt"
    ABS_MEAN_LT = "abs_mean_lt"
    ABS_MEAN_UPDATE_RATIO_GT = "abs_mean_update_ratio_gt"
    ABS_MEAN_UPDATE_RATIO_LT = "abs_mean_update_ratio_lt"
    ATOL = "atol"
    EQUAL_NAN = "equal_nan"
    EPSILON = "epsilon"
    MAX_GT = "max_gt"
    MAX_LT = "max_lt"
    MIN_GT = "min_gt"
    MIN_LT = "min_lt"
    MEAN_GT = "mean_gt"
    MEAN_LT = "mean_lt"
    MAX_MIN_GT = "max_min_gt"
    MAX_MIN_LT = "max_min_lt"
    PARAM = "param"
    RANGE_START_INCLUSIVE = "range_start_inclusive"
    RANGE_END_INCLUSIVE = "range_end_inclusive"
    RANGE_PERCENTAGE_GT = "range_percentage_gt"
    RANGE_PERCENTAGE_LT = "range_percentage_lt"
    RTOL = "rtol"
    ZERO_PERCENTAGE_GE = "zero_percentage_ge"


class ConditionIdEnum(Enum):
    """Condition ids."""
    WEIGHT_INITIALIZATION = "weight_initialization"
    WEIGHT_OVERFLOW = "weight_overflow"
    WEIGHT_TOO_LARGE = "weight_too_large"
    WEIGHT_TOO_SMALL = "weight_too_small"
    GRADIENT_VANISHING = "gradient_vanishing"
    GRADIENT_TOO_LARGE = "gradient_too_large"
    GRADIENT_EXPLODING = "gradient_exploding"
    TENSOR_OVERFLOW = "tensor_overflow"
    OPERATOR_OVERFLOW = "operator_overflow"
    TENSOR_TOO_LARGE = "tensor_too_large"
    TENSOR_TOO_SMALL = "tensor_too_small"
    TENSOR_ALL_ZERO = "tensor_all_zero"
    WEIGHT_NOT_CHANGED = "weight_not_changed"
    WEIGHT_CHANGE_TOO_LARGE = "weight_change_too_large"
    WEIGHT_CHANGE_TOO_SMALL = "weight_change_too_small"
    ACTIVATION_RANGE = "activation_range"
    TENSOR_RANGE = "tensor_range"


class OptimizePhaseEnum(Enum):
    """Optimize phases."""
    TENSOR_CHECK = 400
    OPERATOR_CHECK = 100
    LOSS_CHECK = 300
    INPUT_DATA_CHECK = 200


class ValueTypeEnum(Enum):
    """Value types."""
    FLOAT64 = 1
    INT64 = 2
    BOOL = 3


class PlatformEnum(Enum):
    """Platform types."""
    GPU = "GPU"
    ASCEND = "Ascend"


class TargetTypeEnum(Enum):
    """Target types."""
    TENSOR = 'tensor'
    ACTIVATION = 'activation'
    GRADIENT = 'gradient'
    PARAMETER = 'parameter'
    WEIGHT = 'weight'


class ParamTypeEnum(Enum):
    """Param types."""
    CHECK_PARAM = "CHECK_PARAM"
    SUPPORT_PARAM = "SUPPORT_PARAM"


class ActivationFuncEnum(Enum):
    """Activation functions."""
    TANH = 'tanh'
    SIGMOID = 'sigmoid'
    RELU = 'relu'
    RELUV2 = 'reluv2'


class ConditionContext:
    """
    The class for condition context.

    Args:
        backend (str): parameter name.
        step (int): the type of value.
        debugger_capability (tuple): whether the param support no assignment.
    """
    def __init__(self, backend, step=0, debugger_capability=(1, 1)):
        self._backend = backend
        self._step = step
        self._debugger_capability = debugger_capability

    @property
    def backend(self):
        """Get backend."""
        return self._backend

    @property
    def step(self):
        """Get _step."""
        return self._step

    @property
    def debugger_capability(self):
        """Get debugger_capability."""
        return self._debugger_capability


class ConditionParameter:
    """
    The class for parameters of conditions.

    Args:
        name (ParamNameEnum): parameter name.
        value_type (ValueTypeEnum): the type of value.
        valid_test_func (func): the function used to test whether the param is valid.
        support_disable (bool): whether the param support no assignment.
        default_value (float): default value.
        visible_on_ui (bool): whether the param visible on ui.
        param_type (ParamTypeEnum): parameters type.
        required_params (list): the list of required parameters.
    """

    def __init__(self, name, value_type: ValueTypeEnum, valid_test_func=None, support_disable=True, default_value=None,
                 visible_on_ui=True, param_type=ParamTypeEnum.CHECK_PARAM, required_params=None):
        self._name = name.value
        self._type = value_type
        self._valid_test_func = valid_test_func
        self._support_disable = support_disable
        self._default_value = default_value
        self._visible_on_ui = visible_on_ui
        self._param_type = param_type.value
        self._required_params = required_params

    @property
    def name(self):
        """Get name of parameter."""
        return self._name

    @property
    def type(self):
        """Get type of parameter."""
        return self._type

    @property
    def support_disable(self):
        """Get support_disable of parameter."""
        return self._support_disable

    @property
    def default_value(self):
        """Get default_value of parameter."""
        return self._default_value

    @property
    def visible_on_ui(self):
        """Get visible_on_ui of parameter."""
        return self._visible_on_ui

    @property
    def param_type(self):
        """Get param_type of parameter."""
        return self._param_type

    @property
    def required_params(self):
        """Get required_param of parameter."""
        return self._required_params

    def is_valid(self, value):
        """Check is the parameter valid."""
        if self._valid_test_func is None:
            return True
        return self._valid_test_func(value)


class Condition:
    """
    The class for parameters of conditions.

    Args:
        condition_id (ConditionIdEnum): condition id.
        abbr (str): the abbreviation of condition id.
        optimize_phase (OptimizePhaseEnum): optimize phase.
        parameters (List[ConditionParameter]): parameters.
        supported_target_type (TargetTypeEnum): the supported target type.
        supported_platforms (tuple[PlatformEnum, PlatformEnum]): the supported platforms.
        minimum_debugger_capability (tuple): the minimum debugger capability required.
        availability_test_func (func): the function used to test whether the condition is available.
    """
    def __init__(self, condition_id, abbr, optimize_phase, parameters, supported_target_type, supported_platforms,
                 minimum_debugger_capability, availability_test_func=None):
        self.id = condition_id.value
        self._abbr = abbr
        self.optimize_phase = optimize_phase
        self._parameters = {
            parameter.name: parameter for parameter in parameters
        }
        self.ordered_parameter_names = [parameter.name for parameter in parameters]
        self._supported_target_type = supported_target_type
        self.supported_platforms = supported_platforms
        self.minimum_debugger_capability = minimum_debugger_capability
        self.availability_test_func = availability_test_func

    def get_parameter_definition(self, name):
        """Return parameter definition by the name"""
        return self._parameters[name]

    def is_available(self, condition_context):
        """Check is the condition available."""
        backend = condition_context.backend
        debugger_capability = condition_context.debugger_capability
        if debugger_capability < self.minimum_debugger_capability:
            logger.debug("The debugger capability is lower than the minimum debugger capability.")
            return False
        if backend not in [platform.value for platform in self.supported_platforms]:
            logger.debug("The condition %s is not supported on the platform.", self.id)
            return False
        if self.availability_test_func is None:
            return True
        return self.availability_test_func(condition_context)

    @property
    def abbr(self):
        """The abbreviation of condition"""
        return self._abbr

    @property
    def names(self):
        """The name of condition"""
        return self._parameters.keys()

    @property
    def parameters(self):
        """The parameters of condition"""
        return self._parameters.values()

    @property
    def supported_target_type(self):
        """The supported target type of condition"""
        return self._supported_target_type


def check_initialization_available(condition_context):
    """Check if initialization is available at this step"""
    if condition_context.step == 0:
        return True
    return False


def check_percentage_param_range(value):
    if 0 <= value <= 100:
        return True
    return False


def check_normal_param_range(value):
    if float("-inf") < value < float("inf"):
        return True
    return False


def check_abs_param_range(value):
    if 0 <= value < float("inf"):
        return True
    return False


def check_positive_param_range(value):
    if 0 < value < float("inf"):
        return True
    return False
