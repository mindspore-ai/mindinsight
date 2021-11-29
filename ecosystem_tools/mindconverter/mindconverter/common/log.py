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

import os
import sys
import time
import logging
import threading


class MindConverterFormatter(logging.Formatter):
    """
    MindConverter formatter.
    """

    def formatTime(self, record, datefmt=None):
        """
        Overwrite for uniform format %Y-%m-%d-%H:%M:%S.SSS.SSS

        Args:
            record (LogRecord): Log record.
            datefmt (str): Date format, type is string.

        Returns:
            str, formatted timestamp, type is string.
        """
        created_time = self.converter(record.created)
        if datefmt:
            return time.strftime(datefmt, created_time)

        timestamp = time.strftime('%Y-%m-%d-%H:%M:%S', created_time)
        msecs = str(round(record.msecs * 1000)).zfill(6)
        return '{}.{}.{}'.format(timestamp, msecs[:3], msecs[3:])

    def formatMessage(self, record):
        """Escape the message before format."""
        record.message = ' '.join(record.message.split())
        return super().formatMessage(record)


class MindConverterLogger:
    """MindConverter logger for stdout."""

    CONSOLE_FORMAT = '[%(levelname)s] MI(%(process)d:%(thread)d,%(processName)s):%(asctime)s ' \
                     '[MINDCONVERTER] %(message)s'
    LOGFILE_FORMAT = '[%(levelname)s] MI(%(process)d:%(thread)d,%(processName)s):%(asctime)s ' \
                     '[MINDCONVERTER] %(message)s'

    _mutex = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        with cls._mutex:
            if cls._instance is None:
                cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        output_dir = os.environ.get('MINDCONVERTER_OUTPUT_DIR', os.getcwd())

        self.console_logger = logging.getLogger(name='mindconverter.console')
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = MindConverterFormatter(self.CONSOLE_FORMAT)
        console_handler.setLevel(logging.DEBUG)
        self.console_logger.addHandler(console_handler)
        self.console_logger.setLevel(logging.DEBUG)

        self.logfile_logger = logging.getLogger(name='mindconverter.logfile')
        logfile_handler = logging.FileHandler(os.path.realpath(os.path.join(output_dir, 'mindconverter.log')))
        logfile_handler.formatter = MindConverterFormatter(self.LOGFILE_FORMAT)
        logfile_handler.setLevel(logging.DEBUG)
        self.logfile_logger.addHandler(logfile_handler)
        self.logfile_logger.setLevel(logging.DEBUG)

    @classmethod
    def init(cls):
        cls._instance = cls()

    @classmethod
    def instance(cls):
        return cls._instance

    @classmethod
    def debug(cls, msg, console=True, logfile=True):
        """Log debug level message to stdout."""
        if not cls._instance:
            cls.init()

        if console:
            cls._instance.console_logger.debug(msg)

        if logfile:
            cls._instance.logfile_logger.debug(msg)

    @classmethod
    def info(cls, msg, console=True, logfile=True):
        """Log info level message to stdout."""
        if not cls._instance:
            cls.init()

        if console:
            cls._instance.console_logger.info(msg)

        if logfile:
            cls._instance.logfile_logger.info(msg)

    @classmethod
    def warning(cls, msg, console=True, logfile=True):
        """Log warning message to stdout."""
        if not cls._instance:
            cls.init()

        if console:
            cls._instance.console_logger.warning(msg)

        if logfile:
            cls._instance.logfile_logger.warning(msg)

    @classmethod
    def error(cls, msg, console=True, logfile=True):
        """Log error level message to stdout."""
        if not cls._instance:
            cls.init()

        if console:
            cls._instance.console_logger.error(msg)

        if logfile:
            cls._instance.logfile_logger.error(msg)

    @classmethod
    def exception(cls, msg, console=True, logfile=True):
        """Log exception level message to stdout."""
        if not cls._instance:
            cls.init()

        if console:
            cls._instance.console_logger.exception(msg)

        if logfile:
            cls._instance.logfile_logger.exception(msg)
