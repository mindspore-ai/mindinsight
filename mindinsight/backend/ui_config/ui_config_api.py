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
"""UI config restful api."""
from flask import Blueprint, jsonify

from mindinsight.conf import settings

BLUEPRINT = Blueprint("ui_config", __name__,
                      url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


@BLUEPRINT.route("/ui-config", methods=["GET"])
def get_config():
    """Get config of UI."""
    reply = {}
    enable_debugger = settings.ENABLE_DEBUGGER if hasattr(settings, 'ENABLE_DEBUGGER') else False
    reply["enable_debugger"] = enable_debugger
    return jsonify(reply)


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
