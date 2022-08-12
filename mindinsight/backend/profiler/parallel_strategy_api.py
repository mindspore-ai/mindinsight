# Copyright 2021 Huawei Technologies Co., Ltd
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

This module provides the interfaces to profile parallel strategy.
"""
import os
import json
import stat

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from mindinsight.conf import settings
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException
from mindinsight.profiler.common.exceptions.exceptions import ProfilerIOException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.util import check_train_job_and_profiler_dir

BLUEPRINT = Blueprint("profile_parallel_strategy", __name__, url_prefix=settings.URL_PATH_PREFIX+settings.API_PREFIX)


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)


@BLUEPRINT.route("/profile/parallel-strategy/graphs", methods=["GET"])
def get_parallel_strategy():
    """Get parallel strategy by train id."""
    train_id = request.args.get('train_id')
    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))
    if os.path.exists(profiler_dir + '/graphs'):
        try:
            with open(profiler_dir + '/graphs', 'r') as f:
                return jsonify(json.load(f))
        except (IOError, OSError, json.JSONDecodeError) as err:
            log.error('Error occurred when read graphs file: %s', err)
            raise ProfilerIOException()

    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)

    analyser = AnalyserFactory.instance().get_analyser('parallel_strategy', profiler_dir, train_id)

    if analyser.data['status'] == "finish" and not os.path.exists(profiler_dir + '/graphs'):
        try:
            output_path = profiler_dir + '/graphs'
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            modes = stat.S_IREAD | stat.S_IWRITE
            with os.fdopen(os.open(output_path, flags, modes), "w") as fp:
                json.dump(analyser.data, fp)

        except (IOError, OSError, json.JSONDecodeError) as err:
            log.error('Error occurred when read graphs file: %s', err)
            raise ProfilerIOException()
    return jsonify(analyser.data)
