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
"""Mock MindSpore Interface."""
from .application.model_zoo.resnet import ResNet
from .common.tensor import Tensor
from .dataset import MindDataset
from .nn import *
from .train.callback import _ListCallback, Callback, RunContext, ModelCheckpoint, SummaryStep
from .train.summary import SummaryRecord
