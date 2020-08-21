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
"""Utils method."""
import os
import stat


def generate_file(file, template_content, mode=None):
    """Create a file and write content."""
    os.makedirs(os.path.dirname(file), mode=stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR, exist_ok=True)
    with open(file, 'w') as fp:
        fp.write(template_content)
    if mode:
        os.chmod(file, mode)
    else:
        os.chmod(file, stat.S_IRUSR)
