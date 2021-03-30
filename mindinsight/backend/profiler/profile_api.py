# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
from mindinsight.datavisual.utils.tools import get_train_id, get_profiler_dir, to_int, get_device_id
from mindinsight.datavisual.utils.tools import unquote_args
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.analyser.minddata_analyser import MinddataAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException
from mindinsight.profiler.common.util import analyse_device_list_from_profiler_dir, \
    check_train_job_and_profiler_dir
from mindinsight.profiler.common.validator.validate import validate_condition, validate_ui_proc
from mindinsight.profiler.common.validator.validate import validate_minddata_pipeline_condition
from mindinsight.profiler.common.validator.validate_path import \
    validate_and_normalize_path
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_profiler_path
from mindinsight.profiler.proposer.compose_proposer import ComposeProposal
from mindinsight.profiler.common.log import logger
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.backend.application import CustomResponse

BLUEPRINT = Blueprint("profile", __name__, url_prefix=settings.URL_PATH_PREFIX+settings.API_PREFIX)


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
    except (json.JSONDecodeError, ValueError):
        raise ParamValueError("Json data parse failed.")
    validate_condition(search_condition)

    device_id = search_condition.get("device_id", "0")
    to_int(device_id, 'device_id')
    profiler_dir_abs = os.path.join(settings.SUMMARY_BASE_DIR, train_id, profiler_dir)
    try:
        profiler_dir_abs = validate_and_normalize_path(profiler_dir_abs, "profiler")
    except ValidationError:
        raise ParamValueError("Invalid profiler dir")

    check_train_job_and_profiler_dir(profiler_dir_abs)

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

    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_list, _ = analyse_device_list_from_profiler_dir(profiler_dir_abs)
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
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    graph_type = request.args.get("type", default='0')
    graph_type = to_int(graph_type, 'graph_type')
    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')
    graph_info = {}
    try:
        analyser = AnalyserFactory.instance().get_analyser(
            'step_trace', profiler_dir_abs, device_id)
    except ProfilerFileNotFoundException:
        return jsonify(graph_info)

    graph_info = analyser.query({
        'filter_condition': {
            'mode': 'step',
            'step_id': graph_type
        }})
    graph_info['summary'] = analyser.summary
    graph_info['point_info'] = analyser.point_info
    graph_info['is_heterogeneous'] = False

    # In heterogeneous training scene, do not display step trace data.
    cpu_op_type_file_name = f"cpu_op_type_info_{device_id}.csv"
    if cpu_op_type_file_name in os.listdir(profiler_dir_abs):
        graph_info = {'is_heterogeneous': True}

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
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    proc_name = request.args.get("type")
    validate_ui_proc(proc_name)
    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')

    analyser = AnalyserFactory.instance().get_analyser(
        'step_trace', profiler_dir_abs, device_id)
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
    profiler_dir_abs = get_profiler_abs_dir(request)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = unquote_args(request, "device_id")
    to_int(device_id, 'device_id')
    queue_type = unquote_args(request, "type")
    queue_info = {}

    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profiler_dir_abs, device_id)
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
    profiler_dir_abs = get_profiler_abs_dir(request)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = unquote_args(request, "device_id")
    to_int(device_id, 'device_id')
    op_type = unquote_args(request, "type")

    time_info = {
        'size': 0,
        'info': [],
        "summary": {"time_summary": {}},
        "advise": {}
    }
    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profiler_dir_abs, device_id)
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
    profiler_dir_abs = get_profiler_abs_dir(request)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = unquote_args(request, "device_id")
    to_int(device_id, 'device_id')

    minddata_analyser = AnalyserFactory.instance().get_analyser(
        'minddata', profiler_dir_abs, device_id)
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


@BLUEPRINT.route("/profile/summary/propose", methods=["GET"])
def get_profile_summary_proposal():
    """
    Get summary profiling proposal.

    Returns:
        str, the summary profiling proposal.

    Raises:
        ParamValueError: If the parameters contain some errors.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/summary/propose
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    device_id = get_device_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")
    to_int(device_id, 'device_id')

    profiler_dir_abs = os.path.join(settings.SUMMARY_BASE_DIR, train_id, profiler_dir)
    try:
        profiler_dir_abs = validate_and_normalize_path(profiler_dir_abs, "profiler")
    except ValidationError:
        raise ParamValueError("Invalid profiler dir")

    check_train_job_and_profiler_dir(profiler_dir_abs)

    step_trace_condition = {"filter_condition": {"mode": "proc",
                                                 "proc_name": "iteration_interval",
                                                 "step_id": 0}}
    options = {'step_trace': {"iter_interval": step_trace_condition}}

    proposal_type_list = ['step_trace', 'minddata', 'minddata_pipeline', 'common']
    proposal_obj = ComposeProposal(profiler_dir_abs, device_id, proposal_type_list)
    proposal_info = proposal_obj.get_proposal(options)
    # Use json.dumps for orderly return
    return CustomResponse(json.dumps(proposal_info), mimetype='application/json')


@BLUEPRINT.route("/profile/minddata-pipeline/op-queue", methods=["POST"])
def get_minddata_pipeline_op_queue_info():
    """
    Get minddata pipeline operator info and queue info.

    Returns:
        str, the operation information and queue information.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/profile/minddata-pipeline/op-queue
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    profiler_dir_abs = os.path.join(
        settings.SUMMARY_BASE_DIR, train_id, profiler_dir
    )
    try:
        profiler_dir_abs = validate_and_normalize_path(
            profiler_dir_abs, "profiler"
        )
    except ValidationError:
        raise ParamValueError("Invalid profiler dir.")

    check_train_job_and_profiler_dir(profiler_dir_abs)
    condition = request.stream.read()
    try:
        condition = json.loads(condition) if condition else {}
    except Exception:
        raise ParamValueError("Json data parse failed.")
    validate_minddata_pipeline_condition(condition)

    device_id = condition.get("device_id", "0")
    to_int(device_id, 'device_id')
    analyser = AnalyserFactory.instance().get_analyser(
        'minddata_pipeline', profiler_dir_abs, device_id
    )
    op_info = analyser.query(condition)
    return jsonify(op_info)


@BLUEPRINT.route("/profile/minddata-pipeline/queue", methods=["GET"])
def get_minddata_pipeline_queue_info():
    """
    Get the special minddata pipeline queue info.

    Returns:
        str, the queue information.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/minddata-pipeline/queue
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    profiler_dir_abs = os.path.join(
        settings.SUMMARY_BASE_DIR, train_id, profiler_dir
    )
    try:
        profiler_dir_abs = validate_and_normalize_path(
            profiler_dir_abs, "profiler"
        )
    except ValidationError:
        raise ParamValueError("Invalid profiler dir.")

    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get('device_id', default='0')
    to_int(device_id, 'device_id')
    op_id = request.args.get('op_id', type=int)
    if op_id is None:
        raise ParamValueError("Invalid operator id or operator id does not exist.")

    analyser = AnalyserFactory.instance().get_analyser(
        'minddata_pipeline', profiler_dir_abs, device_id
    )
    op_queue_info = analyser.get_op_and_parent_op_info(op_id)
    return jsonify(op_queue_info)


@BLUEPRINT.route("/profile/timeline-summary", methods=["GET"])
def get_timeline_summary():
    """
    Get timeline summary info.

    Returns:
        Response, the timeline summary info.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/timeline-summary
    """
    summary_dir = request.args.get("dir")
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')
    device_type = request.args.get("device_type", default='ascend')
    if device_type not in ['gpu', 'ascend']:
        logger.info("Invalid device_type, device_type should be gpu or ascend.")
        raise ParamValueError("Invalid device_type.")

    analyser = AnalyserFactory.instance().get_analyser(
        'timeline', profiler_dir_abs, device_id)
    summary = analyser.get_timeline_summary(device_type)

    return summary


@BLUEPRINT.route("/profile/timeline", methods=["GET"])
def get_timeline_detail():
    """
    Get timeline detail.

    Returns:
        Response, the detail information of timeline.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/timeline
    """
    summary_dir = request.args.get("dir")
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get("device_id", default='0')
    _ = to_int(device_id, 'device_id')
    device_type = request.args.get("device_type", default='ascend')
    if device_type not in ['gpu', 'ascend']:
        logger.info("Invalid device_type, device_type should be gpu or ascend.")
        raise ParamValueError("Invalid device_type.")

    analyser = AnalyserFactory.instance().get_analyser(
        'timeline', profiler_dir_abs, device_id)
    timeline = analyser.get_display_timeline(device_type)

    return jsonify(timeline)


@BLUEPRINT.route("/profile/memory-summary", methods=["GET"])
def get_memory_usage_summary():
    """
    Get memory usage summary info.

    Returns:
        Response, the memory usage summary info.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/memory-summary
    """
    summary_dir = request.args.get("dir")
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get("device_id", default='0')
    to_int(device_id, 'device_id')
    device_type = request.args.get("device_type", default='ascend')
    if device_type not in ['ascend']:
        logger.info("Invalid device_type, Memory Usage only supports Ascend for now.")
        raise ParamValueError("Invalid device_type.")

    analyser = AnalyserFactory.instance().get_analyser(
        'memory_usage', profiler_dir_abs, device_id)
    summary = analyser.get_memory_usage_summary(device_type)

    return summary


@BLUEPRINT.route("/profile/memory-graphics", methods=["GET"])
def get_memory_usage_graphics():
    """
    Get graphic representation of memory usage.

    Returns:
        Response, the graphic representation of memory usage.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/memory-graphics
    """
    summary_dir = request.args.get("dir")
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get("device_id", default='0')
    to_int(device_id, 'device_id')
    device_type = request.args.get("device_type", default='ascend')
    if device_type not in ['ascend']:
        logger.info("Invalid device_type, Memory Usage only supports Ascend for now.")
        raise ParamValueError("Invalid device_type.")

    analyser = AnalyserFactory.instance().get_analyser(
        'memory_usage', profiler_dir_abs, device_id)
    graphics = analyser.get_memory_usage_graphics(device_type)

    return graphics


@BLUEPRINT.route("/profile/memory-breakdowns", methods=["GET"])
def get_memory_usage_breakdowns():
    """
    Get memory breakdowns of each node.

    Returns:
        Response, the memory breakdowns for each node.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/profile/memory-breakdowns
    """
    summary_dir = request.args.get("dir")
    profiler_dir_abs = validate_and_normalize_profiler_path(summary_dir, settings.SUMMARY_BASE_DIR)
    check_train_job_and_profiler_dir(profiler_dir_abs)

    device_id = request.args.get("device_id", default='0')
    to_int(device_id, 'device_id')
    device_type = request.args.get("device_type", default='ascend')
    graph_id = request.args.get("graph_id", default='0')
    node_id = request.args.get("node_id", default='0')
    node_id = to_int(node_id, 'node_id')
    if device_type not in ['ascend']:
        logger.error("Invalid device_type, Memory Usage only supports Ascend for now.")
        raise ParamValueError("Invalid device_type.")

    analyser = AnalyserFactory.instance().get_analyser(
        'memory_usage', profiler_dir_abs, device_id)
    breakdowns = analyser.get_memory_usage_breakdowns(device_type, graph_id, node_id)

    return breakdowns


@BLUEPRINT.route("/profile/minddata-cpu-utilization-summary", methods=["POST"])
def get_minddata_cpu_utilization_info():
    """
    Get minddata cpu utilization info.

    Returns:
        str, the minddata cpu utilization info.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>>POST http://xxx/v1/mindinsight/profile/minddata-cpu-utilization-summary
    """
    profiler_dir = get_profiler_dir(request)
    train_id = get_train_id(request)
    if not profiler_dir or not train_id:
        raise ParamValueError("No profiler_dir or train_id.")

    profiler_dir_abs = os.path.join(
        settings.SUMMARY_BASE_DIR, train_id, profiler_dir
    )

    try:
        profiler_dir_abs = validate_and_normalize_path(
            profiler_dir_abs, "profiler"
        )
    except ValidationError:
        raise ParamValueError("Invalid profiler dir.")

    check_train_job_and_profiler_dir(profiler_dir_abs)
    condition = request.stream.read()
    try:
        condition = json.loads(condition) if condition else {}
    except (json.JSONDecodeError, ValueError):
        raise ParamValueError("Json data parse failed.")

    device_id = condition.get("device_id", "0")
    to_int(device_id, 'device_id')
    analyser = AnalyserFactory.instance().get_analyser(
        'minddata_cpu_utilization', profiler_dir_abs, device_id
    )
    cpu_utilization = analyser.query(condition)
    return jsonify(cpu_utilization)


@BLUEPRINT.route("/profile/cluster-step-trace-summary", methods=["POST"])
def get_cluster_step_trace_info():
    """
    Get cluster step trace info.

    Returns:
        str, the cluster step trace info.

    Raises:
        ParamValueError: If the search condition contains some errors.

    Examples:
        >>>POST http://xxx/v1/mindinsight/profile/cluster-step-trace-summary
    """
    train_id = get_train_id(request)
    cluster_profiler_dir = os.path.join(settings.SUMMARY_BASE_DIR, train_id)
    try:
        cluster_profiler_dir = validate_and_normalize_path(cluster_profiler_dir, 'cluster_profiler')
    except ValidationError:
        raise ParamValueError('Invalid cluster_profiler dir')

    condition = request.stream.read()
    try:
        condition = json.loads(condition) if condition else {}
    except (json.JSONDecodeError, ValueError):
        raise ParamValueError("Json data parse failed.")

    device_id = condition.get("device_id", "0")
    to_int(device_id, 'device_id')

    analyser = AnalyserFactory.instance().get_analyser(
        'cluster_step_trace', cluster_profiler_dir, device_id
    )
    step_trace_info = analyser.query(condition)
    return jsonify(step_trace_info)


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)
