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
"""
Profile api.

This module provides the interfaces to profile functions.
"""
import json
import os

from flask import Blueprint
from flask import jsonify
from flask import request
from marshmallow import ValidationError

from mindinsight.conf import settings
from mindinsight.datavisual.utils.tools import get_train_id, get_profiler_dir, unquote_args
from mindinsight.datavisual.utils.tools import to_int
from mindinsight.lineagemgr.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.analyser.minddata_analyser import MinddataAnalyser
from mindinsight.profiler.common.util import analyse_device_list_from_profiler_dir
from mindinsight.profiler.common.validator.validate import validate_condition, validate_ui_proc
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_profiler_path
from mindinsight.utils.exceptions import ParamValueError

BLUEPRINT = Blueprint("profile", __name__, url_prefix=settings.URL_PREFIX)


@BLUEPRINT.route("/profile/ops/search", methods=["POST"])
def get_profile_op_info():
    """
    Get operation profiling info.

    Returns:
        str, the operation profiling information.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/profile/ops/search
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    search_condition = request.stream.read()
    try:
        search_condition = json.loads(search_condition if search_condition else "{}")
    except Exception:
        raise ParamValueError("Json data parse failed.")
    validate_condition(search_condition)

    device_id = search_condition.get("device_id", "0")
    profiler_dir_abs = os.path.join(settings.SUMMARY_BASE_DIR, train_id, profiler_dir)
    try:
        profiler_dir_abs = validate_and_normalize_path(profiler_dir_abs, "profiler")
    except ValidationError:
        raise ParamValueError("Invalid profiler dir")

    op_type = search_condition.get("op_type")

    analyser = AnalyserFactory.instance().get_analyser(
        op_type, profiler_dir_abs, device_id
    )

    op_info = analyser.query(search_condition)
    return jsonify(op_info)


@BLUEPRINT.route("/profile/devices", methods=["GET"])
def get_profile_device_list():
    """
    Get profile device list.

    Returns:
        list, the available device list.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/profile/devices
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    profiler_dir_abs = os.path.join(settings.SUMMARY_BASE_DIR, train_id, profiler_dir)
    try:
        profiler_dir_abs = validate_and_normalize_path(profiler_dir_abs, "profiler")
    except ValidationError:
        raise ParamValueError("Invalid profiler dir")

    device_list = analyse_device_list_from_profiler_dir(profiler_dir_abs)
    return jsonify(device_list)


@BLUEPRINT.route("/profile/training-trace/graph", methods=["GET"])
def get_training_trace_graph():
    """
    Get training trace info of one step.

    Returns:
        Response, the training trace info of one step.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/training-trace/graph
    """
    summary_dir = request.args.get("dir")
    profiler_dir = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    graph_type = request.args.get("type", default='0')
    graph_type = to_int(graph_type, 'graph_type')
    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')

    analyser = AnalyserFactory.instance().get_analyser(
        'step_trace', profiler_dir, device_id)
    graph_info = analyser.query({
        'filter_condition': {
            'mode': 'step',
            'step_id': graph_type
        }})

    return jsonify(graph_info)


@BLUEPRINT.route("/profile/training-trace/target-time-info", methods=["GET"])
def get_target_time_info():
    """
    Get all the time information of the specified column.

    Returns:
        Response, all the time information of the specified column.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/training-trace/target-time-info
    """
    summary_dir = request.args.get("dir")
    profiler_dir = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    proc_name = request.args.get("type")
    validate_ui_proc(proc_name)
    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')

    analyser = AnalyserFactory.instance().get_analyser(
        'step_trace', profiler_dir, device_id)
    target_time_info = analyser.query({
        'filter_condition': {
            'mode': 'proc',
            'proc_name': proc_name
        }})
    target_time_info['summary'] = analyser.summary
    return jsonify(target_time_info)


@BLUEPRINT.route("/profile/queue_info", methods=["GET"])
def get_queue_info():
    """
    Get each type queue info.

    Returns:
        Response, the queue info.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/queue_info
    """
    profile_dir = get_profiler_abs_dir(request)

    device_id = unquote_args(request, "device_id")
    queue_type = unquote_args(request, "type")
    queue_info = {}

    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profile_dir, device_id)
    if queue_type == "get_next":
        queue_info, _ = minddata_analyser.analyse_get_next_info(info_type="queue")
    elif queue_type == "device_queue":
        queue_info, _ = minddata_analyser.analyse_device_queue_info(info_type="queue")

    return jsonify(queue_info)


@BLUEPRINT.route("/profile/minddata_op", methods=["GET"])
def get_time_info():
    """
    Get minddata operation info.

    Returns:
        Response, the minddata operation info.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/minddata_op
    """
    profile_dir = get_profiler_abs_dir(request)
    device_id = unquote_args(request, "device_id")
    op_type = unquote_args(request, "type")

    time_info = {
        'size': 0,
        'info': [],
        "summary": {"time_summary": {}},
        "advise": {}
    }
    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profile_dir, device_id)
    if op_type == "get_next":
        _, time_info = minddata_analyser.analyse_get_next_info(info_type="time")
    elif op_type == "device_queue":
        _, time_info = minddata_analyser.analyse_device_queue_info(info_type="time")

    return jsonify(time_info)


@BLUEPRINT.route("/profile/process_summary", methods=["GET"])
def get_process_summary():
    """
    Get interval process summary.

    Returns:
        Response, the process summary.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/process_summary
    """
    profile_dir = get_profiler_abs_dir(request)
    device_id = unquote_args(request, "device_id")

    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profile_dir, device_id)
    get_next_queue_info, _ = minddata_analyser.analyse_get_next_info(info_type="queue")
    device_queue_info, _ = minddata_analyser.analyse_device_queue_info(info_type="queue")

    result = MinddataAnalyser.analyse_queue_summary(get_next_queue_info, device_queue_info)

    return jsonify(result)


def get_profiler_abs_dir(requests):
    """
    Get interval process summary.

    Args:
        requests (LocalProxy): The requests.

    Returns:
        str, the profiler abs dir.
    """
    profiler_dir = get_profiler_dir(requests)
    train_id = get_train_id(requests)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    profiler_dir_abs = os.path.join(settings.SUMMARY_BASE_DIR, train_id, profiler_dir)
    try:
        profiler_dir_abs = validate_and_normalize_path(profiler_dir_abs, "profiler")
    except ValidationError:
        raise ParamValueError("Invalid profiler dir")

    return profiler_dir_abs

def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)
