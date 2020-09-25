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
"""Lineage utils."""
import re

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher


def enum_to_list(enum):
    """Enum to list."""
    return [enum_ele.value for enum_ele in enum]


def get_timestamp(filename):
    """Get timestamp from filename."""
    timestamp = int(re.search(SummaryWatcher().SUMMARY_FILENAME_REGEX, filename)[1])
    return timestamp
