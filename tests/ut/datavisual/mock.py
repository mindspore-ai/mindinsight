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
"""
Mock for ut test case.
"""


class MockLogger:
    """Mock logger in DataLoader and collect log message for verification."""
    log_msg = {'error': None, 'warning': None, 'info': None}

    @classmethod
    def error(cls, msg, *args):
        """Mock logger.error() and collect error message."""
        cls.log_msg['error'] = msg.replace("%s", "{}").replace("%r", "'{}'").format(*args)

    @classmethod
    def warning(cls, msg, *args):
        """Mock logger.warning() and collect warning message."""
        cls.log_msg['warning'] = msg.replace("%s", "{}").replace("%r", "'{}'").format(*args)

    @classmethod
    def info(cls, msg, *args):
        """Mock logger.info() and collect info message."""
        cls.log_msg['info'] = msg.replace("%s", "{}").replace("%r", "'{}'").format(*args)

    @classmethod
    def debug(cls, msg, *args):
        """Mock logger.debug() and collect debug message."""
        cls.log_msg['debug'] = msg.replace("%s", "{}").replace("%r", "'{}'").format(*args)
