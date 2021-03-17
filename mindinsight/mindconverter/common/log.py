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
        self.logger = setup_logger("mindconverter", "mindconverter", console=True,
                                   sub_log_name="logger_console", formatter="%(message)s")

    def warning(self, msg):
        """Log warning message to stdout."""
        self.logger.warning("[WARNING] MINDCONVERTER: %s", msg)

    def info(self, msg):
        """Log info level message to stdout."""
        self.logger.info("\n")
        self.logger.info("[INFO] MINDCONVERTER: %s", msg)
        self.logger.info("\n")

    def error(self, msg):
        """Log error level message to stdout."""
        self.logger.error("\n")
        self.logger.error("[ERROR] MINDCONVERTER: %s", msg)
        self.logger.error("\n")


logger_console = MindConverterLogger()
