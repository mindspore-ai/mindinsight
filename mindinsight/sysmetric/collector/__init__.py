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
"""The metrics collector."""

from ._collect_cpu import collect_cpu
from ._collect_mem import collect_mem
from ._collect_npu import collect_npu

__all__ = [
    'collect_cpu',
    'collect_mem',
    'collect_npu',
]


def get_metrics():
    mem = collect_mem()
    return {
        'npu': collect_npu(),
        'cpu': {
            'overall': collect_cpu(percent=True),
            'percpu': collect_cpu(percpu=True, percent=True)
        },
        'memory': {
            'virtual': {
                'available': mem.get('available'),
                'used': mem.get('used')
            }
        }
    }
