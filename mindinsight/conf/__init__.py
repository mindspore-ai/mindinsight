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
        self._load_from_defaults()
        self._load_from_constants()
        self.refresh()

    def refresh(self):
        """Refresh settings from environment variables."""
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


    def _load_from_defaults(self):
        """Update settings from defaults module."""
        default_settings = import_module('mindinsight.conf.defaults')
        for setting in dir(default_settings):
            if setting.isupper():
                setattr(self, setting, getattr(default_settings, setting))
                self._default_settings.add(setting)

    def _load_from_constants(self):
        """Update settings from constants module"""
        constant_settings = import_module('mindinsight.conf.constants')
        for setting in dir(constant_settings):
            if setting.isupper():
                setattr(self, setting, getattr(constant_settings, setting))


settings = Settings()
