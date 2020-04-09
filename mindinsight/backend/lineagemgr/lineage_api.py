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
import os

from flask import Blueprint, jsonify, request

from mindinsight.conf import settings
from mindinsight.datavisual.utils.tools import get_train_id
from mindinsight.lineagemgr import filter_summary_lineage, get_summary_lineage
from mindinsight.lineagemgr.common.validator.validate import validate_path
from mindinsight.utils.exceptions import MindInsightException, ParamValueError

BLUEPRINT = Blueprint("lineage", __name__, url_prefix=settings.URL_PREFIX.rstrip("/"))


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
    summary_base_dir = str(settings.SUMMARY_BASE_DIR)
    try:
        lineage_info = filter_summary_lineage(
            summary_base_dir, search_condition)

        lineages = lineage_info['object']

        summary_base_dir = os.path.realpath(summary_base_dir)
        length = len(summary_base_dir)

        for lineage in lineages:
            summary_dir = lineage['summary_dir']
            summary_dir = os.path.realpath(summary_dir)
            if summary_base_dir == summary_dir:
                relative_dir = './'
            else:
                relative_dir = os.path.join(os.curdir, summary_dir[length+1:])
            lineage['summary_dir'] = relative_dir

    except MindInsightException as exception:
        raise MindInsightException(exception.error, exception.message, http_code=400)

    return lineage_info


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

    summary_base_dir = str(settings.SUMMARY_BASE_DIR)
    summary_dir = get_train_id(request)
    if summary_dir.startswith('/'):
        validate_path(summary_dir)
    elif summary_dir.startswith('./'):
        summary_dir = os.path.join(summary_base_dir, summary_dir[2:])
        summary_dir = validate_path(summary_dir)
    else:
        raise ParamValueError(
            "Summary dir should be absolute path or "
            "relative path that relate to summary base dir."
        )
    try:
        dataset_graph = get_summary_lineage(
            summary_dir=summary_dir,
            keys=['dataset_graph']
        )
    except MindInsightException as exception:
        raise MindInsightException(exception.error, exception.message, http_code=400)

    if dataset_graph:
        summary_dir_result = dataset_graph.get('summary_dir')
        base_dir_len = len(summary_base_dir)
        if summary_base_dir == summary_dir_result:
            relative_dir = './'
        else:
            relative_dir = os.path.join(
                os.curdir, summary_dir[base_dir_len + 1:]
            )
        dataset_graph['summary_dir'] = relative_dir

    return jsonify(dataset_graph)


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
