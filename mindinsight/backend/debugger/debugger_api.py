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
"""Debugger restful api."""
import json
from urllib.parse import unquote

from flask import Blueprint, jsonify, request

from mindinsight.conf import settings
from mindinsight.debugger.debugger_server import DebuggerServer
from mindinsight.utils.exceptions import ParamValueError

BLUEPRINT = Blueprint("debugger", __name__,
                      url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


def _initialize_debugger_server():
    """Initialize a debugger server instance."""
    enable_debugger = settings.ENABLE_DEBUGGER if hasattr(settings, 'ENABLE_DEBUGGER') else False
    server = None
    if enable_debugger:
        server = DebuggerServer()
    return server


def _unquote_param(param):
    """
    Decode parameter value.

    Args:
        param (str): Encoded param value.

    Returns:
        str, decoded param value.
    """
    if isinstance(param, str):
        try:
            param = unquote(param, errors='strict')
        except UnicodeDecodeError:
            raise ParamValueError('Unquote error with strict mode.')
    return param


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
        body = json.loads(body if body else "{}")
    except Exception:
        raise ParamValueError("Json data parse failed.")
    return body


def _wrap_reply(func, *args, **kwargs):
    """Serialize reply."""
    reply = func(*args, **kwargs)
    return jsonify(reply)


@BLUEPRINT.route("/debugger/poll-data", methods=["GET"])
def poll_data():
    """
    Wait for data to be updated on UI.

    Get data from server and display the change on UI.

    Returns:
        str, the updated data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/poll-data?pos=xx
    """
    pos = request.args.get('pos')

    reply = _wrap_reply(BACKEND_SERVER.poll_data, pos)

    return reply


@BLUEPRINT.route("/debugger/search", methods=["GET"])
def search():
    """
    Search nodes in specified watchpoint.

    Returns:
        str, the required data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/search?name=mock_name&watch_point_id=1
    """
    name = request.args.get('name')
    graph_name = request.args.get('graph_name')
    watch_point_id = int(request.args.get('watch_point_id', 0))
    node_category = request.args.get('node_category')
    reply = _wrap_reply(BACKEND_SERVER.search, {'name': name,
                                                'graph_name': graph_name,
                                                'watch_point_id': watch_point_id,
                                                'node_category': node_category})

    return reply


@BLUEPRINT.route("/debugger/retrieve_node_by_bfs", methods=["GET"])
def retrieve_node_by_bfs():
    """
    Search node by bfs.

    Returns:
        str, the required data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/retrieve_node_by_bfs?name=node_name&ascend=true
    """
    name = request.args.get('name')
    graph_name = request.args.get('graph_name')
    ascend = request.args.get('ascend', 'false')
    ascend = ascend == 'true'
    reply = _wrap_reply(BACKEND_SERVER.retrieve_node_by_bfs, name, graph_name, ascend)

    return reply


@BLUEPRINT.route("/debugger/tensor-comparisons", methods=["GET"])
def tensor_comparisons():
    """
    Get tensor comparisons.

    Returns:
        str, the required data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/tensor-comparisons
    """
    name = request.args.get('name')
    detail = request.args.get('detail', 'data')
    shape = _unquote_param(request.args.get('shape'))
    tolerance = request.args.get('tolerance', '0')
    reply = _wrap_reply(BACKEND_SERVER.tensor_comparisons, name, shape, detail, tolerance)

    return reply


@BLUEPRINT.route("/debugger/retrieve", methods=["POST"])
def retrieve():
    """
    Retrieve data according to mode and params.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/retrieve
    """
    body = _read_post_request(request)
    mode = body.get('mode')
    params = body.get('params')
    reply = _wrap_reply(BACKEND_SERVER.retrieve, mode, params)
    return reply


@BLUEPRINT.route("/debugger/tensor-history", methods=["POST"])
def retrieve_tensor_history():
    """
    Retrieve data according to mode and params.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/tensor-history
    """
    body = _read_post_request(request)
    name = body.get('name')
    graph_name = body.get('graph_name')
    reply = _wrap_reply(BACKEND_SERVER.retrieve_tensor_history, name, graph_name)
    return reply


@BLUEPRINT.route("/debugger/tensors", methods=["GET"])
def retrieve_tensor_value():
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/tensors?name=tensor_name&detail=data&shape=[1,1,:,:]
    """
    name = request.args.get('name')
    detail = request.args.get('detail')
    shape = _unquote_param(request.args.get('shape'))
    graph_name = request.args.get('graph_name')
    prev = bool(request.args.get('prev') == 'true')

    reply = _wrap_reply(BACKEND_SERVER.retrieve_tensor_value, name, detail, shape, graph_name, prev)
    return reply


@BLUEPRINT.route("/debugger/create-watchpoint", methods=["POST"])
def create_watchpoint():
    """
    Create watchpoint.

    Returns:
        str, watchpoint id.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/create-watchpoint
    """
    params = _read_post_request(request)
    params['watch_condition'] = params.pop('condition', None)
    reply = _wrap_reply(BACKEND_SERVER.create_watchpoint, params)
    return reply


@BLUEPRINT.route("/debugger/update-watchpoint", methods=["POST"])
def update_watchpoint():
    """
    Update watchpoint.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/update-watchpoint
    """
    params = _read_post_request(request)
    reply = _wrap_reply(BACKEND_SERVER.update_watchpoint, params)
    return reply


@BLUEPRINT.route("/debugger/delete-watchpoint", methods=["POST"])
def delete_watchpoint():
    """
    delete watchpoint.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/delete-watchpoint
    """
    body = _read_post_request(request)

    watch_point_id = body.get('watch_point_id')

    reply = _wrap_reply(BACKEND_SERVER.delete_watchpoint, watch_point_id)

    return reply


@BLUEPRINT.route("/debugger/control", methods=["POST"])
def control():
    """
    Control request.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/control
    """
    params = _read_post_request(request)
    reply = _wrap_reply(BACKEND_SERVER.control, params)

    return reply


@BLUEPRINT.route("/debugger/recheck", methods=["POST"])
def recheck():
    """
    Recheck request.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/recheck
    """
    reply = _wrap_reply(BACKEND_SERVER.recheck)

    return reply


@BLUEPRINT.route("/debugger/tensor-graphs", methods=["GET"])
def retrieve_tensor_graph():
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/tensor-graphs?tensor_name=tensor_name&graph_name=graph_name
    """
    tensor_name = request.args.get('tensor_name')
    graph_name = request.args.get('graph_name')
    reply = _wrap_reply(BACKEND_SERVER.retrieve_tensor_graph, tensor_name, graph_name)
    return reply


@BLUEPRINT.route("/debugger/tensor-hits", methods=["GET"])
def retrieve_tensor_hits():
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/tensor-hits?tensor_name=tensor_name&graph_name=graph_name
    """
    tensor_name = request.args.get('tensor_name')
    graph_name = request.args.get('graph_name')
    reply = _wrap_reply(BACKEND_SERVER.retrieve_tensor_hits, tensor_name, graph_name)
    return reply


@BLUEPRINT.route("/debugger/search-watchpoint-hits", methods=["POST"])
def search_watchpoint_hits():
    """
    Search watchpoint hits by group condition.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/search-watchpoint-hits
    """
    body = _read_post_request(request)
    group_condition = body.get('group_condition')
    reply = _wrap_reply(BACKEND_SERVER.search_watchpoint_hits, group_condition)
    return reply


BACKEND_SERVER = _initialize_debugger_server()


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
    if BACKEND_SERVER:
        BACKEND_SERVER.start()
