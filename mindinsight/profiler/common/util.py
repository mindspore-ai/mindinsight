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
Profiler util.

This module provides the utils.
"""
import os


def analyse_device_list_from_profiler_dir(profiler_dir):
    """
    Analyse device list from profiler dir.

    Args:
        profiler_dir (str): The profiler data dir.

    Returns:
        list, the device_id list.
    """
    device_id_list = set()
    for _, _, filenames in os.walk(profiler_dir):
        for filename in filenames:
            profiler_file_prefix = ["output_op_compute_time", "output_data_preprocess_aicpu"]
            items = filename.split("_")
            device_num = items[-1].split(".")[0] if items[-1].split(".") else ""
            if device_num.isdigit() and '_'.join(items[:-1]) in profiler_file_prefix:
                device_id_list.add(device_num)

    return list(device_id_list)
