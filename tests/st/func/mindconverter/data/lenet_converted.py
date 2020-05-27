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
"""Test network script of LeNet."""
import mindspore.nn as nn
import mindspore.ops.operations as P
# import torch.nn as nn
# import torch.nn.functional as F


class TestLeNet(nn.Cell):
    """TestLeNet network."""
    def __init__(self):
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=6, kernel_size=5, pad_mode='pad', has_bias=True)
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=5, pad_mode='pad', has_bias=True)
        self.fc1 = nn.Dense(in_channels=16 * 5 * 5, out_channels=120)
        self.fc2 = nn.Dense(in_channels=120, out_channels=84)
        self.fc3 = nn.Dense(in_channels=84, out_channels=10)

    def construct(self, input_x):
        """Callback method."""
        out = self.forward1(input_x)
        return out

    def forward1(self, input_x):
        """forward1 method."""
        out = P.ReLU()(self.conv1(input_x))
        out = P.MaxPool(2, None, 'valid')(out)
        out = P.ReLU()(self.conv2(out))
        out = P.MaxPool(2, None, 'valid')(out)
        out = P.Reshape()(out, (P.Shape()(out)[0], -1,))
        out = P.ReLU()(self.fc1(out))
        out = P.ReLU()(self.fc2(out))
        out = self.fc3(out)
        return out
