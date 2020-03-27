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
"""Static resource api."""
import os
import sys

from flask import current_app
from flask import send_from_directory
from flask import Blueprint


APP_PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
BLUEPRINT = Blueprint("static_resource", __name__)


@BLUEPRINT.route("/", methods=["GET"])
def index():
    """Interface to  return static index.html."""
    return send_from_directory(get_index_resource_dir(), "index.html")


def get_index_resource_dir():
    """Interface to return index.html resource directory."""
    return os.path.realpath(os.path.join(APP_PATH, current_app.static_folder, os.pardir))


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.
    """
    app.register_blueprint(BLUEPRINT)
