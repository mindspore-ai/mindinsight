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
"""crc32 type stub module."""
from typing import Union

ByteStr = Union[bytes, str]


def CheckValueAgainstData(crc_value: ByteStr, data: ByteStr, size: int) -> bool:
    """Check crc_value against new crc value from data to see if data is currupted."""


def GetMaskCrc32cValue(data: ByteStr, n: int) -> int:
    """Get masked crc value from data."""
