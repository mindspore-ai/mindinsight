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
from functools import wraps
import re

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamRunContextError, \
    LineageGetModelFileError, LineageLogError, LineageParamValueError, LineageDirNotExistError, \
    LineageParamSummaryPathError
from mindinsight.lineagemgr.common.validator.validate import validate_path
from mindinsight.utils.exceptions import MindInsightException


def enum_to_list(enum):
    return [enum_ele.value for enum_ele in enum]


def try_except(logger):
    """
    Catch or raise exceptions while collecting lineage.

    Args:
        logger (logger): The logger instance which logs the warning info.

    Returns:
        function, the decorator which we use to retry the decorated function.
    """
    def try_except_decorate(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                func(self, *args, **kwargs)
            except (AttributeError, MindInsightException,
                    LineageParamRunContextError, LineageLogError,
                    LineageGetModelFileError, IOError) as err:
                logger.error(err)

                try:
                    raise_except = self.raise_exception
                except AttributeError:
                    raise_except = False

                if raise_except is True:
                    raise

        return wrapper
    return try_except_decorate


def normalize_summary_dir(summary_dir):
    """Normalize summary dir."""
    try:
        summary_dir = validate_path(summary_dir)
    except (LineageParamValueError, LineageDirNotExistError) as error:
        log.error(str(error))
        log.exception(error)
        raise LineageParamSummaryPathError(str(error.message))
    return summary_dir


def get_timestamp(filename):
    """Get timestamp from filename."""
    timestamp = int(re.search(SummaryWatcher().SUMMARY_FILENAME_REGEX, filename)[1])
    return timestamp
