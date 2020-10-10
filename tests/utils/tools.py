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
"""
Description: This file is used for some common util.
"""
import io
import os
import shutil
import time
import json

from urllib.parse import urlencode

import numpy as np
from PIL import Image

from mindinsight.datavisual.common.enums import DataManagerStatus


def get_url(url, params):
    """
    Concatenate the URL and params.

    Args:
        url (str): A link requested. For example, http://example.com.
        params (dict): A dict consists of params. For example, {'offset': 1, 'limit':'100}.

    Returns:
        str, like http://example.com?offset=1&limit=100

    """

    return url + '?' + urlencode(params)


def delete_files_or_dirs(path_list):
    """Delete files or dirs in path_list."""
    for path in path_list:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def check_loading_done(data_manager, time_limit=15, first_sleep_time=0):
    """If loading data for more than `time_limit` seconds, exit."""
    if first_sleep_time > 0:
        time.sleep(first_sleep_time)
    start_time = time.time()
    while data_manager.status not in (DataManagerStatus.DONE.value, DataManagerStatus.INVALID.value):
        time_used = time.time() - start_time
        if time_used > time_limit:
            break
        time.sleep(0.1)
        continue
    return bool(data_manager.status == DataManagerStatus.DONE.value)


def get_image_tensor_from_bytes(image_string):
    """Get image tensor from bytes."""
    img = Image.open(io.BytesIO(image_string))
    image_tensor = np.array(img)

    return image_tensor


def compare_result_with_file(result, expected_file_path):
    """Compare result with file which contain the expected results."""
    with open(expected_file_path, 'r') as file:
        expected_results = json.load(file)
        assert result == expected_results


def deal_float_for_dict(res: dict, expected_res: dict, decimal_num=2):
    """
    Deal float rounded to specified decimals in dict.

    For example:
        res:{
                "model_lineages": {
                    "metric": {"acc": 0.1234561}
                }
            }
        expected_res:
            {
                "model_lineages": {
                    "metric": {"acc": 0.1234562}
                }
            }
    After:
        res:{
                "model_lineages": {
                    "metric": {"acc": 0.12346}
                }
            }
        expected_res:
            {
                "model_lineages": {
                    "metric": {"acc": 0.12346}
                }
            }

    Args:
        res (dict）: e.g.
            {
                "model_lineages": {
                    "metric": {"acc": 0.1234561}
                }
            }
        expected_res (dict):
            {
                "model_lineages": {
                    "metric": {"acc": 0.1234562}
                }
            }
        decimal_num (int): decimal rounded digits.

    """
    for key in res:
        value = res[key]
        expected_value = expected_res[key]
        if isinstance(value, dict):
            deal_float_for_dict(value, expected_value)
        elif isinstance(value, float):
            res[key] = round(value, decimal_num)
            expected_res[key] = round(expected_value, decimal_num)


def _deal_float_for_list(list1, list2, decimal_num):
    """Deal float for list1 and list2."""
    index = 0
    for _ in list1:
        deal_float_for_dict(list1[index], list2[index], decimal_num)
        index += 1


def assert_equal_lineages(lineages1, lineages2, assert_func, decimal_num=2):
    """Assert float almost equal for lineage data."""
    if isinstance(lineages1, list) and isinstance(lineages2, list):
        _deal_float_for_list(lineages1, lineages2, decimal_num)
    elif lineages1.get('object') is not None and lineages2.get('object') is not None:
        _deal_float_for_list(lineages1['object'], lineages2['object'], decimal_num)
    else:
        deal_float_for_dict(lineages1, lineages2, decimal_num)
    assert_func(lineages1, lineages2)
