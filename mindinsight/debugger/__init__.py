# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
Debugger Introduction.

This module provides Python APIs to retrieve the debugger info. The APIs can
help users to understand the training process and find the bugs in training
script.
"""

from mindinsight.debugger.api.conditions import \
    Watchpoint, WatchpointHit, TensorTooLargeCondition, TensorUnchangedCondition, TensorAllZeroCondition, \
    TensorOverflowCondition, OperatorOverflowCondition, TensorRangeCondition, TensorTooSmallCondition, \
    TensorChangeBelowThresholdCondition, TensorChangeAboveThresholdCondition, ConditionBase
from mindinsight.debugger.api.debugger_tensor import DebuggerTensor
from mindinsight.debugger.api.dump_analyzer import DumpAnalyzer
from mindinsight.debugger.api.node import Node


__all__ = ["DumpAnalyzer", "Node", "DebuggerTensor", "Watchpoint",
           "WatchpointHit",
           "TensorTooLargeCondition",
           "TensorTooSmallCondition",
           "TensorRangeCondition",
           "TensorOverflowCondition",
           "OperatorOverflowCondition",
           "TensorAllZeroCondition",
           "TensorUnchangedCondition",
           "TensorChangeBelowThresholdCondition",
           "TensorChangeAboveThresholdCondition",
           "ConditionBase"
           ]
