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
"""Source file module."""
import os
import shutil
import stat
from pathlib import Path

from mindinsight.wizard.common.exceptions import OSPermissionError, TemplateFileError


class SourceFile:
    """Network code generator."""
    file_relative_path = ''
    template_file_path = ''
    content = ''

    @staticmethod
    def _make_dir(directory):
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        os.makedirs(directory, mode=mode, exist_ok=True)
        return directory

    def write(self, project_directory):
        """Generate the network files."""
        template_file_path = Path(self.template_file_path)
        if not template_file_path.is_file():
            raise TemplateFileError("Template file %s is not exist." % self.template_file_path)
        new_file_path = os.path.join(project_directory, self.file_relative_path)
        self._make_dir(os.path.dirname(new_file_path))
        with open(new_file_path, 'w', encoding='utf-8') as fp:
            fp.write(self.content)
        try:
            shutil.copymode(self.template_file_path, new_file_path)
            os.chmod(new_file_path, stat.S_IRUSR | stat.S_IWUSR)
            self.set_writeable(new_file_path)
            if new_file_path.endswith('.sh'):
                self.set_executable(new_file_path)
        except OSError:
            raise OSPermissionError("Notice: Set permission bits failed on %s." % new_file_path)

    @staticmethod
    def set_writeable(file_name):
        """Add write permission."""
        if not os.access(file_name, os.W_OK):
            file_stat = os.stat(file_name)
            permissions = stat.S_IMODE(file_stat.st_mode) | stat.S_IWUSR
            os.chmod(file_name, permissions)

    @staticmethod
    def set_executable(file_name):
        """Add executable permission."""
        if not os.access(file_name, os.X_OK):
            file_stat = os.stat(file_name)
            permissions = stat.S_IMODE(file_stat.st_mode) | stat.S_IXUSR
            os.chmod(file_name, permissions)
