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
"""Lineage restful api."""
import json

from flask import Blueprint, jsonify, request

from mindinsight.conf import settings
from mindinsight.datavisual.utils.tools import get_train_id
from mindinsight.datavisual.data_transform.data_manager import DATA_MANAGER
from mindinsight.lineagemgr.cache_item_updater import update_lineage_object
from mindinsight.lineagemgr.common.validator.validate import validate_train_id
from mindinsight.lineagemgr.model import filter_summary_lineage
from mindinsight.utils.exceptions import MindInsightException, ParamValueError

BLUEPRINT = Blueprint("lineage", __name__, url_prefix=settings.URL_PATH_PREFIX+settings.API_PREFIX)


@BLUEPRINT.route("/lineagemgr/lineages", methods=["POST"])
def get_lineage():
    """
    Get lineage.

    Returns:
        str, the lineage information.

    Raises:
        MindInsightException: If method fails to be called.
        ParamValueError: If parsing json data search_condition fails.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/lineagemgr/lineages
    """
    search_condition = request.stream.read()
    try:
        search_condition = json.loads(search_condition if search_condition else "{}")
    except Exception:
        raise ParamValueError("Json data parse failed.")

    lineage_info = _get_lineage_info(search_condition=search_condition)

    return jsonify(lineage_info)


def _get_lineage_info(search_condition):
    """
    Get lineage info for dataset or model.

    Args:
        search_condition (dict): Search condition.

    Returns:
        dict, lineage info.

    Raises:
        MindInsightException: If method fails to be called.
    """
    try:
        lineage_info = filter_summary_lineage(data_manager=DATA_MANAGER, search_condition=search_condition)

    except MindInsightException as exception:
        raise MindInsightException(exception.error, exception.message, http_code=400)

    return lineage_info


@BLUEPRINT.route("/lineagemgr/lineages", methods=["PUT"])
def update_lineage():
    """
    Get lineage.

    Returns:
        str, update the lineage information about cache and tag.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> PUT http://xxxx/v1/mindinsight/lineagemgr/lineages?train_id=./run1
    """
    train_id = get_train_id(request)
    added_info = request.json
    if not isinstance(added_info, dict):
        raise ParamValueError("The request body should be a dict.")

    update_lineage_object(DATA_MANAGER, train_id, added_info)

    return jsonify({"status": "success"})


@BLUEPRINT.route("/datasets/dataset_graph", methods=["GET"])
def get_dataset_graph():
    """
    Get dataset graph.

    Returns:
        str, the dataset graph information.

    Raises:
        MindInsightException: If method fails to be called.
        ParamValueError: If summary_dir is invalid.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/datasets/dataset_graph?train_id=xxx
    """

    train_id = get_train_id(request)
    validate_train_id(train_id)
    search_condition = {
        'summary_dir': {
            'in': [train_id]
        }
    }
    result = {}
    try:
        objects = filter_summary_lineage(data_manager=DATA_MANAGER, search_condition=search_condition).get('object')
    except MindInsightException as exception:
        raise MindInsightException(exception.error, exception.message, http_code=400)

    if objects:
        lineage_obj = objects[0]
        dataset_graph = lineage_obj.get('dataset_graph')

        if dataset_graph:
            result.update({'dataset_graph': dataset_graph})
            result.update({'summary_dir': lineage_obj.get('summary_dir')})

    return jsonify(result)


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
