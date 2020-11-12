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
from mindinsight.conditionmgr.condition import Condition
from mindinsight.conditionmgr.condition import OptimizePhaseEnum
from mindinsight.conditionmgr.condition import ConditionParameter
from mindinsight.conditionmgr.condition import ValueTypeEnum
from mindinsight.conditionmgr.condition import TargetTypeEnum
from mindinsight.conditionmgr.condition import PlatformEnum
from mindinsight.conditionmgr.condition import check_initialization_available

CONDITION_LIST = [
    Condition(
        condition_id="weight_initialization",
        abbr="WI",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_initialization
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="zero_percentage_ge",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=100
            ),
            ConditionParameter(
                name="max_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_lt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1),
        available_test_func=check_initialization_available
    ),
    Condition(
        condition_id="weight_overflow",
        abbr="WO",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="weight_too_large",
        abbr="WL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="weight_too_small",
        abbr="WS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.WEIGHT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="gradient_vanishing",
        abbr="GV",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="gradient_too_large",
        abbr="GL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="gradient_exploding",
        abbr="GE",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.GRADIENT,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="tensor_overflow",
        abbr="TO",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_general_overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="operator_overflow",
        abbr="OO",
        # Send this condition to MindSpore will use WatchCondition.Condition.overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND,),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="nan",
        abbr="NAN",
        # Send this condition to MindSpore will use WatchCondition.Condition.nan
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.GPU,),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="overflow",
        abbr="OVERFLOW",
        # Send this condition to MindSpore will use WatchCondition.Condition.overflow
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND,),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="inf",
        abbr="INF",
        # Send this condition to MindSpore will use WatchCondition.Condition.inf
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="max_gt",
        abbr="MAX>",
        # Send this condition to MindSpore will use WatchCondition.Condition.max_gt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="max_lt",
        abbr="MAX<",
        # Send this condition to MindSpore will use WatchCondition.Condition.max_lt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="min_gt",
        abbr="MIN>",
        # Send this condition to MindSpore will use WatchCondition.Condition.min_gt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="min_lt",
        abbr="MIN<",
        # Send this condition to MindSpore will use WatchCondition.Condition.min_lt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="max_min_gt",
        abbr="MAX-MIN>",
        # Send this condition to MindSpore will use WatchCondition.Condition.max_min_gt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="max_min_lt",
        abbr="MAX-Min<",
        # Send this condition to MindSpore will use WatchCondition.Condition.max_min_lt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="mean_gt",
        abbr="MEAN>",
        # Send this condition to MindSpore will use WatchCondition.Condition.mean_gt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="mean_lt",
        abbr="MEAN<",
        # Send this condition to MindSpore will use WatchCondition.Condition.mean_lt
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="param",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 0)
    ),
    Condition(
        condition_id="tensor_initialization",
        abbr="TI",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_initialization
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="zero_percentage_ge",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=100
            ),
            ConditionParameter(
                name="max_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_lt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1),
        available_test_func=check_initialization_available
    ),
    Condition(
        condition_id="tensor_too_large",
        abbr="TL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_gt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_gt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="tensor_too_small",
        abbr="TS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="max_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="min_lt",
                value_type=ValueTypeEnum.FLOAT64
            ),
            ConditionParameter(
                name="mean_lt",
                value_type=ValueTypeEnum.FLOAT64
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="tensor_all_zero",
        abbr="TZ",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_all_zero
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="zero_percentage_ge",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=100
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="weight_not_changed",
        abbr="WNC",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_not_changed
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="rtol",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-5
            ),
            ConditionParameter(
                name="atol",
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-8,
                visible_on_ui=False
            ),
            ConditionParameter(
                name="equal_nan",
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
        condition_id="weight_change_too_large",
        abbr="WCL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_update_ratio_mean_gt",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-1
            ),
            ConditionParameter(
                name="epsilon",
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
        condition_id="weight_change_too_small",
        abbr="WCS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_update_ratio_mean_lt",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-4
            ),
            ConditionParameter(
                name="epsilon",
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
        condition_id="tensor_change_too_large",
        abbr="TCL",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_large
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_update_ratio_mean_gt",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-1
            ),
            ConditionParameter(
                name="epsilon",
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-9,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="tensor_change_too_small",
        abbr="TCS",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_change_too_small
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="abs_update_ratio_mean_lt",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-4
            ),
            ConditionParameter(
                name="epsilon",
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-9,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    ),
    Condition(
        condition_id="tensor_not_changed",
        abbr="TNC",
        # Send this condition to MindSpore will use WatchCondition.Condition.tensor_not_changed
        optimize_phase=OptimizePhaseEnum.TENSOR_CHECK,
        parameters=[
            ConditionParameter(
                name="rtol",
                value_type=ValueTypeEnum.FLOAT64,
                default_value=1e-5
            ),
            ConditionParameter(
                name="atol",
                value_type=ValueTypeEnum.FLOAT64,
                support_disable=False,
                default_value=1e-8,
                visible_on_ui=False
            ),
            ConditionParameter(
                name="equal_nan",
                value_type=ValueTypeEnum.BOOL,
                support_disable=False,
                default_value=False,
                visible_on_ui=False
            )
        ],
        supported_target_type=TargetTypeEnum.TENSOR,
        supported_platforms=(PlatformEnum.ASCEND, PlatformEnum.GPU),
        minimum_debugger_capability=(1, 1)
    )
]
