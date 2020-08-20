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
"""Test CreateProject class."""
import os
import shutil
import tempfile
from unittest.mock import patch

from mindinsight.wizard.base.source_file import SourceFile
from mindinsight.wizard.create_project import CreateProject
from mindinsight.wizard.network.generic_network import GenericNetwork
from tests.ut.wizard.utils import generate_file


class TestCreateProject:
    """Test SourceFile"""
    workspace_dir = None

    def setup_method(self):
        """Setup before call test method."""
        self.workspace_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Tear down after call test method."""
        self._remove_dirs()
        self.workspace_dir = None

    def _remove_dirs(self):
        """Recursively delete a directory tree."""
        if self.workspace_dir and os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)

    @staticmethod
    def _generate_file(file):
        """Create a file and write content."""
        generate_file(file, "template file.")

    @patch.object(GenericNetwork, 'generate')
    @patch.object(GenericNetwork, 'configure')
    @patch.object(CreateProject, 'ask_network')
    @patch.object(CreateProject, 'echo_notice')
    @patch('os.getcwd')
    def test_run(self, mock_getcwd, mock_echo_notice, mock_ask_network, mock_config, mock_generate):
        """Test run method of CreateProject."""
        source_file = SourceFile()
        source_file.template_file_path = os.path.join(self.workspace_dir, 'templates', 'train.py-tpl')
        source_file.file_relative_path = 'train.py'
        self._generate_file(source_file.template_file_path)

        # mock os.getcwd method
        mock_getcwd.return_value = self.workspace_dir
        mock_echo_notice.return_value = None
        mock_ask_network.return_value = 'lenet'
        mock_config.return_value = None
        mock_generate.return_value = [source_file]

        project_name = 'test'
        new_project = CreateProject()
        new_project.run({'name': project_name})

        assert os.path.exists(os.path.join(self.workspace_dir, project_name))
        assert os.access(os.path.join(self.workspace_dir, project_name, 'train.py'), mode=os.F_OK | os.R_OK | os.W_OK)
