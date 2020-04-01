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
"""Mock the MindSpore mindspore/nn/optim.py."""
from .cell import Cell


class Parameter:
    """Mock the MindSpore Parameter class."""

    def __init__(self, learning_rate):
        self._name = "Parameter"
        self.default_input = learning_rate

    @property
    def name(self):
        """The property of name."""
        return self._name

    def __repr__(self):
        format_str = 'Parameter (name={name})'
        return format_str.format(name=self._name)


class Optimizer(Cell):
    """Mock the MindSpore Optimizer class."""

    def __init__(self, learning_rate):
        super(Optimizer, self).__init__()
        self.learning_rate = Parameter(learning_rate)


class Momentum(Optimizer):
    """Mock the MindSpore Momentum class."""

    def __init__(self, learning_rate):
        super(Momentum, self).__init__(learning_rate)
        self.dynamic_lr = False
