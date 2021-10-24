# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Mock the MindSpore SoftmaxCrossEntropyWithLogits class."""
from ..cell import Cell


class _Loss(Cell):
    """Mocked _Loss."""

    def __init__(self, reduction='mean'):
        super(_Loss, self).__init__()
        self.reduction = reduction

    def construct(self, base, target):
        """Mocked construct function."""
        raise NotImplementedError


class SoftmaxCrossEntropyWithLogits(_Loss):
    """Mocked SoftmaxCrossEntropyWithLogits."""

    def __init__(self, weight=None):
        super(SoftmaxCrossEntropyWithLogits, self).__init__(weight)

    def construct(self, base, target):
        """Mocked construct."""
        return 1
