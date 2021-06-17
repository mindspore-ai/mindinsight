# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
import weakref
from urllib.parse import unquote

from flask import Blueprint, jsonify, request, Response

from mindinsight.conf import settings
from mindinsight.debugger.session_manager import SessionManager
from mindinsight.utils.exceptions import ParamMissError, ParamValueError, ParamTypeError

BLUEPRINT = Blueprint("debugger", __name__,
                      url_prefix=settings.URL_PATH_PREFIX + settings.API_PREFIX)


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


def to_int(param, param_name):
    """Transfer param to int type."""
    try:
        param = int(param)
    except ValueError:
        raise ParamTypeError(param_name, 'Integer')
    return param


def _wrap_reply(func, *args, **kwargs):
    """Serialize reply."""
    reply = func(*args, **kwargs)
    return jsonify(reply)


@BLUEPRINT.route("/debugger/sessions/<session_id>/poll-data", methods=["GET"])
def poll_data(session_id):
    """
    Wait for data to be updated on UI.

    Get data from server and display the change on UI.

    Returns:
        str, the updated data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/sessions/xxxx/poll-data?pos=xx
    """
    pos = request.args.get('pos')

    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).poll_data, pos)

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/search", methods=["GET"])
def search(session_id):
    """
    Search nodes in specified watchpoint.

    Returns:
        str, the required data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/sessions/xxxx/search?name=mock_name&watch_point_id=1
    """
    name = request.args.get('name')
    graph_name = request.args.get('graph_name')
    watch_point_id = to_int(request.args.get('watch_point_id', 0), 'watch_point_id')
    node_category = request.args.get('node_category')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')
    stack_pattern = _unquote_param(request.args.get('stack_info_key_word'))
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).search,
                        {'name': name,
                         'graph_name': graph_name,
                         'watch_point_id': watch_point_id,
                         'node_category': node_category,
                         'rank_id': rank_id,
                         'stack_pattern': stack_pattern})

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-comparisons", methods=["GET"])
def tensor_comparisons(session_id):
    """
    Get tensor comparisons.

    Returns:
        str, the required data.

    Examples:
        >>> Get http://xxxx/v1/mindinsight/debugger/sessions/xxxx/tensor-comparisons
    """
    name = request.args.get('name')
    detail = request.args.get('detail', 'data')
    shape = _unquote_param(request.args.get('shape'))
    graph_name = request.args.get('graph_name', '')
    tolerance = request.args.get('tolerance', '0')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).tensor_comparisons, name, shape,
                        detail, tolerance, rank_id, graph_name)

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/retrieve", methods=["POST"])
def retrieve(session_id):
    """
    Retrieve data according to mode and params.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/retrieve
    """
    body = _read_post_request(request)
    mode = body.get('mode')
    params = body.get('params')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).retrieve, mode, params)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-history", methods=["POST"])
def retrieve_tensor_history(session_id):
    """
    Retrieve data according to mode and params.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/tensor-history
    """
    body = _read_post_request(request)
    name = body.get('name')
    graph_name = body.get('graph_name')
    rank_id = to_int(body.get('rank_id', 0), 'rank_id')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).retrieve_tensor_history, name, graph_name,
                        rank_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensors", methods=["GET"])
def retrieve_tensor_value(session_id):
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/sessions/xxxx/tensors?name=tensor_name&detail=data&shape=[1,1,:,:]
    """
    name = request.args.get('name')
    detail = request.args.get('detail')
    shape = _unquote_param(request.args.get('shape'))
    graph_name = request.args.get('graph_name')
    prev = bool(request.args.get('prev') == 'true')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')

    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).retrieve_tensor_value, name, detail,
                        shape, graph_name, prev, rank_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/create-watchpoint", methods=["POST"])
def create_watchpoint(session_id):
    """
    Create watchpoint.

    Returns:
        str, watchpoint id.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/create-watchpoint
    """
    params = _read_post_request(request)
    params['watch_condition'] = params.pop('condition', None)
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).create_watchpoint, params)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/update-watchpoint", methods=["POST"])
def update_watchpoint(session_id):
    """
    Update watchpoint.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/update-watchpoint
    """
    params = _read_post_request(request)
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).update_watchpoint, params)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/delete-watchpoint", methods=["POST"])
def delete_watchpoint(session_id):
    """
    Delete watchpoint.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/delete-watchpoint
    """
    body = _read_post_request(request)

    watch_point_id = body.get('watch_point_id')

    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).delete_watchpoint, watch_point_id)

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/control", methods=["POST"])
def control(session_id):
    """
    Control request.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/control
    """
    params = _read_post_request(request)
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).control, params)

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/recheck", methods=["POST"])
def recheck(session_id):
    """
    Recheck request.

    Returns:
        str, reply message.

    Raises:
        MindInsightException: If method fails to be called.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/recheck
    """
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).recheck)

    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-graphs", methods=["GET"])
def retrieve_tensor_graph(session_id):
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/sessions/xxxx/tensor-graphs?tensor_name=xxx&graph_name=xxx
    """
    tensor_name = request.args.get('tensor_name')
    graph_name = request.args.get('graph_name')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).retrieve_tensor_graph, tensor_name,
                        graph_name, rank_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-hits", methods=["GET"])
def retrieve_tensor_hits(session_id):
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/sessions/xxxx/tensor-hits?tensor_name=xxx&graph_name=xxx
    """
    tensor_name = request.args.get('tensor_name')
    graph_name = request.args.get('graph_name')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).retrieve_tensor_hits, tensor_name,
                        graph_name, rank_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/search-watchpoint-hits", methods=["POST"])
def search_watchpoint_hits(session_id):
    """
    Search watchpoint hits by group condition.

    Returns:
        str, the required data.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions/xxxx/search-watchpoint-hits
    """
    body = _read_post_request(request)
    group_condition = body.get('group_condition')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).search_watchpoint_hits, group_condition)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/condition-collections", methods=["GET"])
def get_condition_collections(session_id):
    """Get condition collections."""
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).get_condition_collections)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/set-recommended-watch-points", methods=["POST"])
def set_recommended_watch_points(session_id):
    """Set recommended watch points."""
    body = _read_post_request(request)
    request_body = body.get('requestBody')
    if request_body is None:
        raise ParamMissError('requestBody')

    set_recommended = request_body.get('set_recommended')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).set_recommended_watch_points,
                        set_recommended)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-files/load", methods=["POST"])
def load(session_id):
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxx/v1/mindinsight/debugger/sessions/xxxx/tensor-files/load
    """
    body = _read_post_request(request)
    name = body.get('name')
    graph_name = body.get('graph_name')
    rank_id = to_int(body.get('rank_id', 0), 'rank_id')
    prev = bool(body.get('prev') == 'true')
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).load, name, prev, graph_name, rank_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/tensor-files/download", methods=["GET"])
def download(session_id):
    """
    Retrieve tensor value according to name and shape.

    Returns:
        str, the required data.

    Examples:
        >>> GET http://xxx/v1/mindinsight/debugger/sessions/xxx/tensor-files/download?name=name&graph_name=xxx&prev=xxx
    """
    name = request.args.get('name')
    graph_name = request.args.get('graph_name')
    rank_id = to_int(request.args.get('rank_id', 0), 'rank_id')
    prev = bool(request.args.get('prev') == 'true')
    file_name, file_path, clean_func = SessionManager.get_instance().get_session(session_id).\
        download(name, prev, graph_name, rank_id)

    def file_send():
        with open(file_path, 'rb') as fb:
            while True:
                data = fb.read(50 * 1024 * 1024)
                if not data:
                    break
                yield data

    response = Response(file_send(), content_type='application/octet-stream')
    response.headers["Content-disposition"] = 'attachment; filename=%s' % file_name
    weakref.finalize(response, clean_func,)
    return response


@BLUEPRINT.route("/debugger/sessions", methods=["POST"])
def create_session():
    """
    Get session id if session exist, else create a session.

    Returns:
        str, session id.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/sessions
    """
    body = _read_post_request(request)
    summary_dir = body.get('dump_dir')
    session_type = body.get('session_type')
    reply = _wrap_reply(SessionManager.get_instance().create_session, session_type, summary_dir)
    return reply


@BLUEPRINT.route("/debugger/sessions", methods=["GET"])
def get_train_jobs():
    """
    Check the current active sessions.

    Examples:
        >>> GET http://xxxx/v1/mindinsight/debugger/sessions
    """
    reply = _wrap_reply(SessionManager.get_instance().get_train_jobs)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/delete", methods=["POST"])
def delete_session(session_id):
    """
    Delete session by session id.

    Examples:
        >>> POST http://xxxx/v1/mindinsight/debugger/xxx/delete-session
    """
    reply = _wrap_reply(SessionManager.get_instance().delete_session, session_id)
    return reply


@BLUEPRINT.route("/debugger/sessions/<session_id>/stacks", methods=["GET"])
def get_stack_infos(session_id):
    """
    Get stack infos.

    Examples:
        >>> GET /v1/mindsight/debugger/sessions/<session_id>/stacks?key_word=xxx&offset=0
    """
    key_word = _unquote_param(request.args.get('key_word'))
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    filter_condition = {
        'pattern': key_word,
        'limit': limit,
        'offset': offset
    }
    reply = _wrap_reply(SessionManager.get_instance().get_session(session_id).get_stack_infos, filter_condition)
    return reply


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): The application obj.
    """
    app.register_blueprint(BLUEPRINT)
