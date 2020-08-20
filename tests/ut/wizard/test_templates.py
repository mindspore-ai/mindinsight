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
"""Test TemplateManager class."""
import os
import shutil
import tempfile
import textwrap

from mindinsight.wizard.base.templates import TemplateManager
from tests.ut.wizard.utils import generate_file


def create_template_files(template_dir):
    """Create network template files."""
    all_template_files = []
    train_file = os.path.join(template_dir, 'train.py-tpl')
    generate_file(train_file,
                  textwrap.dedent("""\
                        {% if loss=='SoftmaxCrossEntropyWithLogits' %}
                        net_loss = nn.SoftmaxCrossEntropyWithLogits(is_grad=False, sparse=True, reduction="mean")
                        {% elif loss=='SoftmaxCrossEntropyExpand' %}
                        net_loss = nn.SoftmaxCrossEntropyExpand(sparse=True)
                        {% endif %}
                        """))
    all_template_files.append(train_file)

    os.mkdir(os.path.join(template_dir, 'src'))
    config_file = os.path.join(template_dir, 'src', 'config.py-tpl')
    generate_file(config_file,
                  textwrap.dedent("""\
                        {
                            'num_classes': 10,
                            {% if optimizer=='Momentum' %}
                            'lr': 0.01,
                            "momentum": 0.9,
                            {% elif optimizer=='SGD' %}
                            'lr': 0.1,
                            {% else %}
                            'lr': 0.001,
                            {% endif %}
                            'epoch_size': 1
                        }
                        """))
    all_template_files.append(config_file)

    os.mkdir(os.path.join(template_dir, 'scripts'))
    run_standalone_train_file = os.path.join(template_dir, 'scripts', 'run_standalone_train.sh-tpl')
    generate_file(run_standalone_train_file,
                  textwrap.dedent("""\
                        python train.py --dataset_path=$PATH1 --pre_trained=$PATH2 &> log &
                        """))
    all_template_files.append(run_standalone_train_file)

    os.mkdir(os.path.join(template_dir, 'dataset'))
    os.mkdir(os.path.join(template_dir, 'dataset', 'mnist'))
    dataset_file = os.path.join(template_dir, 'dataset', 'mnist', 'dataset.py-tpl')
    generate_file(dataset_file,
                  textwrap.dedent("""\
                        import mindspore.dataset as ds
                        import mindspore.dataset.transforms.vision.c_transforms as CV
                        """))
    all_template_files.append(dataset_file)
    return all_template_files


class TestTemplateManager:
    """Test TemplateManager"""
    template_dir = None
    all_template_files = []

    def setup_method(self):
        """Setup before call test method."""
        self.template_dir = tempfile.mkdtemp()
        self.all_template_files = create_template_files(self.template_dir)

    def teardown_method(self):
        """Tear down after call test method."""
        self._remove_dirs()
        self.template_dir = None

    def _remove_dirs(self):
        """Recursively delete a directory tree."""
        if self.template_dir and os.path.exists(self.template_dir):
            shutil.rmtree(self.template_dir)

    def test_template_files(self):
        """Test get_template_files method."""
        src_file_num = 1
        dataset_file_num = 1
        template_mgr = TemplateManager(self.template_dir)
        all_files = template_mgr.get_template_files()
        assert set(all_files) == set(self.all_template_files)

        template_mgr = TemplateManager(os.path.join(self.template_dir, 'src'))
        all_files = template_mgr.get_template_files()
        assert len(all_files) == src_file_num

        template_mgr = TemplateManager(os.path.join(self.template_dir, 'dataset'))
        all_files = template_mgr.get_template_files()
        assert len(all_files) == dataset_file_num

        template_mgr = TemplateManager(self.template_dir, exclude_dirs=['src'])
        all_files = template_mgr.get_template_files()
        assert len(all_files) == len(self.all_template_files) - src_file_num

        template_mgr = TemplateManager(self.template_dir, exclude_dirs=['src', 'dataset'])
        all_files = template_mgr.get_template_files()
        assert len(all_files) == len(self.all_template_files) - src_file_num - dataset_file_num

        template_mgr = TemplateManager(self.template_dir,
                                       exclude_dirs=['src', 'dataset'],
                                       exclude_files=['train.py-tpl'])
        all_files = template_mgr.get_template_files()
        assert len(all_files) == len(self.all_template_files) - src_file_num - dataset_file_num - 1

    def test_src_render(self):
        """Test render file in src directory."""
        template_mgr = TemplateManager(os.path.join(self.template_dir, 'src'))
        source_files = template_mgr.render(optimizer='Momentum')
        assert source_files[0].content == textwrap.dedent("""\
                {
                    'num_classes': 10,
                    'lr': 0.01,
                    "momentum": 0.9,
                    'epoch_size': 1
                }
                """)

        source_files = template_mgr.render(optimizer='SGD')
        assert source_files[0].content == textwrap.dedent("""\
                {
                    'num_classes': 10,
                    'lr': 0.1,
                    'epoch_size': 1
                }
                """)
        source_files = template_mgr.render()
        assert source_files[0].content == textwrap.dedent("""\
                        {
                            'num_classes': 10,
                            'lr': 0.001,
                            'epoch_size': 1
                        }
                        """)

    def test_dataset_render(self):
        """Test render file in dataset directory."""
        template_mgr = TemplateManager(os.path.join(self.template_dir, 'dataset'))
        source_files = template_mgr.render()
        assert source_files[0].content == textwrap.dedent("""\
                import mindspore.dataset as ds
                import mindspore.dataset.transforms.vision.c_transforms as CV
                """)
        assert source_files[0].file_relative_path == 'mnist/dataset.py'
        assert source_files[0].template_file_path == os.path.join(self.template_dir, 'dataset', 'mnist/dataset.py-tpl')

    def test_assemble_render(self):
        """Test render assemble files in template directory."""
        template_mgr = TemplateManager(self.template_dir, exclude_dirs=['src', 'dataset'])
        source_files = template_mgr.render(loss='SoftmaxCrossEntropyWithLogits')
        unmatched_files = []
        for source_file in source_files:
            if source_file.template_file_path == os.path.join(self.template_dir, 'scripts/run_standalone_train.sh-tpl'):
                assert source_file.content == textwrap.dedent("""\
                        python train.py --dataset_path=$PATH1 --pre_trained=$PATH2 &> log &
                        """)
                assert source_file.file_relative_path == 'scripts/run_standalone_train.sh'
            elif source_file.template_file_path == os.path.join(self.template_dir, 'train.py-tpl'):
                assert source_file.content == textwrap.dedent("""\
                        net_loss = nn.SoftmaxCrossEntropyWithLogits(is_grad=False, sparse=True, reduction="mean")
                        """)
                assert source_file.file_relative_path == 'train.py'
            else:
                unmatched_files.append(source_file)

        assert not unmatched_files
