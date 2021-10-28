# Copyright 2019 Huawei Technologies Co., Ltd
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

"""
Function:
    Test mindconverter to convert user's PyTorch network script.
Usage:
    pytest tests/st/func/mindconverter
"""
import difflib
import os
import sys
import pytest

from mindconverter.converter import main


@pytest.mark.usefixtures('create_output_dir')
class TestConverter:
    """Test Converter module."""

    @classmethod
    def setup_class(cls):
        """Setup method."""
        cls.script_dir = os.path.join(os.path.dirname(__file__), 'data')
        pytorch_base_dir = os.path.dirname(__file__).split('/')[:3]
        cls.pytorch_dir = \
            '/'.join(pytorch_base_dir + ['share-data', 'dataset', 'mindinsight_dataset', 'resnet50'])
        sys.path.insert(0, cls.script_dir)

    @classmethod
    def teardown_class(cls):
        """Teardown method."""
        sys.path.remove(cls.script_dir)

    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_convert_lenet(self, output):
        """Test LeNet script of the PyTorch convert to MindSpore script"""
        script_filename = "lenet_script.py"
        expect_filename = "lenet_converted.py"
        files_config = {
            'root_path': self.script_dir,
            'in_files': [os.path.join(self.script_dir, script_filename)],
            'outfile_dir': output,
            'report_dir': output
        }
        main(files_config)

        assert os.path.isfile(os.path.join(output, script_filename))

        with open(os.path.join(output, script_filename)) as converted_f:
            converted_source = converted_f.readlines()

        with open(os.path.join(self.script_dir, expect_filename)) as expect_f:
            expect_source = expect_f.readlines()

        diff = difflib.ndiff(converted_source, expect_source)
        diff_lines = 0
        for line in diff:
            if line.startswith('+'):
                diff_lines += 1

        converted_ratio = 100 - (diff_lines * 100) / (len(expect_source))
        assert converted_ratio >= 80
