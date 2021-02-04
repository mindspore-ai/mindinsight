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
"""Log module."""

import sys
import os
import stat
import time
import fcntl
import logging
from logging.handlers import RotatingFileHandler

from mindinsight.conf import settings
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.constant import GeneralErrors


class MultiCompatibleRotatingFileHandler(RotatingFileHandler):
    """Inherit RotatingFileHandler for multiprocess compatibility."""

    def rolling_rename(self):
        """Rolling rename log files."""
        for i in range(self.backupCount - 1, 0, -1):
            sfn = self.rotation_filename("%s.%d" % (self.baseFilename, i))
            dfn = self.rotation_filename("%s.%d" % (self.baseFilename, i + 1))
            if os.path.exists(sfn):
                if os.path.exists(dfn):
                    os.remove(dfn)
                os.chmod(sfn, stat.S_IREAD)
                os.rename(sfn, dfn)

    def doRollover(self):
        """Do a rollover, as described in __init__()."""
        if self.stream:
            self.stream.close()
            self.stream = None

        # Attain an exclusive lock with blocking mode by `fcntl` module.
        with open(self.baseFilename, 'a') as file_pointer:
            fcntl.lockf(file_pointer.fileno(), fcntl.LOCK_EX)

        try:
            if self.backupCount > 0:
                self.rolling_rename()

            # dfn stands for destinated file name according to source codes in RotatingFileHandler.doRollover()
            dfn = self.rotation_filename(self.baseFilename + ".1")
            if os.path.exists(dfn):
                os.remove(dfn)

            os.chmod(self.baseFilename, stat.S_IREAD)
            self.rotate(self.baseFilename, dfn)

            with open(self.baseFilename, 'a'):
                os.chmod(self.baseFilename, stat.S_IREAD | stat.S_IWRITE)

            if not self.delay:
                self.stream = self._open()

        except FileNotFoundError:
            # Suppress this exception for concurrency.
            pass

    def _open(self):
        """Open the current base file with the (original) mode and encoding."""
        new_log = open(self.baseFilename, self.mode, encoding=self.encoding)
        os.chmod(self.baseFilename, stat.S_IREAD | stat.S_IWRITE)
        return new_log


class MindInsightFormatter(logging.Formatter):
    """
    MindInsight formatter.
    """

    def __init__(self, sub_module, fmt=None, **kwargs):
        """
        Initialization of SlogFormatter.

        Args:
            sub_module (str): Sub module name, type is string.
            fmt (str): Specified format pattern, type is string.

        Returns:
            Formatter, instance of SlogFormatter.
        """
        super(MindInsightFormatter, self).__init__(fmt=fmt, **kwargs)
        self.sub_module = sub_module.upper()

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

    def format(self, record):
        """
        Apply log format with specified pattern.

        Args:
            record (str): Format pattern, type is string.

        Returns:
            str, formatted log content according to format pattern, type if string.
        """
        record.filepath = record.pathname[__file__.rfind('mindinsight'):]
        record.sub_module = self.sub_module
        return super().format(record)


def get_logger(sub_module, log_name):
    """
    Get logger by name and sub module.

    Args:
        sub_module (str): Sub module name, type is string.
        log_name (str): Log file name, type is  string.

    Returns:
        Logger, logger instance named by sub_module and log_name.
    """
    return logging.getLogger(name='{}.{}'.format(sub_module, log_name))


def setup_logger(sub_module, log_name, **kwargs):
    """
    Setup logger with sub module name and log file name.

    Args:
        sub_module (str): Sub module name, also for sub directory under logroot.
        log_name (str): Log name, also for log filename.
        console (bool): Whether to output log to stdout. Default: False.
        logfile (bool): Whether to output log to disk. Default: True.
        level (Enum): Log level. Default: INFO.
        formatter (str): Log format.
        propagate (bool): Whether to enable propagate feature. Default: False.
        maxBytes (int): Rotating max bytes. Default: 50M.
        backupCount (int): Rotating backup count. Default: 30.

    Returns:
        Logger, well-configured logger instance.

    Examples:
        >>> from mindinsight.utils.log import setup_logger
        >>> logger = setup_logger('datavisual', 'flask.request', level=logging.DEBUG)

        >>> from mindinsight.utils.log import get_logger
        >>> logger = get_logger('datavisual', 'flask.request')

        >>> import logging
        >>> logger = logging.getLogger('datavisual.flask.request')
    """

    if kwargs.get('sub_log_name', False):
        logger = get_logger(sub_module, kwargs['sub_log_name'])
    else:
        logger = get_logger(sub_module, log_name)
    if logger.hasHandlers():
        return logger

    level = kwargs.get('level', settings.LOG_LEVEL)
    formatter = kwargs.get('formatter', None)
    propagate = kwargs.get('propagate', False)

    logger.setLevel(level)
    logger.propagate = propagate

    if not formatter:
        formatter = settings.LOG_FORMAT

    if kwargs.get('console', False):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.formatter = MindInsightFormatter(sub_module, formatter)
        logger.addHandler(console_handler)

    if kwargs.get('logfile', True):
        max_bytes = kwargs.get('maxBytes', settings.LOG_ROTATING_MAXBYTES)

        if not isinstance(max_bytes, int) or not max_bytes > 0:
            raise MindInsightException(GeneralErrors.PARAM_VALUE_ERROR,
                                       'maxBytes should be int type and > 0.')

        backup_count = kwargs.get('backupCount',
                                  settings.LOG_ROTATING_BACKUPCOUNT)

        if not isinstance(backup_count, int) or not backup_count > 0:
            raise MindInsightException(GeneralErrors.PARAM_VALUE_ERROR,
                                       'backupCount should be int type and > 0.')

        logfile_dir = os.path.join(settings.WORKSPACE, 'log', sub_module)

        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        os.makedirs(logfile_dir, mode=mode, exist_ok=True)

        logfile_handler = MultiCompatibleRotatingFileHandler(
            filename=os.path.join(logfile_dir, '{}.{}.log'.format(log_name, settings.PORT)),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf8'
        )
        logfile_handler.formatter = MindInsightFormatter(sub_module, formatter)
        logger.addHandler(logfile_handler)

    return logger
