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
from importlib import import_module
import os
import json
from flask import Blueprint, jsonify, request

from marshmallow import ValidationError

from mindinsight.conf import settings
from mindinsight.mindconverter.graph_based_converter.framework import get_ms_graph_from_onnx, convert_from_ui
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.mindconverter.common.exceptions import ConvertFromUIError

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
    model_path = os.path.join(settings.SUMMARY_BASE_DIR, model_file)
    try:
        # most unix systems allow
        model_path = os.path.realpath(model_path)
    except ValueError:
        raise ValidationError("The path is invalid!")
    response = get_ms_graph_from_onnx(model_path, input_nodes, output_nodes)
    return jsonify(response)


@BLUEPRINT.route("/converter/models", methods=["GET"])
def list_models():
    """List onnx and pb models in current dir."""
    files = [f for f in os.listdir(settings.SUMMARY_BASE_DIR) if f.endswith(".onnx") or f.endswith(".pb")]
    files = sorted(files)
    return {"models_files": files}


@BLUEPRINT.route("/converter/models/info", methods=["GET"])
def get_info_from_onnx():
    """Get the parameter of inputs, shape and outputs according to the onnx file."""
    file_name = request.args.get('file_name')
    path = os.path.join(settings.SUMMARY_BASE_DIR, file_name)
    try:
        # most unix systems allow
        path = os.path.realpath(path)
    except ValueError:
        raise ValidationError("The path is invalid!")
    onnx = import_module("onnx")
    model = onnx.load(path)
    inputs = []
    shape = []
    outputs = []
    input_name = model.graph.input
    for n in input_name:
        inputs.append(n.name)
        tmp = []
        for i in n.type.tensor_type.shape.dim:
            tmp.append(i.dim_value)
        shape.append(tmp)
    for o in model.graph.output:
        outputs.append(o.name)
    return {"name": file_name, "inputs": inputs, "shape": shape, "outputs": outputs}


@BLUEPRINT.route("/converter/convert", methods=["POST"])
def convert_ui():
    """
    Convert the graph according to user selections from UI.

    Returns:
        str, reply message.

    Raises:
        ConvertFromUIError: If method fails to be called.
    """
    body = _read_post_request(request)
    model_file = body.get('model_file')
    input_node = body.get('input_nodes')
    shape = body.get('shape')
    path = body.get('output')
    output_folder = os.path.join(settings.SUMMARY_BASE_DIR, path)
    input_nodes = {}
    for index, node in enumerate(input_node):
        input_nodes[node] = tuple(shape[index])
    output_nodes = body.get('output_nodes')
    scope = body.get('scope')
    model_path = os.path.realpath(os.path.join(settings.SUMMARY_BASE_DIR, model_file))
    try:
        response = convert_from_ui(model_path, scope, input_nodes, output_nodes, output_folder)
    except ConvertFromUIError as e:
        raise ConvertFromUIError(str(e))
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
