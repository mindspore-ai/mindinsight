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

from mindinsight.datavisual.data_transform.data_manager import DataManager
from mindinsight.lineagemgr.cache_item_updater import LineageCacheItemUpdater
from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path
from mindinsight.lineagemgr.model import get_lineage_table, LineageTable, METRIC_PREFIX
from mindinsight.optimizer.common.constants import HYPER_CONFIG_ENV_NAME
from mindinsight.optimizer.common.enums import TuneMethod, TargetKey, TargetGoal
from mindinsight.optimizer.common.exceptions import OptimizerTerminateError
from mindinsight.optimizer.common.log import logger
from mindinsight.optimizer.tuners.gp_tuner import GPBaseTuner
from mindinsight.optimizer.utils.param_handler import organize_params_target
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
        self._data_manager = self._init_data_manager()
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

        # need to add validation for config_info: command, summary_base_dir, target and params.
        config_info['summary_base_dir'] = self._normalize_path("summary_base_dir", config_info.get('summary_base_dir'))
        self._make_summary_base_dir(config_info['summary_base_dir'])
        return config_info

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

    def _init_data_manager(self):
        """Initialize data_manager."""
        data_manager = DataManager(summary_base_dir=self._summary_base_dir)
        data_manager.register_brief_cache_item_updater(LineageCacheItemUpdater())

        return data_manager

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
        self._data_manager.start_load_data(reload_interval=0).join()

        try:
            lineage_table = get_lineage_table(self._data_manager)
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
            suggestion = self._suggest(self._lineage_table, params_info, target_info, method=tuner.get("name"))

            hyper_config = {
                'params': suggestion,
                'summary_dir': os.path.join(self._summary_base_dir, f'{self._dir_prefix}_{str(uuid.uuid1())}')
            }
            os.environ[HYPER_CONFIG_ENV_NAME] = json.dumps(hyper_config)
            s = subprocess.Popen(shlex.split(command))
            s.wait()
            if s.returncode != _OK:
                logger.error("An error occurred during execution, the auto tuning will be terminated.")
                raise OptimizerTerminateError("An error occurred during execution, the auto tuning was terminated.")

    def _get_tuner(self, tune_method=TuneMethod.GP.value):
        """Get tuner."""
        if tune_method.lower() not in TuneMethod.list_members():
            raise ParamValueError("'tune_method' should in %s." % TuneMethod.list_members())

        # Only support gaussian process regressor currently.
        return GPBaseTuner()

    def _suggest(self, lineage_table: LineageTable, params_info: dict, target_info: dict, method):
        """Get suggestions for targets."""
        tuner = self._get_tuner(method)
        target_name = target_info[TargetKey.NAME.value]
        if TargetKey.GROUP.value in target_info and target_info[TargetKey.GROUP.value] == 'metric':
            target_name = METRIC_PREFIX + target_name
        param_matrix, target_matrix = organize_params_target(lineage_table, params_info, target_name)

        if not param_matrix.empty:
            suggestion = tuner.suggest([], [], params_info)
        else:
            target_column = target_matrix[target_name].reshape((-1, 1))
            if target_info.get(TargetKey.GOAL.value) == TargetGoal.MAXIMUM.value:
                target_column = -target_column

            suggestion = tuner.suggest(param_matrix, target_column, params_info)

        return suggestion
