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
"""Test GenericNetwork class."""
import os

import pytest

from mindinsight.wizard.network import lenet


class TestGenericNetwork:
    """Test SourceFile"""

    def test_generate_scripts(self):
        """Test network object to generate network scripts"""
        network_inst = lenet.Network()
        network_inst.configure({
            "loss": "SoftmaxCrossEntropyWithLogits",
            "optimizer": "Momentum",
            "dataset": "mnist"})
        sources_files = network_inst.generate()
        dataset_source_file = None
        config_source_file = None
        shell_script_dir_files = []
        out_files = []
        for sources_file in sources_files:
            if sources_file.file_relative_path == 'src/dataset.py':
                dataset_source_file = sources_file
            elif sources_file.file_relative_path == 'src/config.py':
                config_source_file = sources_file
            elif sources_file.file_relative_path.startswith('scripts'):
                shell_script_dir_files.append(sources_file)
            elif not os.path.dirname(sources_file.file_relative_path):
                out_files.append(sources_file)
            else:
                pass

        assert sources_files
        assert dataset_source_file is not None
        assert config_source_file is not None
        assert shell_script_dir_files
        assert out_files

    def test_config(self):
        """Test network object to config."""
        network_inst = lenet.Network()
        settings = {
            "loss": "SoftmaxCrossEntropyWithLogits",
            "optimizer": "Momentum",
            "dataset": "mnist"}
        configurations = network_inst.configure(settings)
        assert configurations["dataset"] == settings["dataset"]
        assert configurations["loss"] == settings["loss"]
        assert configurations["optimizer"] == settings["optimizer"]

        settings["dataset"] = "mnist_another"
        with pytest.raises(ModuleNotFoundError) as exec_info:
            network_inst.configure(settings)
        assert exec_info.value.name == f'mindinsight.wizard.dataset.{settings["dataset"]}'
