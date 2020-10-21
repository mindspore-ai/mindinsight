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
"""Enums."""

import enum


class BaseEnum(enum.Enum):
    """Base enum."""
    @classmethod
    def list_members(cls):
        """List all members."""
        return [member.value for member in cls]


class ReasonCode(BaseEnum):
    """Reason code for calculating importance."""
    NOT_ALL_NUMBERS = 1
    SAMPLES_NOT_ENOUGH = 2
    CORRELATION_NAN = 3


class AcquisitionFunctionEnum(BaseEnum):
    """Enum for acquisition function method."""
    # Upper confidence bound
    UCB = 'ucb'
    # Probability of improvement
    PI = 'pi'
    # Expected improvement
    EI = 'ei'


class TuneMethod(BaseEnum):
    """Enum for tuning method."""
    # Gaussian process regressor
    GP = 'gp'


class GPSupportArgs(BaseEnum):
    METHOD = 'method'


class HyperParamKey(BaseEnum):
    """Config keys for hyper parameters."""
    BOUND = 'bounds'
    CHOICE = 'choice'
    DECIMAL = 'decimal'
    TYPE = 'type'
    SOURCE = 'source'


class HyperParamType(BaseEnum):
    """Config keys for hyper parameters."""
    INT = 'int'
    FLOAT = 'float'


class TargetKey(BaseEnum):
    """Config keys for target."""
    GROUP = 'group'
    NAME = 'name'
    GOAL = 'goal'


class TargetGoal(BaseEnum):
    """Goal for target."""
    MAXIMUM = 'maximize'
    MINIMUM = 'minimize'


class HyperParamSource(BaseEnum):
    SYSTEM_DEFINED = 'system_defined'
    USER_DEFINED = 'user_defined'


class TargetGroup(BaseEnum):
    SYSTEM_DEFINED = 'system_defined'
    METRIC = 'metric'


class TunableSystemDefinedParams(BaseEnum):
    """Tunable metadata keys of lineage collection."""
    BATCH_SIZE = 'batch_size'
    EPOCH = 'epoch'
    LEARNING_RATE = 'learning_rate'


class SystemDefinedTargets(BaseEnum):
    """System defined targets"""
    LOSS = 'loss'
