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
"""General tuner."""
import json
import os
import shlex
import subprocess
import uuid
import yaml

from marshmallow import ValidationError

from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path
from mindinsight.lineagemgr.model import get_lineage_table, LineageTable
from mindinsight.optimizer.common.constants import HYPER_CONFIG_ENV_NAME
from mindinsight.optimizer.common.enums import TuneMethod
from mindinsight.optimizer.common.exceptions import OptimizerTerminateError, ConfigParamError
from mindinsight.optimizer.common.log import logger
from mindinsight.optimizer.common.validator.optimizer_config import OptimizerConfig
from mindinsight.optimizer.tuners.gp_tuner import GPBaseTuner
from mindinsight.optimizer.utils.param_handler import organize_params_target
from mindinsight.optimizer.utils.utils import get_nested_message
from mindinsight.utils.exceptions import MindInsightException, ParamValueError, FileSystemPermissionError, UnknownError

_OK = 0


class Tuner:
    """
    Tuner for auto tuning.

    Args:
        config_path (str): config path, a yaml format file containing settings about tuner, target and parameters, etc.

    Raises:
        FileSystemPermissionError, can not open the config file because of permission.
        UnknownError, other exception.
    """
    def __init__(self, config_path: str):
        self._config_info = self._validate_config(config_path)
        self._summary_base_dir = self._config_info.get('summary_base_dir')
        self._dir_prefix = 'train'

    def _validate_config(self, config_path):
        """Check config_path."""
        config_path = self._normalize_path("config_path", config_path)
        try:
            with open(config_path, "r") as file:
                config_info = yaml.safe_load(file)
        except PermissionError as exc:
            raise FileSystemPermissionError("Can not open config file. Detail: %s." % str(exc))
        except Exception as exc:
            raise UnknownError("Detail: %s." % str(exc))

        self._validate_config_schema(config_info)
        config_info['summary_base_dir'] = self._normalize_path("summary_base_dir", config_info.get('summary_base_dir'))
        self._make_summary_base_dir(config_info['summary_base_dir'])
        return config_info

    def _validate_config_schema(self, config_info):
        error = OptimizerConfig().validate(config_info)
        if error:
            err_msg = get_nested_message(error)
            raise ConfigParamError(err_msg)

    def _make_summary_base_dir(self, summary_base_dir):
        """Check and make summary_base_dir."""
        if not os.path.exists(summary_base_dir):
            permissions = os.R_OK | os.W_OK | os.X_OK
            os.umask(permissions << 3 | permissions)
            mode = permissions << 6
            try:
                logger.info("The summary_base_dir is generated automatically, path is %s.", summary_base_dir)
                os.makedirs(summary_base_dir, mode=mode, exist_ok=True)
            except OSError as exc:
                raise UnknownError("Can not make the summary base directory. Detail: %s." % str(exc))

    def _normalize_path(self, param_name, path):
        """Normalize config path."""
        path = os.path.realpath(path)
        try:
            path = safe_normalize_path(
                path, param_name, None, check_absolute_path=True
            )
        except ValidationError:
            logger.error("The %r is invalid.", param_name)
            raise ParamValueError("The %r is invalid." % param_name)

        return path

    def _update_from_lineage(self):
        """Update lineage from lineagemgr."""
        try:
            lineage_table = get_lineage_table(summary_base_dir=self._summary_base_dir)
        except MindInsightException as err:
            logger.info("Can not query lineage. Detail: %s", str(err))
            lineage_table = None

        self._lineage_table = lineage_table

    def optimize(self, max_expr_times=1):
        """Method for auto tuning."""
        target_info = self._config_info.get('target')
        params_info = self._config_info.get('parameters')
        command = self._config_info.get('command')
        tuner = self._config_info.get('tuner')
        for _ in range(max_expr_times):
            self._update_from_lineage()
            suggestion, user_defined_info = self._suggest(self._lineage_table, params_info, target_info, tuner)

            hyper_config = {
                'params': suggestion,
                'summary_dir': os.path.join(self._summary_base_dir, f'{self._dir_prefix}_{str(uuid.uuid1())}'),
                'custom_lineage_data': user_defined_info
            }
            logger.info("Suggest values are: %s.", suggestion)
            os.environ[HYPER_CONFIG_ENV_NAME] = json.dumps(hyper_config)
            s = subprocess.Popen(shlex.split(command))
            s.wait()
            if s.returncode != _OK:
                logger.error("An error occurred during execution, the auto tuning will be terminated.")
                raise OptimizerTerminateError("An error occurred during execution, the auto tuning was terminated.")

    def _get_tuner(self, tuner):
        """Get tuner."""
        if tuner is None:
            return GPBaseTuner()

        tuner_name = tuner.get("name").lower()
        if tuner_name not in TuneMethod.list_members():
            raise ParamValueError("'tune_method' should in %s." % TuneMethod.list_members())

        args = tuner.get("args")
        if args is not None and args.get("method") is not None:
            return GPBaseTuner(args.get("method"))

        # Only support gaussian process regressor currently.
        return GPBaseTuner()

    def _suggest(self, lineage_table: LineageTable, params_info: dict, target_info: dict, tuner):
        """Get suggestions for targets."""
        tuner = self._get_tuner(tuner)
        param_matrix, target_column = organize_params_target(lineage_table, params_info, target_info)
        suggestion, user_defined_info = tuner.suggest(param_matrix, target_column, params_info)

        return suggestion, user_defined_info
