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
"""Base writer."""
from abc import abstractmethod


class Writer:
    """Base writer for writers."""
    @abstractmethod
    def add(self, value):
        """
        Abstract method for adding value.

        Args:
            value (object): scalar, tensor or image value with wall_time, tag and step.
        """

    @abstractmethod
    def write(self):
        """Abstract method for writing file."""
