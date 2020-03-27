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
"""Mock the MindSpore mindspore/train/callback.py."""
from collections import OrderedDict


class Cell:
    """Mock the Cell class."""

    def __init__(self, auto_prefix=True, pips=None):
        if pips is None:
            pips = dict()
        self._cells = OrderedDict()
        self._auto_prefix = auto_prefix
        self._pips = pips

    @property
    def auto_prefix(self):
        """The property of auto_prefix."""
        return self._auto_prefix

    @property
    def pips(self):
        """The property of pips."""
        return self._pips


class WithLossCell(Cell):
    """Mocked WithLossCell class."""

    def __init__(self, backbone, loss_fn):
        super(WithLossCell, self).__init__()
        self._backbone = backbone
        self._loss_fn = loss_fn


class TrainOneStepWithLossScaleCell(Cell):
    """Mocked TrainOneStepWithLossScaleCell."""
    def __init__(self, network, optimizer):
        super(TrainOneStepWithLossScaleCell, self).__init__()
        self.network = network
        self.optimizer = optimizer
