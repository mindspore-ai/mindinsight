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
"""ST for profiler."""
import os

RAW_DATA_BASE = os.path.realpath(os.path.join(os.path.dirname(__file__), '../../../utils/resource'))
RAW_DATA = os.path.realpath(os.path.join(RAW_DATA_BASE, 'JOB1'))
PROFILER_DIR = os.path.realpath(os.path.join(RAW_DATA_BASE, 'profiler'))
MAREY_DIR = os.path.realpath(os.path.join(RAW_DATA_BASE, 'marey_graph'))
