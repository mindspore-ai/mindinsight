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
"""MindSpore Mock Interface"""
import os
import time
import socket


class SummaryRecord:
    """Mock the MindSpore SummaryRecord class."""

    def __init__(self,
                 log_dir: str,
                 file_prefix: str = "events",
                 file_suffix: str = "_MS",
                 create_time=int(time.time())):
        self.log_dir = log_dir
        self.prefix = file_prefix
        self.suffix = file_suffix
        hostname = socket.gethostname()
        file_name = f'{file_prefix}.out.events.summary.{str(create_time)}.{hostname}{file_suffix}'

        self.full_file_name = os.path.join(log_dir, file_name)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=mode, exist_ok=True)
        with open(self.full_file_name, 'wb'):
            pass

    def flush(self):
        """Mock flush method."""

    def close(self):
        """Mock close method."""
