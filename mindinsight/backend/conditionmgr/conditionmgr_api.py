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
"""Conditionmgr restful api."""
import json

from flask import Blueprint, request

from mindinsight.conf import settings
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.utils.exceptions import ParamMissError
from mindinsight.backend.debugger.debugger_api import BACKEND_SERVER, _wrap_reply

BLUEPRINT = Blueprint("conditionmgr", __name__,
                      url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


@BLUEPRINT.route("/conditionmgr/train-jobs/<train_id>/condition-collections", methods=["GET"])
def get_condition_collections(train_id):
    """get condition collections"""
    reply = _wrap_reply(BACKEND_SERVER.get_condition_collections, train_id)
    return reply


@BLUEPRINT.route("/conditionmgr/train-jobs/<train_id>/set-recommended-watch-points", methods=["POST"])
def set_recommended_watch_points(train_id):
    """set recommended watch points."""
    body = request.stream.read()
    try:
        body = json.loads(body if body else "{}")
    except json.JSONDecodeError:
        raise ParamValueError("Json data parse failed.")

    request_body = body.get('requestBody')
    if request_body is None:
        raise ParamMissError('requestBody')

    set_recommended = request_body.get('set_recommended')
    reply = _wrap_reply(BACKEND_SERVER.set_recommended_watch_points, set_recommended, train_id)
    return reply


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
