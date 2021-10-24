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
"""Mock MindSpore loss_scale.py."""
from ..cell import Cell


class TrainOneStepWithLossScaleCell(Cell):
    """Mock the TrainOneStepWithLossScaleCell class."""

    def __init__(self, network, optimizer):
        super(TrainOneStepWithLossScaleCell, self).__init__()
        self.network = network
        self.optimizer = optimizer

    def construct(self, data, label):
        """Mock the construct method."""
        raise NotImplementedError
