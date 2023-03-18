# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""Define the util."""

MS_VERSION = '1.0.x'


def version_match(ms_version, mi_version):
    """
    Judge if the version of Mindinsight and Mindspore is matched.
    0 means the version is totally matched;
    1 means the major version is matched but the minor version is mismatch;
    2 means the version is totally mismatch.
    """
    if not ms_version:
        ms_version = MS_VERSION
    mi_major, mi_minor = mi_version.split('.')[:2]
    ms_major, ms_minor = ms_version.split('.')[:2]
    mi_major_num = int(mi_major)
    mi_minor_num = int(mi_minor)
    ms_major_num = int(ms_major)
    ms_minor_num = int(ms_minor)
    if ms_major_num == mi_major_num and ms_minor_num == mi_minor_num:
        return 0
    if ms_major_num == mi_major_num and ms_minor_num > mi_minor_num:
        return 1
    return 2
