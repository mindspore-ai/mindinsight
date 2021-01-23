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
"""Common Tools."""
import imghdr
import math
import os

from numbers import Number
from urllib.parse import unquote

from mindinsight.datavisual.common.exceptions import MaxCountExceededError
from mindinsight.datavisual.common.exceptions import PathNotDirectoryError
from mindinsight.datavisual.common.log import logger
from mindinsight.utils import exceptions
from mindinsight.utils.exceptions import UnknownError

_IMG_EXT_TO_MIMETYPE = {
    'bmp': 'image/bmp',
    'gif': 'image/gif',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}
_DEFAULT_IMAGE_MIMETYPE = 'application/octet-stream'


def find_app_package():
    """Find package in current directory."""
    backend_dir = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, os.pardir, "backend"))
    packages = []
    for file in os.listdir(backend_dir):
        file_path = os.path.join(backend_dir, file)
        if os.path.isfile(file_path):
            continue
        if not os.path.isfile(os.path.join(file_path, '__init__.py')):
            continue
        rel_path = os.path.relpath(file_path, backend_dir)
        package = rel_path.replace(os.path.sep, '.')
        package = f"mindinsight.backend.{package}"
        packages.append(package)
    return packages


def to_str(bytes_or_text, encode="utf-8"):
    """Bytes transform string."""
    if isinstance(bytes_or_text, bytes):
        return bytes_or_text.decode(encode)
    if isinstance(bytes_or_text, str):
        return bytes_or_text

    raise TypeError("Param isn't str or bytes type, param={}".format(bytes_or_text))


def to_int(param, param_name):
    """
    Transfer param to int type.

    Args:
        param (Any): A param transformed.
        param_name (str): Param name.

    Returns:
        int, value after transformed.

    """
    try:
        param = int(param)
    except ValueError:
        raise exceptions.ParamTypeError(param_name, 'Integer')
    return param


def to_float(param, param_name):
    """
    Transfer param to float type.

    Args:
        param (Any): A param transformed.
        param_name (str): Param name.

    Returns:
        float, value after transformed.

    """
    try:
        param = float(param)
    except ValueError:
        raise exceptions.ParamTypeError(param_name, 'Float')
    return param


def str_to_bool(param, param_name):
    """
    Check param and transform it to bool.

    Args:
        param (str): 'true' or 'false' is valid.
        param_name (str): Param name.

    Returns:
        bool, if param is 'true', case insensitive.

    Raises:
        ParamValueError: If the value of param is not 'false' and 'true'.

    """
    if not isinstance(param, str):
        raise exceptions.ParamTypeError(param_name, 'str')

    if param.lower() not in ['false', 'true']:
        raise exceptions.ParamValueError("The value of %s must be 'false' or 'true'." % param_name)
    param = (param.lower() == 'true')

    return param


def get_img_mimetype(img_data):
    """
    Recognize image headers and generate image MIMETYPE.

    Args:
        img_data (bin): Binary character stream of image.

    Returns:
        str, a MIMETYPE of the give image.
    """
    image_type = imghdr.what(None, img_data)
    mimetype = _IMG_EXT_TO_MIMETYPE.get(image_type, _DEFAULT_IMAGE_MIMETYPE)
    return mimetype


def get_train_id(request):
    """
    Get train ID from request query string and unquote content.

    Args:
        request (FlaskRequest): Http request instance.

    Returns:
        str, unquoted train ID.
    """
    train_id = request.args.get('train_id')
    if train_id is not None:
        try:
            train_id = unquote(train_id, errors='strict')
        except UnicodeDecodeError:
            raise exceptions.UrlDecodeError('Unquote train id error with strict mode')
    return train_id


def get_profiler_dir(request):
    """
    Get train ID from request query string and unquote content.

    Args:
        request (FlaskRequest): Http request instance.

    Returns:
        str, unquoted train ID.
    """
    profiler_dir = request.args.get('profile')
    if profiler_dir is not None:
        try:
            profiler_dir = unquote(profiler_dir, errors='strict')
        except UnicodeDecodeError:
            raise exceptions.UrlDecodeError('Unquote profiler_dir error with strict mode')
    return profiler_dir


def unquote_args(request, arg_name):
    """
    Get args from request query string and unquote content.

    Args:
        request (FlaskRequest): Http request instance.
        arg_name (str): The name of arg.

    Returns:
        str, unquoted arg.
    """
    arg_value = request.args.get(arg_name, "")
    if arg_value is not None:
        try:
            arg_value = unquote(arg_value, errors='strict')
        except UnicodeDecodeError:
            raise exceptions.ParamValueError('Unquote error with strict mode')
    return arg_value


def get_device_id(request):
    """
    Get device ID from request query string and unquote content.

    Args:
        request (FlaskRequest): Http request instance.

    Returns:
        str, unquoted device ID.
    """
    device_id = request.args.get('device_id')
    if device_id is not None:
        try:
            device_id = unquote(device_id, errors='strict')
        except UnicodeDecodeError:
            raise exceptions.UrlDecodeError('Unquote train id error with strict mode')
    else:
        device_id = "0"
    return device_id


def if_nan_inf_to_none(name, value):
    """
    Transform value to None if it is NaN or Inf.

    Args:
        name (str): Name of value.
        value (float): A number transformed.

    Returns:
        float, if value is NaN or Inf, return None.

    """
    if not isinstance(value, Number):
        raise exceptions.ParamTypeError(name, 'number')
    if math.isnan(value) or math.isinf(value):
        value = None
    return value


def exception_wrapper(func):
    """Exception wrapper"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (PathNotDirectoryError, FileNotFoundError) as err:
            # except PathNotDirectoryError and FileNotFoundError as they are on warning level
            logger.warning(str(err))
        except Exception as exc:
            logger.exception(exc)
            raise UnknownError(str(exc))
    return wrapper


def exception_no_raise_wrapper(func):
    """Don't raise exception to avoid printing error in stdout and log error in the log file."""
    def wrapper(*args, **kwargs):
        try:
            return exception_wrapper(func)(*args, **kwargs)
        except UnknownError as err:
            logger.error(str(err))
    return wrapper

class Counter:
    """Count accumulator with limit checking."""

    def __init__(self, max_count=None, init_count=0):
        self._count = init_count
        self._max_count = max_count

    def add(self, value=1):
        """Add value."""
        if self._max_count is not None and self._count + value > self._max_count:
            raise MaxCountExceededError()
        self._count += value
