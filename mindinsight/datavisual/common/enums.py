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
"""Enums."""

import enum

class BaseEnum(enum.Enum):

    @classmethod
    def list_members(cls):
        """List all members."""
        return [member.value for member in cls]


class DataManagerStatus(BaseEnum):
    """Data manager status."""
    INIT = 'INIT'
    LOADING = 'LOADING'
    DONE = 'DONE'
    INVALID = 'INVALID'


class PluginNameEnum(BaseEnum):
    """Plugin Name Enum."""
    IMAGE = 'image'
    SCALAR = 'scalar'
    GRAPH = 'graph'
    HISTOGRAM = 'histogram'
    TENSOR = 'tensor'


@enum.unique
class CacheStatus(enum.Enum):
    """Train job cache status."""
    NOT_IN_CACHE = "NOT_IN_CACHE"
    CACHING = "CACHING"
    CACHED = "CACHED"
