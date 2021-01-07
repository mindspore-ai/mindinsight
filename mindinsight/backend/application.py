# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
"""Web application module."""
import os
from importlib import import_module
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException

from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS

from mindinsight.conf import settings
from mindinsight.utils.hook import HookUtils
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.exceptions import RequestMethodNotAllowed
from mindinsight.datavisual.common import error_handler
from mindinsight.datavisual.utils.tools import find_app_package
from mindinsight.datavisual.utils.tools import get_img_mimetype
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.log import setup_logger


def get_security_headers():
    """Get security headers."""
    domain_white_list = []
    for hook in HookUtils.instance().hooks():
        domain_white_list += hook.register_secure_domains()

    content_security_policy = {
        'img-src': ["'self'", 'data:'],
        'style-src': ["'self'", "'unsafe-inline'"],
        'frame-src': ["'self'"] + domain_white_list,
        'frame-ancestors': ["'self'"] + domain_white_list,
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-eval'"]
    }

    headers = {
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'X-Content-Type-Options': 'nosniff',
        'Access-Control-Allow-Methods': ', '.join(settings.SUPPORT_REQUEST_METHODS),
        'Content-Security-Policy': '; '.join([
            f"{k} {' '.join(v)}" for k, v in content_security_policy.items()
        ]),
        'X-Download-Options': 'noopen',
        'Cache-Control': 'no-store',
        'Pragma': 'no-cache'
    }

    return list(headers.items())


SECURITY_HEADERS = get_security_headers()


class CustomResponse(Response):
    """Define custom response."""
    def __init__(self, response=None, **kwargs):
        headers = kwargs.get("headers")
        security_headers = list(SECURITY_HEADERS)
        if isinstance(response, bytes):
            mimetype = get_img_mimetype(response)
            security_headers.append(('Content-Type', mimetype))
        if headers is None:
            headers = Headers(security_headers)
        else:
            for header in security_headers:
                headers.add(*header)
        kwargs['headers'] = headers
        super(CustomResponse, self).__init__(response, **kwargs)


def _init_app_module(app):
    """
    Init app module.

    Args:
        app (Flask): An instance of Flask.
    """
    packages = find_app_package()
    gunicorn_logger = setup_logger("gunicorn", "error")
    for package in packages:
        try:
            app_module = import_module(package)
            gunicorn_logger.info("[%s].init_module starts.", package)
            app_module.init_module(app)
            gunicorn_logger.info("[%s].init_module ends.", package)
        except AttributeError:
            logger.debug('[%s].init_module not exists.', package)


def before_request():
    """A function to run before each request."""
    if request.method not in settings.SUPPORT_REQUEST_METHODS:
        raise RequestMethodNotAllowed()


def create_app():
    """Set flask APP config, and start the data manager."""
    gunicorn_logger = setup_logger("gunicorn", "error")
    gunicorn_logger.info("create_app starts.")
    static_url_path = settings.URL_PATH_PREFIX + "/static"
    static_folder_path = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'ui', 'dist', 'static'))

    app = Flask(__name__, static_url_path=static_url_path, static_folder=static_folder_path)
    app.config['JSON_SORT_KEYS'] = False

    if settings.ENABLE_CORS:
        CORS(app, supports_credentials=True)

    app.before_request(before_request)

    app.register_error_handler(HTTPException, error_handler.handle_http_exception_error)
    app.register_error_handler(MindInsightException, error_handler.handle_mindinsight_error)
    app.register_error_handler(Exception, error_handler.handle_unknown_error)

    app.response_class = CustomResponse

    _init_app_module(app)
    gunicorn_logger.info("create_app ends.")

    return app


APP = create_app()
