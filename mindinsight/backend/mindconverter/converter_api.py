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
"""MindConverter API module."""
import json
from flask import Blueprint, jsonify, request

from mindinsight.conf import settings
from mindinsight.mindconverter.graph_based_converter.framework import get_ms_graph_from_onnx
from mindinsight.utils.exceptions import ParamValueError

BLUEPRINT = Blueprint("converter", __name__, url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


@BLUEPRINT.route("/converter/graph/nodes", methods=["POST"])
def get_graph_nodes():
    """Get onnx graph."""
    body = _read_post_request(request)
    model_file = body.get('model_file')
    input_node = body.get('input_nodes')
    shape = body.get('shape')
    input_nodes = {}
    for index, node in enumerate(input_node):
        input_nodes[node] = tuple(shape[index])
    output_nodes = body.get('output_nodes')
    response = get_ms_graph_from_onnx(model_file, input_node, output_nodes)
    return jsonify(response)


def _read_post_request(post_request):
    """
    Extract the body of post request.

    Args:
        post_request (object): The post request.

    Returns:
        dict, the deserialized body of request.
    """
    body = post_request.stream.read()
    try:
        body = json.loads(body or "{}")
    except Exception:
        raise ParamValueError("Json data parse failed.")
    return body


def init_module(app):
    """
    Init module entry.
    """
    app.register_blueprint(BLUEPRINT)
