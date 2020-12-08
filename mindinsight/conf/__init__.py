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
"""Conf module."""

import os
import json
import types
from importlib import import_module


class Settings:
    """
    Definition of Settings class.

    Examples:
        >>> from mindinsight.conf import settings
        >>> print(settings.PORT)
    """

    _prefix = 'MINDINSIGHT_'
    _explicit_settings = set()
    _default_settings = set()

    def __init__(self):
        """Initialization of Settings."""
        self.load_from_defaults()
        self.load_from_constants()
        self.refresh()

    def refresh(self):
        """Refresh settings from config file and environment variables."""
        self.update_from_file()
        self.update_from_env()

    def load_from_defaults(self):
        """Update settings from defaults module."""
        default_settings = import_module('mindinsight.conf.defaults')
        for setting in dir(default_settings):
            if setting.isupper():
                setattr(self, setting, getattr(default_settings, setting))
                self._default_settings.add(setting)

    def load_from_constants(self):
        """Update settings from constants module"""
        constant_settings = import_module('mindinsight.conf.constants')
        for setting in dir(constant_settings):
            if setting.isupper():
                setattr(self, setting, getattr(constant_settings, setting))

    def update_from_file(self):
        """Update settings from config file."""
        config_path = os.environ.get('MINDINSIGHT_CONFIG', '')
        if not config_path:
            return

        config_module = None

        # python:full.path.for.config.module
        if config_path.startswith('python:'):
            config_module = import_module(config_path[len('python:'):])

        # file:full/path/for/config.py
        elif config_path.startswith('file:'):
            config_path = config_path[len('file:'):]
            module_name = '__mindinsightconfig__'
            config_module = types.ModuleType(module_name)
            machinery = import_module('importlib.machinery')
            loader = machinery.SourceFileLoader(module_name, config_path)
            loader.exec_module(config_module)

        if config_module is None:
            return

        for setting in dir(config_module):
            if setting.isupper() and setting in self._default_settings:
                setting_value = getattr(config_module, setting)
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

    def update_from_env(self):
        """Update settings from environment variables."""
        for key, value in os.environ.items():
            if not key.startswith(self._prefix):
                continue

            setting = key[len(self._prefix):]
            if setting not in self._default_settings:
                continue

            setting_value = getattr(self, setting)
            if isinstance(setting_value, bool):
                value = (value == 'True')
            elif isinstance(setting_value, (int, float)):
                value = type(setting_value)(value)
            elif isinstance(setting_value, (list, dict)):
                value = json.loads(value)

            setattr(self, setting, value)
            self._explicit_settings.add(setting)

    def is_overridden(self, setting_name):
        """
        Check if specified setting is overridden.

        Args:
            setting_name (str): Setting name to be checked.

        Returns:
            bool, indicate whether given setting name is overridden.
        """
        return setting_name in self._explicit_settings

    def dump(self):
        """
        Dump settings data.

        Returns:
            dict, json formatted data of settings.
        """
        config = {}
        for setting in dir(self):
            if setting.isupper():
                config[setting] = getattr(self, setting)

        return config


settings = Settings()
