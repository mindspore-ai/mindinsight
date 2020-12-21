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
"""Validator for optimizer config."""
import math

from marshmallow import Schema, fields, ValidationError, validates, validate, validates_schema

from mindinsight.optimizer.common.enums import TuneMethod, AcquisitionFunctionEnum, GPSupportArgs, \
    HyperParamSource, HyperParamType, TargetGoal, TargetKey, TunableSystemDefinedParams, TargetGroup, \
    HyperParamKey, SystemDefinedTargets
from mindinsight.optimizer.utils.utils import is_param_name_valid

_BOUND_LEN = 2
_NUMBER_ERR_MSG = "Value(s) should be integer or float."
_TYPE_ERR_MSG = "Value should be a %s."
_VALUE_ERR_MSG = "Value should be in %s. Current value is %r."


def _generate_schema_err_msg(err_msg, *args):
    """Organize error messages."""
    if args:
        err_msg = err_msg % args
    return {"invalid": err_msg}


def _generate_err_msg_for_nested_keys(err_msg, *args):
    """Organize error messages for system defined parameters."""
    err_dict = {}
    for name in args[::-1]:
        if not err_dict:
            err_dict.update({name: err_msg})
        else:
            err_dict = {name: err_dict}
    return err_dict


def include_integer(low, high):
    """Check if the range [low, high) includes integer."""
    def _in_range(num, low, high):
        """check if num in [low, high)"""
        return low <= num < high

    if _in_range(math.ceil(low), low, high) or _in_range(math.floor(high), low, high):
        return True
    return False


class TunerSchema(Schema):
    """Schema for tuner."""
    dict_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "dict")

    name = fields.Str(required=True,
                      validate=validate.OneOf(TuneMethod.list_members()),
                      error_messages=_generate_schema_err_msg("Value should be in %s." % TuneMethod.list_members()))
    args = fields.Dict(error_messages=dict_err_msg)

    @validates("args")
    def check_args(self, data):
        """Check args for tuner."""
        data_keys = list(data.keys())
        support_args = GPSupportArgs.list_members()
        if not set(data_keys).issubset(set(support_args)):
            raise ValidationError("Only support setting %s for tuner. "
                                  "Current key(s): %s." % (support_args, data_keys))

        method = data.get(GPSupportArgs.METHOD.value)
        if not isinstance(method, str):
            raise ValidationError("The 'method' type should be str.")
        if method not in AcquisitionFunctionEnum.list_members():
            raise ValidationError("Supported acquisition function must be one of %s. Current value is %r." %
                                  (AcquisitionFunctionEnum.list_members(), method))


class ParameterSchema(Schema):
    """Schema for parameter."""
    number_err_msg = _generate_schema_err_msg(_NUMBER_ERR_MSG)
    list_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "list")
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "string")

    bounds = fields.List(fields.Number(error_messages=number_err_msg), error_messages=list_err_msg)
    choice = fields.List(fields.Number(error_messages=number_err_msg), error_messages=list_err_msg)
    type = fields.Str(error_messages=str_err_msg)
    source = fields.Str(error_messages=str_err_msg)

    @validates("bounds")
    def check_bounds(self, bounds):
        """Check if bounds are valid."""
        if len(bounds) != _BOUND_LEN:
            raise ValidationError("Length of bounds should be %s." % _BOUND_LEN)
        if bounds[1] <= bounds[0]:
            raise ValidationError("The upper bound must be greater than lower bound. "
                                  "The range is [lower_bound, upper_bound).")

    @validates("choice")
    def check_choice(self, choice):
        """Check if choice is valid."""
        if not choice:
            raise ValidationError("It is empty, please fill in at least one value.")

    @validates("type")
    def check_type(self, type_in):
        """Check if type is valid."""
        if type_in not in HyperParamType.list_members():
            raise ValidationError("It should be in %s." % HyperParamType.list_members())

    @validates("source")
    def check_source(self, source):
        """Check if source is valid."""
        if source not in HyperParamSource.list_members():
            raise ValidationError(_VALUE_ERR_MSG % (HyperParamSource.list_members(), source))

    @validates_schema
    def check_combination(self, data, **kwargs):
        """check the combination of parameters."""
        bound_key = HyperParamKey.BOUND.value
        choice_key = HyperParamKey.CHOICE.value
        type_key = HyperParamKey.TYPE.value

        # check bound and type
        bounds = data.get(bound_key)
        param_type = data.get(type_key)
        if bounds is not None:
            if param_type is None:
                raise ValidationError("If %r is specified, the %r should be specified also." %
                                      (HyperParamKey.BOUND.value, HyperParamKey.TYPE.value))
            if param_type == HyperParamType.INT.value and not include_integer(bounds[0], bounds[1]):
                raise ValidationError("No integer in 'bounds', please modify it.")

        # check bound and choice
        if (bound_key in data and choice_key in data) or (bound_key not in data and choice_key not in data):
            raise ValidationError("Only one of [%r, %r] should be specified." %
                                  (bound_key, choice_key))


class TargetSchema(Schema):
    """Schema for target."""
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "string")

    group = fields.Str(error_messages=str_err_msg)
    name = fields.Str(required=True, error_messages=str_err_msg)
    goal = fields.Str(error_messages=str_err_msg)

    @validates("group")
    def check_group(self, group):
        """Check if bounds are valid."""
        if group not in TargetGroup.list_members():
            raise ValidationError(_VALUE_ERR_MSG % (TargetGroup.list_members(), group))

    @validates("goal")
    def check_goal(self, goal):
        """Check if source is valid."""
        if goal not in TargetGoal.list_members():
            raise ValidationError(_VALUE_ERR_MSG % (TargetGoal.list_members(), goal))

    @validates_schema
    def check_combination(self, data, **kwargs):
        """check the combination of parameters."""
        if TargetKey.GROUP.value not in data:
            # if name is in system_defined keys, group will be 'system_defined', else will be 'user_defined'.
            return
        name = data.get(TargetKey.NAME.value)
        group = data.get(TargetKey.GROUP.value)
        if group == TargetGroup.SYSTEM_DEFINED.value and name not in SystemDefinedTargets.list_members():
            raise ValidationError({
                TargetKey.GROUP.value: "This target is not system defined. Current group is %r." % group})


class OptimizerConfig(Schema):
    """Define the search model condition parameter schema."""
    dict_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "dict")
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "string")

    summary_base_dir = fields.Str(required=True, error_messages=str_err_msg)
    command = fields.Str(required=True, error_messages=str_err_msg)
    tuner = fields.Dict(required=True, error_messages=dict_err_msg)
    target = fields.Dict(required=True, error_messages=dict_err_msg)
    parameters = fields.Dict(required=True, error_messages=dict_err_msg)

    def _pre_check_tunable_system_parameters(self, name, value):
        self._check_param_type_tunable_system_parameters(name, value)
        # need to check param type in choice before checking the value
        self._check_param_type_choice_tunable_system_parameters(name, value)
        self._check_param_value_tunable_system_parameters(name, value)

    def _check_param_type_tunable_system_parameters(self, name, value):
        """Check param type for tunable system parameters."""
        param_type = value.get(HyperParamKey.TYPE.value)
        if param_type is None:
            return

        if name == TunableSystemDefinedParams.LEARNING_RATE.value:
            if param_type != HyperParamType.FLOAT.value:
                err_msg = "The value(s) should be float number, " \
                          "please config its type as %r." % HyperParamType.FLOAT.value
                raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.TYPE.value))
        elif param_type != HyperParamType.INT.value:
            err_msg = "The value(s) should be integer, please config its type as %r." % HyperParamType.INT.value
            raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.TYPE.value))

    def _check_param_type_choice_tunable_system_parameters(self, name, value):
        """Check param type in choice for tunable system parameters."""
        choice = value.get(HyperParamKey.CHOICE.value)
        if choice is None:
            return

        if name == TunableSystemDefinedParams.LEARNING_RATE.value:
            if list(filter(lambda x: not isinstance(x, float), choice)):
                err_msg = "The value(s) should be float number."
                raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.CHOICE.value))
        elif list(filter(lambda x: isinstance(x, bool) or not isinstance(x, int), choice)):
            # isinstance(x, int) will return True if x is bool. use 'type(x)' will not pass lint.
            err_msg = "The value(s) should be integer."
            raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.CHOICE.value))

    def _check_param_value_tunable_system_parameters(self, name, value):
        """Check param value for tunable system parameters."""
        bound = value.get(HyperParamKey.BOUND.value)
        choice = value.get(HyperParamKey.CHOICE.value)

        err_msg = "The value(s) should be positive number."
        if bound is not None and bound[0] <= 0:
            raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.BOUND.value))
        if choice is not None and min(choice) <= 0:
            raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.CHOICE.value))

        if name == TunableSystemDefinedParams.LEARNING_RATE.value:
            if bound is not None and bound[1] > 1:
                err_msg = "The upper bound should be less than and equal to 1."
                raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.BOUND.value))
            if choice is not None and max(choice) >= 1:
                err_msg = "The value(s) should be float number less than 1."
                raise ValidationError(_generate_err_msg_for_nested_keys(err_msg, name, HyperParamKey.CHOICE.value))

    @validates("tuner")
    def check_tuner(self, data):
        """Check tuner."""
        err = TunerSchema().validate(data)
        if err:
            raise ValidationError(err)

    @validates("parameters")
    def check_parameters(self, parameters):
        """Check parameters."""
        for name, value in parameters.items():
            if not is_param_name_valid(name):
                raise ValidationError("Parameter name %r is not a valid name, only number(0-9), alphabet(a-z, A-Z) "
                                      "and underscore(_) characters are allowed in name." % name)
            is_system_param = False

            source = value.get(HyperParamKey.SOURCE.value)
            if source in [None, HyperParamSource.SYSTEM_DEFINED.value] and \
                    name in TunableSystemDefinedParams.list_members():
                is_system_param = True

            if is_system_param:
                self._pre_check_tunable_system_parameters(name, value)

            err = ParameterSchema().validate(value)
            if err:
                raise ValidationError({name: err})

            if source is None:
                # if params is in system_defined keys, group will be 'system_defined', else will be 'user_defined'.
                continue

            if source == HyperParamSource.SYSTEM_DEFINED.value and \
                    name not in TunableSystemDefinedParams.list_members():
                raise ValidationError({
                    name: {"source": "This param is not system defined. Current source is %r." % source}})

    @validates("target")
    def check_target(self, target):
        """Check target."""
        err = TargetSchema().validate(target)
        if err:
            raise ValidationError(err)
