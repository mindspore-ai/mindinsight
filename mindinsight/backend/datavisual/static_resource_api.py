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
from flask import make_response
from flask import redirect
from flask import Blueprint

from mindinsight.conf import settings


BLUEPRINT = Blueprint("static_resource", __name__, url_prefix=settings.URL_PATH_PREFIX)


@BLUEPRINT.route("/", methods=["GET"])
def index():
    """Interface to return index.html."""
    app_path = os.path.realpath(os.path.dirname(sys.argv[0]))
    index_html_file = os.path.realpath(os.path.join(app_path, current_app.static_folder, os.pardir, 'index.html'))
    with open(index_html_file, 'r') as file_pointer:
        html_content = file_pointer.read()
    return make_response(html_content)


@BLUEPRINT.route("/graphvizlib.wasm", methods=["GET"])
def return_wasm_file():
    """
    Interface to redirect graphvizlib.wasm

    When accessing the graphvizlib.wasm file in front module via Firefox browser, the file path will change to
    "/graphvizlib.wasm" which makes the computed diagram inaccessible. Redirecting the path to correct address can
    ensure the computed graph accessible properly.
    """
    return redirect(location="static/js/graphvizlib.wasm")


def init_module(app):
    """
    Init module entry.

    Args:
        app: the application obj.
    """
    app.register_blueprint(BLUEPRINT)
