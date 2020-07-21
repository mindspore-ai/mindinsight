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
"""The memory collector."""

import psutil
from psutil._common import bytes2human


def collect_mem(readable=False):
    """
    Collect the virtual memory info.

    Args:
        readable (bool): Read the sizes like 1K, 234M, 2G etc.

    Returns:
        dict, the virtual memory info.
    """
    mem = psutil.virtual_memory()._asdict()
    if not readable:
        return dict(mem)
    return {k: v if k == 'percent' else bytes2human(v) for k, v in mem.items()}
