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
from attrdict import AttrDict

from mindinsight.optimizer.common.constants import HYPER_CONFIG_ENV_NAME
from mindinsight.optimizer.common.exceptions import HyperConfigError

_HYPER_CONFIG_LEN_LIMIT = 100000


class HyperConfig:
    """
    Hyper config.

    Init hyper config:
    >>> hyper_config = HyperConfig()

    Get suggest params:
    >>> param_obj = hyper_config.params
    >>> learning_rate = params.learning_rate

    Get summary dir:
    >>> summary_dir = hyper_config.summary_dir

    Record by SummaryCollector:
    >>> summary_cb = SummaryCollector(summary_dir)
    """
    def __init__(self):
        self._init_validate_hyper_config()

    def _init_validate_hyper_config(self):
        """Init and validate hyper config."""
        hyper_config = os.environ.get(HYPER_CONFIG_ENV_NAME)
        if hyper_config is None:
            raise HyperConfigError("Hyper config is not in system environment.")
        if len(hyper_config) > _HYPER_CONFIG_LEN_LIMIT:
            raise HyperConfigError("Hyper config is too long. The length limit is %s, the length of "
                                   "hyper_config is %s." % (_HYPER_CONFIG_LEN_LIMIT, len(hyper_config)))

        try:
            hyper_config = json.loads(hyper_config)
        except TypeError as exc:
            raise HyperConfigError("Hyper config type error. detail: %s." % str(exc))
        except Exception as exc:
            raise HyperConfigError("Hyper config decode error. detail: %s." % str(exc))

        self._validate_hyper_config(hyper_config)
        self._summary_dir = hyper_config.get('summary_dir')
        self._param_obj = AttrDict(hyper_config.get('params'))

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
        return self._param_obj

    @property
    def summary_dir(self):
        """Get train summary dir path."""
        return self._summary_dir
