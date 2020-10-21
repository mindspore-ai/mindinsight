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
"""Hyper config."""
import json
import os

from mindinsight.optimizer.common.constants import HYPER_CONFIG_ENV_NAME, HYPER_CONFIG_LEN_LIMIT
from mindinsight.optimizer.common.exceptions import HyperConfigEnvError, HyperConfigError


class AttributeDict(dict):
    """A dict can be accessed by attribute."""
    def __init__(self, d=None):
        super().__init__()
        if d is not None:
            for k, v in d.items():
                self[k] = v

    def __key(self, key):
        """Get key."""
        return "" if key is None else key

    def __setattr__(self, key, value):
        """Set attribute for object."""
        self[self.__key(key)] = value

    def __getattr__(self, key):
        """
        Get attribute value according by attribute name.

        Args:
            key (str): attribute name.

        Returns:
            Any, attribute value.

        Raises:
            AttributeError: If the key does not exists, will raise Exception.

        """
        value = self.get(self.__key(key))
        if value is None:
            raise AttributeError("The attribute %r is not exist." % key)
        return value

    def __getitem__(self, key):
        """Get attribute value according by attribute name."""
        value = super().get(self.__key(key))
        if value is None:
            raise AttributeError("The attribute %r is not exist." % key)
        return value

    def __setitem__(self, key, value):
        """Set attribute for object."""
        return super().__setitem__(self.__key(key), value)


class HyperConfig:
    """
    Hyper config.
    1. Init HyperConfig.
    2. Get suggested params and summary_dir.
    3. Record by SummaryCollector with summary_dir.

    Examples:
        >>> hyper_config = HyperConfig()
        >>> params = hyper_config.params
        >>> learning_rate = params.learning_rate
        >>> batch_size = params.batch_size

        >>> summary_dir = hyper_config.summary_dir
        >>> summary_cb = SummaryCollector(summary_dir)
    """
    def __init__(self):
        self._init_validate_hyper_config()

    def _init_validate_hyper_config(self):
        """Init and validate hyper config."""
        hyper_config = os.environ.get(HYPER_CONFIG_ENV_NAME)
        if hyper_config is None:
            raise HyperConfigEnvError("Hyper config is not in system environment.")
        if len(hyper_config) > HYPER_CONFIG_LEN_LIMIT:
            raise HyperConfigEnvError("Hyper config is too long. The length limit is %s, the length of "
                                      "hyper_config is %s." % (HYPER_CONFIG_LEN_LIMIT, len(hyper_config)))

        try:
            hyper_config = json.loads(hyper_config)
        except TypeError as exc:
            raise HyperConfigError("Hyper config type error. detail: %s." % str(exc))
        except Exception as exc:
            raise HyperConfigError("Hyper config decode error. detail: %s." % str(exc))

        self._validate_hyper_config(hyper_config)
        self._hyper_config = hyper_config

    def _validate_hyper_config(self, hyper_config):
        """Validate hyper config."""
        for key in ['summary_dir', 'params']:
            if key not in hyper_config:
                raise HyperConfigError("%r must exist in hyper_config." % key)

        # validate summary_dir
        summary_dir = hyper_config.get('summary_dir')
        if not isinstance(summary_dir, str):
            raise HyperConfigError("The 'summary_dir' should be string.")
        hyper_config['summary_dir'] = os.path.realpath(summary_dir)

        # validate params
        params = hyper_config.get('params')
        if not isinstance(params, dict):
            raise HyperConfigError("'params' is not a dict.")
        for key, value in params.items():
            if not isinstance(value, (int, float)):
                raise HyperConfigError("The value of %r is not integer or float." % key)

    @property
    def params(self):
        """Get params."""
        return AttributeDict(self._hyper_config.get('params'))

    @property
    def summary_dir(self):
        """Get train summary dir path."""
        return self._hyper_config.get('summary_dir')

    @property
    def custom_lineage_data(self):
        return self._hyper_config.get('custom_lineage_data')
