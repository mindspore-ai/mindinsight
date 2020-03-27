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
"""Validate the input path."""
import os
from typing import Union, List
from marshmallow import ValidationError


def safe_normalize_path(
        path,
        raise_key,
        safe_prefixes: Union[None, List[str]],
        check_absolute_path=False,
        allow_parent_dir=False,
):
    """
    Returns safe normalized path.

    This func validates given path, and returns its normalized form. If
    safe_prefixes is given, this func will check whether the path is safe.

    Note:
        This func is not compatible with windows.

        Caller should check returned path to ensure safety according to
        business logic.

        File scheme (rfc8089) is currently not supported.

    Args:
        path (str): Path to be normalized.

        raise_key (str): The exception raise key

        safe_prefixes (list[str]): If not none, path must startswith one of the
            safe_prefixes. Set this arg to [] will cause all paths considered
            unsafe. Normally, prefix in this arg should end with "/".

        check_absolute_path (bool): Whether check path is absolute.

        allow_parent_dir (bool): Whether allow parent dir in path.

    Returns:
        str, normalized path.
    """
    normalized_path = validate_and_normalize_path(
        path,
        raise_key=raise_key,
        check_absolute_path=check_absolute_path,
        allow_parent_dir=allow_parent_dir,
    )

    if safe_prefixes is None:
        return normalized_path

    normalized_str = str(normalized_path)
    for prefix in safe_prefixes:
        if normalized_str.startswith(prefix):
            return normalized_path

    raise ValidationError({raise_key: {"The path is invalid!"}})


def validate_and_normalize_path(
        path,
        raise_key,
        check_absolute_path=False,
        allow_parent_dir=False,
):
    """
    Validates path and returns its normalized form.

    If path has a valid scheme, treat path as url, otherwise consider path a
    unix local path.

    Note:
        File scheme (rfc8089) is currently not supported.

    Args:
        path (str): Path to be normalized.
        raise_key (str): The exception raise key.
        check_absolute_path (bool): Whether check path scheme is supported.
        allow_parent_dir (bool): Whether allow parent dir in path.


    Returns:
        str, normalized path.
    """
    if not path:
        raise ValidationError({raise_key: {"The path is invalid!"}})

    path_str = str(path)
    if not allow_parent_dir:
        path_components = path_str.split("/")
        if ".." in path_components:
            raise ValidationError({raise_key: {"The path is invalid!"}})

    # path does not have valid schema, treat it as unix local path.
    if check_absolute_path:
        if not path_str.startswith("/"):
            raise ValidationError({raise_key: {"The path is invalid!"}})
    try:
        # most unix systems allow
        normalized_path = os.path.realpath(path)
    except ValueError:
        raise ValidationError({raise_key: {"The path is invalid!"}})

    return normalized_path
