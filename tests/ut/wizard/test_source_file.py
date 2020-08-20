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
"""Test SourceFile class."""
import os
import shutil
import stat
import tempfile

import pytest

from mindinsight.wizard.base.source_file import SourceFile
from tests.ut.wizard.utils import generate_file


class TestSourceFile:
    """Test SourceFile"""

    def setup_method(self):
        """Setup before call test method."""
        self._input_dir = tempfile.mkdtemp()
        self._output_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Tear down after call test method."""
        self._remove_dirs()
        self._input_dir = None
        self._output_dir = None

    def _remove_dirs(self):
        """Recursively delete a directory tree."""
        for temp_dir in [self._input_dir, self._output_dir]:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    @staticmethod
    def _generate_file(file, stat_mode):
        """Create a file and write content."""
        generate_file(file, "template file.", stat_mode)

    @pytest.mark.parametrize('params', [{
        'file_relative_path': 'src/config.py',
        'template_file_path': 'src/config.py-tpl'
    }, {
        'file_relative_path': 'src/lenet.py',
        'template_file_path': 'src/lenet.py-tpl'
    }, {
        'file_relative_path': 'README.md',
        'template_file_path': 'README.md-tpl'
    }, {
        'file_relative_path': 'train.py',
        'template_file_path': 'train.py-tpl'
    }])
    def test_write_py(self, params):
        """Test write python script file"""
        source_file = SourceFile()
        source_file.file_relative_path = params['file_relative_path']
        source_file.template_file_path = os.path.join(self._input_dir, params['template_file_path'])
        self._generate_file(source_file.template_file_path, stat.S_IRUSR)

        # start write
        source_file.write(self._output_dir)

        output_file_path = os.path.join(self._output_dir, source_file.file_relative_path)
        assert os.access(output_file_path, os.F_OK | os.R_OK | os.W_OK)
        assert stat.filemode(os.stat(output_file_path).st_mode) == '-rw-------'

    @pytest.mark.parametrize('params', [{
        'file_relative_path': 'scripts/run_eval.sh',
        'template_file_path': 'scripts/run_eval.sh-tpl'
    }, {
        'file_relative_path': 'run_distribute_train.sh',
        'template_file_path': 'run_distribute_train.sh-tpl'
    }])
    def test_write_sh(self, params):
        """Test write shell script file"""
        source_file = SourceFile()
        source_file.file_relative_path = params['file_relative_path']
        source_file.template_file_path = os.path.join(self._input_dir, params['template_file_path'])
        self._generate_file(source_file.template_file_path, stat.S_IRUSR)

        # start write
        source_file.write(self._output_dir)

        output_file_path = os.path.join(self._output_dir, source_file.file_relative_path)
        assert os.access(output_file_path, os.F_OK | os.R_OK | os.W_OK | os.X_OK)
        assert stat.filemode(os.stat(output_file_path).st_mode) == '-rwx------'
