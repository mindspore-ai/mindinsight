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
"""Handle custom error."""
from urllib.parse import quote
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import MethodNotAllowed

from flask import request, jsonify

from mindinsight.datavisual.common.exceptions import RequestMethodNotAllowed
from mindinsight.datavisual.common.exceptions import RestfulApiNotExist
from mindinsight.datavisual.common.log import restful_logger as logger
from mindinsight.utils.exceptions import UnknownError
from mindinsight.utils.exceptions import FileSystemPermissionError


def handle_http_exception_error(ex):
    """Handle http exception error."""
    logger.warning('%r %r, detail: %r', request.method, quote(request.path), str(ex))
    if isinstance(ex, NotFound):
        error = RestfulApiNotExist()
    elif isinstance(ex, MethodNotAllowed):
        error = RequestMethodNotAllowed()
    else:
        logger.exception(ex)
        error = UnknownError('System error or http error.')
    res_body = {"error_code": error.error_code, "error_msg": error.message}
    return jsonify(res_body), error.http_code


def handle_mindinsight_error(ex):
    """Handle mindinsight error."""
    if int(ex.http_code) < 500:
        logger.warning('%r %r detail: %r', request.method, quote(request.path), ex.message)
    else:
        logger.error('%r %r detail: %r', request.method, quote(request.path), ex.message)
        logger.exception(ex)
    res_body = dict(error_code=ex.error_code, error_msg=ex.message)
    return jsonify(res_body), ex.http_code


def handle_unknown_error(ex):
    """Handle unknown error."""
    logger.error('%r %r detail: %r', request.method, quote(request.path), str(ex))
    logger.exception(ex)
    if isinstance(ex, PermissionError):
        error = FileSystemPermissionError('File System Permission Error')
    else:
        error = UnknownError('System error.')
    res_body = dict(error_code=error.error_code, error_msg=error.message)
    return jsonify(res_body), error.http_code
