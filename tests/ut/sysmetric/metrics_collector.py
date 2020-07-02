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
"""Test the metrics collector."""
from os import cpu_count

from mindinsight.sysmetric.collector import collect_cpu, collect_mem, collect_npu


def test_collect_cpu():
    overall = collect_cpu(percent=True)
    assert isinstance(overall, dict)
    for value in overall.values():
        assert 0 <= value <= 100
    for key in 'user', 'system', 'idle':
        assert key in overall
    cores = collect_cpu(percpu=True)
    assert isinstance(cores, list) and len(cores) == cpu_count()


def test_collect_mem():
    mem = collect_mem()
    assert 'total' in mem
    assert 'available' in mem
    assert mem['total'] > mem['available']


def test_collect_npu():
    npu = collect_npu()
    if npu is not None:
        assert len(npu) == 8
