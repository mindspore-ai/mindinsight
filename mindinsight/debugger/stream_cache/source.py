# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Source Info."""

from mindinsight.domain.graph.base import Source


class DebuggerSource(Source):
    """Source Data object"""

    @property
    def stack(self):
        """The property of stack."""
        return [self]

    def __lt__(self, other):
        pkg_pattern = 'site-packages'
        cur_path_value = int(pkg_pattern in self.file_path)
        other_path_value = int(pkg_pattern in other.file_path)
        if cur_path_value != other_path_value:
            return cur_path_value < other_path_value
        if self.file_path != other.file_path:
            return self.file_path < other.file_path
        return self.line_no < other.line_no

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def __hash__(self):
        return hash(str(self.to_dict()))
