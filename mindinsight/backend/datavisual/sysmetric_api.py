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
"""System metrics API."""

from flask import Blueprint, jsonify
from mindinsight.conf import settings
from mindinsight.sysmetric.collector import get_metrics

BLUEPRINT = Blueprint("sysmetric", __name__, url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


@BLUEPRINT.route("/sysmetric/current", methods=["GET"])
def query_sysmetric():
    """Query the system metrics."""

    return jsonify(get_metrics())


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.

    """
    app.register_blueprint(BLUEPRINT)
