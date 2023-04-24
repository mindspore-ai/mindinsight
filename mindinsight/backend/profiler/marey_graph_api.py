# Copyright 2022 Huawei Technologies Co., Ltd
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
Marey api.

This module provides the interfaces to profile used in extended marey's graph.
"""
import os

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from mindinsight.conf import settings
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.util import check_train_job_and_profiler_dir
from mindinsight.profiler.common.log import logger
from mindinsight.utils.exceptions import ParamValueError

BLUEPRINT = Blueprint("profile_marey_graph", __name__, url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)


@BLUEPRINT.route("/profile/marey-graph/memory-data", methods=["GET"])
def get_memory_data():
    """Get memory data by train id."""

    train_id = request.args.get('train_id')
    device_type = request.args.get("device_type")
    if device_type not in ['ascend']:
        logger.info("Invalid device_type, device_type should be gpu or ascend.")
        raise ParamValueError("Invalid device_type.")
    if train_id is None:
        logger.info("Invalid train_id parameter of None.")
        raise ParamValueError("Invalid train_id.")

    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))
    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)

    analyser = AnalyserFactory.instance().get_analyser('memory_usage', profiler_dir, train_id)
    return jsonify(analyser.get_memory_data_for_marey(device_type))


@BLUEPRINT.route("/profile/marey-graph/flops-data", methods=["GET"])
def get_flops_data():
    """Get memory data by train id."""

    train_id = request.args.get('train_id')
    if train_id is None:
        logger.info("Invalid train_id parameter of None.")
        raise ParamValueError("Invalid train_id.")

    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))
    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)

    analyser = AnalyserFactory.instance().get_analyser('flops', profiler_dir, train_id)
    return jsonify(analyser.get_flops_data_for_marey())


@BLUEPRINT.route("/profile/marey-graph/overview-time", methods=["GET"])
def get_overview_time():
    """Get memory data by train id."""

    train_id = request.args.get('train_id')
    if train_id is None:
        logger.info("Invalid train_id parameter of None.")
        raise ParamValueError("Invalid train_id.")

    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))
    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)

    analyser = AnalyserFactory.instance().get_analyser('cluster_step_trace', profiler_dir, train_id)
    return jsonify(analyser.get_overview_time_info())


@BLUEPRINT.route("/profile/marey-graph/timeline", methods=["GET"])
def get_timeline():
    """Get memory data by train id."""

    train_id = request.args.get('train_id')
    device_list = request.args.get('device_list')
    if train_id is None:
        logger.info("Invalid train_id parameter of None.")
        raise ParamValueError("Invalid train_id.")

    step = request.args.get('step', default='1')
    device_type = request.args.get("device_type")
    if device_type not in ['ascend']:
        logger.info("Invalid device_type, device_type should be gpu or ascend.")
        raise ParamValueError("Invalid device_type.")

    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))
    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)

    analyser = AnalyserFactory.instance().get_analyser('timeline', profiler_dir, train_id)
    return jsonify(analyser.get_marey_timeline(step, device_list))
