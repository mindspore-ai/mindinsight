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
"""Hook module."""

import os
import threading
from importlib import import_module

from mindinsight.conf import settings
from mindinsight.utils.exceptions import FileSystemPermissionError


class BaseHook:
    """Base hook class."""

    def register_secure_domains(self):
        """Hook function to register secure domains."""
        return []

    def register_startup_arguments(self, parser):
        """
        Hook function to register startup arguments.

        Args:
            parser (ArgumentParser): specify parser to which arguments are added.
        """

    def on_startup(self, logger):
        """
        Hook function to on startup.

        Args:
            logger (Logger): script logger of start command.
        """

    def on_shutdown(self, logger):
        """
        Hook function to on shutdown.

        Args:
            logger (Logger): script logger of stop command.
        """

    def on_init(self):
        """Hook function to on init."""


class HookUtils:
    """
    Lock utilities.

    Examples:
        >>> from mindinsight.utils.hook import HookUtils
        >>> for hook in HookUtils.instance().hooks():
        >>>     domains = hook.register_secure_domains()
        >>>     hook.register_startup_arguments(parser)
        >>>     hook.on_startup(logger)
        >>>     hook.on_shutdown(logger)
        >>>     hook.on_init()
    """

    _lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Built-in __new__ function."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls, *args, **kwargs)
                    cls._instance.discover()
        return cls._instance

    def discover(self):
        """Discover hook instances."""
        self.__hooks = []
        mindinsight_path = os.path.join(__file__, os.pardir, os.pardir)
        hook_path = os.path.realpath(os.path.join(mindinsight_path, 'common', 'hook'))
        files = os.listdir(hook_path)
        files.sort()
        for file in files:
            if file.startswith('_') or not file.endswith('.py'):
                continue
            hook_name = file[:-len('.py')]
            hook_module = import_module('mindinsight.common.hook.{}'.format(hook_name))
            hook_cls = getattr(hook_module, 'Hook', None)
            if hook_cls is not None and issubclass(hook_cls, BaseHook):
                self.__hooks.append(hook_cls())

    def hooks(self):
        """
        Return list of hook instances.

        Returns:
            list, list of hook instances.
        """
        return self.__hooks

    @classmethod
    def instance(cls):
        """
        Produce singleton instance of HookUtils.

        Returns:
            HookUtils, singleton instance of HookUtils.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def init(workspace='', config='', **kwargs):
    """
    Init MindInsight context.

    Args:
        workspace (str): specify mindinsight workspace, default is ''.
        config (str): specify mindinsight config file, default is ''.

    Raises:
        FileSystemPermissionError, if workspace is not allowed to access or available.
    """
    permissions = os.R_OK | os.W_OK | os.X_OK

    # set umask to 0o077
    os.umask(permissions << 3 | permissions)

    # assign argument values into environment
    if workspace:
        kwargs['workspace'] = workspace

    if config:
        kwargs['config'] = config

    for key, value in kwargs.items():
        variable = 'MINDINSIGHT_{}'.format(key.upper())
        os.environ[variable] = str(value)

    settings.refresh()

    if os.path.exists(settings.WORKSPACE):
        if not os.access(settings.WORKSPACE, permissions):
            raise FileSystemPermissionError('Workspace {} not allowed to access'.format(workspace))
    else:
        try:
            mode = permissions << 6
            os.makedirs(settings.WORKSPACE, mode=mode, exist_ok=True)
        except OSError:
            # race condition or priority problem
            raise FileSystemPermissionError('Workspace {} not available'.format(workspace))

    for hook in HookUtils.instance().hooks():
        hook.on_init()
