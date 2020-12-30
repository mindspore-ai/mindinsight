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
import re
from typing import Union, List
from urllib.parse import unquote

from marshmallow import ValidationError

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerParamValueErrorException, ProfilerDirNotFoundException
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.profiler.common.log import logger as log


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


def validate_and_normalize_profiler_path(summary_dir, summary_base_dir):
    """
    Validate and normalize profiler path.

    Args:
        summary_dir (str): The relative path of summary directory.
        summary_base_dir (str): The summary base directory.

    Returns:
        str, normalized path of profiler directory.
    """
    profiler_directory_pattern = r'^profiler.*'
    if not summary_dir:
        raise ProfilerParamValueErrorException('The file dir does not exist.')
    try:
        unquote_path = unquote(summary_dir, errors='strict')
    except UnicodeDecodeError:
        raise ProfilerParamValueErrorException('Unquote error with strict mode')
    train_job_dir = os.path.join(summary_base_dir, unquote_path)
    try:
        train_job_dir_abs = validate_and_normalize_path(train_job_dir, 'train_job_dir')
    except ValidationError:
        log.error('train_job dir <%s> is invalid', train_job_dir)
        raise ProfilerParamValueErrorException('train_job dir is invalid.')
    if not os.path.exists(train_job_dir_abs):
        raise TrainJobNotExistError(error_detail=train_job_dir_abs)

    try:
        profiler_name_list = []
        for dir_name in os.listdir(train_job_dir_abs):
            search_res = re.search(profiler_directory_pattern, dir_name)
            if search_res:
                profiler_name_list.append(search_res[0])
        profiler_name_list.sort()
        profiler_name_newest = profiler_name_list[-1]
        profiler_dir = os.path.join(summary_base_dir, unquote_path, profiler_name_newest)
    except ValidationError:
        log.error('no valid profiler dir under <%s>', train_job_dir_abs)
        raise ProfilerDirNotFoundException('Profiler dir not found.')
    try:
        profiler_dir = validate_and_normalize_path(profiler_dir, 'profiler')
    except ValidationError:
        log.error('profiler dir <%s> is invalid', profiler_dir)
        raise ProfilerParamValueErrorException('Profiler dir is invalid.')

    return profiler_dir
