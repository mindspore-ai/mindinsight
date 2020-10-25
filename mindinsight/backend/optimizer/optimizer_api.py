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
"""Optimizer API module."""
import json
from flask import Blueprint, jsonify, request

from mindinsight.conf import settings
from mindinsight.datavisual.data_transform.data_manager import DATA_MANAGER
from mindinsight.lineagemgr.model import get_lineage_table
from mindinsight.optimizer.common.enums import ReasonCode
from mindinsight.optimizer.common.exceptions import SamplesNotEnoughError, CorrelationNanError
from mindinsight.optimizer.utils.importances import calc_hyper_param_importance
from mindinsight.optimizer.utils.utils import calc_histogram
from mindinsight.utils.exceptions import ParamValueError

BLUEPRINT = Blueprint("optimizer", __name__, url_prefix=settings.URL_PATH_PREFIX+settings.API_PREFIX)


@BLUEPRINT.route("/optimizer/targets/search", methods=["POST"])
def get_optimize_targets():
    """Get optimize targets."""
    search_condition = request.stream.read()
    try:
        search_condition = json.loads(search_condition if search_condition else "{}")
    except Exception:
        raise ParamValueError("Json data parse failed.")

    response = _get_optimize_targets(DATA_MANAGER, search_condition)
    return jsonify(response)


def _get_optimize_targets(data_manager, search_condition=None):
    """Get optimize targets."""
    table = get_lineage_table(data_manager=data_manager, search_condition=search_condition)

    target_summaries = []
    for target in table.target_names:
        hyper_parameters = []
        for hyper_param in table.hyper_param_names:
            param_info = {"name": hyper_param}
            try:
                importance = calc_hyper_param_importance(table.dataframe_data, hyper_param, target)
                param_info.update({"importance": importance})
            except SamplesNotEnoughError:
                param_info.update({"importance": 0})
                param_info.update({"reason_code": ReasonCode.SAMPLES_NOT_ENOUGH.value})
            except CorrelationNanError:
                param_info.update({"importance": 0})
                param_info.update({"reason_code": ReasonCode.CORRELATION_NAN.value})
            hyper_parameters.append(param_info)

        # Sort `hyper_parameters` in descending order of `importance` and ascending order of `name`.
        # If the automatically collected parameters and user-defined parameters have the same importance,
        # the user-defined parameters will be ranked behind.
        hyper_parameters.sort(key=lambda hyper_param: (-hyper_param.get("importance"),
                                                       hyper_param.get("name").startswith('['),
                                                       hyper_param.get("name")))

        target_summary = {
            "name": target,
            "buckets": calc_histogram(table.get_column(target)),
            "hyper_parameters": hyper_parameters,
            "data": table.get_column_values(target)
        }
        target_summaries.append(target_summary)

    target_summaries.sort(key=lambda summary: summary.get("name"))

    hyper_params_metadata = [{
        "name": hyper_param,
        "data": table.get_column_values(hyper_param)
    } for hyper_param in table.hyper_param_names]

    result = {
        "metadata": {
            "train_ids": table.train_ids,
            "possible_hyper_parameters": hyper_params_metadata,
            "unrecognized_params": table.drop_column_info
        },
        "targets": target_summaries
    }

    return result


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)
