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
Condition list.

This module provide the detail conditions list.
"""
from mindinsight.debugger.conditionmgr.condition import Condition
from mindinsight.debugger.conditionmgr.condition import OptimizePhaseEnum
from mindinsight.debugger.conditionmgr.condition import ConditionParameter
from mindinsight.debugger.conditionmgr.condition import ValueTypeEnum
from mindinsight.debugger.conditionmgr.condition import TargetTypeEnum
from mindinsight.debugger.conditionmgr.condition import PlatformEnum
from mindinsight.debugger.conditionmgr.condition import ParamTypeEnum
from mindinsight.debugger.conditionmgr.condition import ConditionIdEnum
from mindinsight.debugger.conditionmgr.condition import ParamNameEnum
from mindinsight.debugger.conditionmgr.condition import check_initialization_available
from mindinsight.debugger.conditionmgr.condition import check_normal_param_range
from mindinsight.debugger.conditionmgr.condition import check_percentage_param_range
from mindinsight.debugger.conditionmgr.condition import check_abs_param_range, check_positive_param_range


CONDITION_LIST = [
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_INITIALIZATION,
        abbr="WI",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_initialization
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ZERO_PERCENTAGE_GE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                default_value=100
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1),
        availability_test_func=check_initialization_available
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_OVERFLOW,
        abbr="WO",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_TOO_LARGE,
        abbr="WL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_TOO_SMALL,
        abbr="WS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.GRADIENT_VANISHING,
        abbr="GV",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.GRADIENT_TOO_LARGE,
        abbr="GL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.GRADIENT_EXPLODING,
        abbr="GE",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.TENSOR_OVERFLOW,
        abbr="TO",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.OPERATOR_OVERFLOW,
        abbr="OO",
        # Send this condition to MindSpore will use WatchCondition.Condition.overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND,),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.TENSOR_TOO_LARGE,
        abbr="TL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.TENSOR_TOO_SMALL,
        abbr="TS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MEAN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.TENSOR_ALL_ZERO,
        abbr="TZ",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_all_zero
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ZERO_PERCENTAGE_GE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                default_value=100
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_NOT_CHANGED,
        abbr="WNC",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_not_changed
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.RTOL,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range,
                default_value=1e-5
            ),
            ConditionParameter(
                name=ParamNameEnum.ATOL,
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-8,
                visible_on_ui=False
            ),
            ConditionParameter(
                name=ParamNameEnum.EQUAL_NAN,
                value_type=ValueTypeEnum.BOOL,
                support_disable=False,
                default_value=False,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_CHANGE_TOO_LARGE,
        abbr="WCL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_UPDATE_RATIO_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range,
                default_value=1e-1
            ),
            ConditionParameter(
                name=ParamNameEnum.EPSILON,
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-9,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.WEIGHT_CHANGE_TOO_SMALL,
        abbr="WCS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.ABS_MEAN_UPDATE_RATIO_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range,
                default_value=1e-4
            ),
            ConditionParameter(
                name=ParamNameEnum.EPSILON,
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-9,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.ACTIVATION_RANGE,
        abbr="AR",
        # Send this condition to MindSpore will use WatchCondition.Condition.activation_range
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.RANGE_START_INCLUSIVE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range,
                param_type=ParamTypeEnum.SUPPORT_PARAM
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_END_INCLUSIVE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range,
                param_type=ParamTypeEnum.SUPPORT_PARAM
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_PERCENTAGE_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                required_params=[ParamNameEnum.RANGE_START_INCLUSIVE.value, ParamNameEnum.RANGE_END_INCLUSIVE.value]
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_PERCENTAGE_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                required_params=[ParamNameEnum.RANGE_START_INCLUSIVE.value, ParamNameEnum.RANGE_END_INCLUSIVE.value]
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_positive_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_MIN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.ACTIVATION,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id=ConditionIdEnum.TENSOR_RANGE,
        abbr="TR",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_range
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name=ParamNameEnum.RANGE_START_INCLUSIVE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range,
                param_type=ParamTypeEnum.SUPPORT_PARAM
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_END_INCLUSIVE,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_normal_param_range,
                param_type=ParamTypeEnum.SUPPORT_PARAM
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_PERCENTAGE_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                required_params=[ParamNameEnum.RANGE_START_INCLUSIVE.value, ParamNameEnum.RANGE_END_INCLUSIVE.value]
            ),
            ConditionParameter(
                name=ParamNameEnum.RANGE_PERCENTAGE_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_percentage_param_range,
                required_params=[ParamNameEnum.RANGE_START_INCLUSIVE.value, ParamNameEnum.RANGE_END_INCLUSIVE.value]
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_MIN_LT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_positive_param_range
            ),
            ConditionParameter(
                name=ParamNameEnum.MAX_MIN_GT,
                value_type=ValueTypeEnum.FLOAT64,
                valid_test_func=check_abs_param_range
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    )
]
