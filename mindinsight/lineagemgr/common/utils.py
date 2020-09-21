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
import os
import re

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamTypeError
from mindinsight.lineagemgr.common.log import logger as log


def enum_to_list(enum):
    return [enum_ele.value for enum_ele in enum]


def get_timestamp(filename):
    """Get timestamp from filename."""
    timestamp = int(re.search(SummaryWatcher().SUMMARY_FILENAME_REGEX, filename)[1])
    return timestamp


def make_directory(path):
    """Make directory."""
    if path is None or not isinstance(path, str) or not path.strip():
        log.error("Invalid input path: %r.", path)
        raise LineageParamTypeError("Invalid path type")

    # convert relative path to abs path
    path = os.path.realpath(path)
    log.debug("The abs path is %r", path)

    # check path exist and its write permissions]
    if os.path.exists(path):
        real_path = path
    else:
        # All exceptions need to be caught because create directory maybe have some limit(permissions)
        log.debug("The directory(%s) doesn't exist, will create it", path)
        try:
            os.makedirs(path, exist_ok=True)
            real_path = path
        except PermissionError as err:
            log.error("No write permission on the directory(%r), error = %r", path, err)
            raise LineageParamTypeError("No write permission on the directory.")
    return real_path
