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
"""Test tuner and hyper config."""
import json
import os
import shutil

import pytest

from mindinsight.optimizer.tuner import Tuner
from mindinsight.optimizer.hyper_config import HyperConfig

from tests.utils.lineage_writer import LineageWriter
from tests.utils.lineage_writer.base import Metadata
from tests.utils.tools import convert_dict_to_yaml
from tests.st.func.optimizer.conftest import SUMMARY_BASE_DIR


def _create_summaries(summary_base_dir):
    """Create summaries."""
    learning_rate = [0.01, 0.001, 0.02, 0.04, 0.05]
    acc = [0.8, 0.9, 0.8, 0.7, 0.6]
    momentum = [0.8, 0.9, 0.8, 0.9, 0.7]
    train_ids = []
    train_id_prefix = 'train_'
    params = {}
    for i, lr in enumerate(learning_rate):
        train_id = f'./{train_id_prefix}{i + 1}'
        train_ids.append(train_id)
        params.update({
            train_id: {
                'train': {
                    Metadata.learning_rate: lr
                },
                'eval': {
                    Metadata.metrics: json.dumps({'acc': acc[i]}),
                    'user_defined_info': {'momentum': momentum[i]}
                }
            }
        })

    lineage_writer = LineageWriter(summary_base_dir)
    lineage_writer.create_summaries(train_id_prefix=train_id_prefix, train_job_num=5, params=params)

    return train_ids


def _prepare_script_and_yaml(output_dir, script_name='test.py', yaml_name='config.yaml'):
    """Prepare script and yaml file."""
    script_path = os.path.join(output_dir, script_name)
    with open(script_path, 'w'):
        pass
    config_dict = {
        'command': 'python %s' % script_path,
        'summary_base_dir': SUMMARY_BASE_DIR,
        'tuner': {
            'name': 'gp',
        },
        'target': {
            'group': 'metric',
            'name': 'acc',
            'goal': 'maximize'
        },
        'parameters': {
            'learning_rate': {
                'bounds': [0.0001, 0.01],
                'type': 'float'
            },
            'momentum': {
                'choice': [0.8, 0.9]
            }
        }
    }
    convert_dict_to_yaml(config_dict, output_dir, yaml_name)
    return script_path, os.path.join(output_dir, yaml_name)


class TestHyperConfig:
    """Test HyperConfig."""
    def setup_class(self):
        """Setup class."""
        self._generated_file_path = []
        self._train_ids = _create_summaries(SUMMARY_BASE_DIR)
        script_path, self._yaml_path = _prepare_script_and_yaml(SUMMARY_BASE_DIR)
        self._generated_file_path.append(script_path)
        self._generated_file_path.append(self._yaml_path)

    def teardown_class(self):
        """Delete the files generated before."""
        for train_id in self._train_ids:
            summary_dir = os.path.join(SUMMARY_BASE_DIR, train_id)
            if os.path.exists(summary_dir):
                shutil.rmtree(summary_dir)
        for file in self._generated_file_path:
            if os.path.exists(file):
                os.remove(file)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_tuner_success(self):
        """Test tuner successfully."""
        tuner = Tuner(self._yaml_path)
        tuner.optimize()

        hyper_config = HyperConfig()

        params = hyper_config.params
        assert list(params.keys()) == ['learning_rate', 'momentum']
        assert 0.0001 <= params.learning_rate < 0.01
        assert params.momentum in [0.8, 0.9]

        assert list(hyper_config.custom_lineage_data.keys()) == ['momentum']
