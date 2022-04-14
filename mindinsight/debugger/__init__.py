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
MindSpore Debugger is a debugging tool for training in Graph Mode. It can be applied to visualize
and analyze the intermediate computation results of the computational graph.
In Graph Mode training, the computation results of intermediate nodes in the computational graph can not be acquired
conveniently, which makes it difficult for users to do the debugging.

By applying MindSpore Debugger, users can:Visualize the computational graph on the UI and analyze the output
of the graph node.Set watchpoints to monitor training exceptions (for example, tensor overflow) and trace error causes.
Visualize and analyze the change of parameters, such as weights.Visualize the nodes and code mapping relationship.

Debugger API is a python API interface provided for offline debugger. You need to save dump data before using it.
For the method of saving dump data, `refer to Using Dump in the Graph Mode
<https://www.mindspore.cn/tutorials/experts/en/master/debug/dump.html>`_ .
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
