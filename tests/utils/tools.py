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
"""
Description: This file is used for some common util.
"""
import io
import os
import shutil
import time
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
    while data_manager.status != DataManagerStatus.DONE.value:
        time_used = time.time() - start_time
        if time_used > time_limit:
            break
        time.sleep(0.1)
        continue


def get_image_tensor_from_bytes(image_string):
    """Get image tensor from bytes."""
    img = Image.open(io.BytesIO(image_string))
    image_tensor = np.array(img)

    return image_tensor
