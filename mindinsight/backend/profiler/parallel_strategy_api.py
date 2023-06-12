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
from threading import Thread

from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from mindinsight.conf import settings
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException
from mindinsight.profiler.common.exceptions.exceptions import ProfilerIOException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.util import check_train_job_and_profiler_dir
from mindinsight.profiler.analyser.parallel_strategy_analyser import Status, ParallelStrategyCache

BLUEPRINT = Blueprint("profile_parallel_strategy", __name__, url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


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
    stage_id = request.args.get('stage_id')
    if stage_id != "metadata":
        stage_id = int(stage_id) if stage_id else 'metadata'

    profiler_dir = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, train_id, 'profiler'))

    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError as exc:
        raise ProfilerFileNotFoundException('Invalid cluster_profiler dir, detail: %s.' % str(exc))

    check_train_job_and_profiler_dir(profiler_dir)
    log.info("call get_parallel_strategy: %s, %s", str(train_id), str(stage_id))

    res_data = ParallelStrategyCache.get_cache(train_id, stage_id, profiler_dir)
    if res_data:
        return jsonify({'status': Status.FINISH.value, 'data': res_data})

    analyser = AnalyserFactory.instance().get_analyser('parallel_strategy', profiler_dir, train_id)

    if analyser.data['status'] == Status.FINISH.value:
        try:
            thread_list = []
            meta_data = analyser.data.get('metadata', {})
            graphs_data = analyser.data.get('graphs', {})

            if stage_id == 'metadata':
                res_data = meta_data
                res_data.update({
                    "stage_num": len(graphs_data)
                })
            else:
                res_data = graphs_data.get(stage_id, {})

            thread_list.append(Thread(target=ParallelStrategyCache.set_cache,
                                      args=(train_id, 'metadata', res_data, profiler_dir)))

            for k, v in graphs_data.items():
                thread_list.append(Thread(target=ParallelStrategyCache.set_cache,
                                          args=(train_id, k, v, profiler_dir)))

            for t in thread_list:
                t.start()

        except (IOError, OSError, json.JSONDecodeError) as err:
            log.error('Error occurred when read graphs file: %s', err)
            raise ProfilerIOException()
    return jsonify({'status': analyser.data.get('status'), 'data': res_data})
