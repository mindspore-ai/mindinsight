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
"""The cpu collector."""

import psutil


def collect_cpu(percpu=False, percent=False):
    """
    Collect the cpu info.

    Args:
        percpu (bool): To return a list of cpu info for each logical CPU on the system.
        percent (bool): Represent the sized in percentage.

    Returns:
        Union[dict, List[dict]], the CPUs info.
    """
    if percent:
        times = psutil.cpu_times_percent(percpu=percpu)
    else:
        times = psutil.cpu_times(percpu=percpu)
    if not percpu:
        return dict(times._asdict())
    return [dict(time._asdict()) for time in times]
