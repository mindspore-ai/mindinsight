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
"""Mock the customized network TrainOneStep."""
import mindspore.nn as nn


class TrainOneStep(nn.Cell):
    """Mock the customized network TrainOneStep."""
    def __init__(self, network, optimizer):
        super(TrainOneStep, self).__init__(auto_prefix=False)
        self.network = network
        self.optimizer = optimizer

    def construct(self):
        """Mock the construct method."""
        raise NotImplementedError
