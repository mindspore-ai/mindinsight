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

_BOUND_LEN = 2
_NUMBER_ERR_MSG = "Value(s) should be integer or float."
_TYPE_ERR_MSG = "Value type should be %r."
_VALUE_ERR_MSG = "Value should be in %s. Current value is %s."


def _generate_schema_err_msg(err_msg, *args):
    """Organize error messages."""
    if args:
        err_msg = err_msg % args
    return {"invalid": err_msg}


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
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "str")

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

    @validates("type")
    def check_type(self, type_in):
        """Check if type is valid."""
        if type_in not in HyperParamType.list_members():
            raise ValidationError("The type should be in %s." % HyperParamType.list_members())

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
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "str")

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
                TargetKey.GROUP.value: "This target is not system defined. Current group is: %s." % group})


class OptimizerConfig(Schema):
    """Define the search model condition parameter schema."""
    dict_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "dict")
    str_err_msg = _generate_schema_err_msg(_TYPE_ERR_MSG, "str")

    summary_base_dir = fields.Str(required=True, error_messages=str_err_msg)
    command = fields.Str(required=True, error_messages=str_err_msg)
    tuner = fields.Dict(required=True, error_messages=dict_err_msg)
    target = fields.Dict(required=True, error_messages=dict_err_msg)
    parameters = fields.Dict(required=True, error_messages=dict_err_msg)

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
            err = ParameterSchema().validate(value)
            if err:
                raise ValidationError({name: err})

            if HyperParamKey.SOURCE.value not in value:
                # if params is in system_defined keys, group will be 'system_defined', else will be 'user_defined'.
                continue
            source = value.get(HyperParamKey.SOURCE.value)
            if source == HyperParamSource.SYSTEM_DEFINED.value and \
                    name not in TunableSystemDefinedParams.list_members():
                raise ValidationError({
                    name: {"source": "This param is not system defined. Current source is: %s." % source}})

    @validates("target")
    def check_target(self, target):
        """Check target."""
        err = TargetSchema().validate(target)
        if err:
            raise ValidationError(err)
