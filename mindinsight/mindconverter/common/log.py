# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Create a logger."""
__all__ = ["logger", "logger_console"]

from mindinsight.utils.log import setup_logger

logger = setup_logger("mindconverter", "mindconverter", console=False)


class MindConverterLogger:
    """MindConverter logger for stdout."""

    def __init__(self):
        self.logger = setup_logger("mindconverter", "mindconverter", console=True, sub_log_name="logger_console")
        self.console = setup_logger("mindconverter", "mindconverter", console=True, sub_log_name="logger_only_console",
                                    logfile=False)

    def warning(self, msg, only_console=False):
        """Log warning message to stdout."""
        if only_console:
            self.console.warning(msg)
        else:
            self.logger.warning(msg)

    def info(self, msg, only_console=False):
        """Log info level message to stdout."""
        if only_console:
            self.console.info(msg)
        else:
            self.logger.info(msg)

    def error(self, msg, only_console=False):
        """Log error level message to stdout."""
        if only_console:
            self.console.error(msg)
        else:
            self.logger.error(msg)


logger_console = MindConverterLogger()
