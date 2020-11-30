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
"""Test targets restful api."""
import json
import os
import shutil

import pytest

from tests.utils.lineage_writer import LineageWriter
from tests.utils.lineage_writer.base import Metadata
from tests.st.func.optimizer.conftest import MOCK_DATA_MANAGER, SUMMARY_BASE_DIR

BASE_URL = '/v1/mindinsight/optimizer/targets/search'


class TestTargets:
    """Test Targets."""

    def setup_class(self):
        """Setup class."""
        learning_rate = [0.01, 0.001, 0.02, 0.04, 0.05]
        acc = [0.8, 0.9, 0.8, 0.7, 0.6]
        self._train_ids = []
        train_id_prefix = 'train_'
        params = {}
        for i, lr in enumerate(learning_rate):
            train_id = f'./{train_id_prefix}{i + 1}'
            self._train_ids.append(train_id)
            params.update({
                train_id: {
                    'train': {Metadata.learning_rate: lr},
                    'eval': {Metadata.metrics: json.dumps({'acc': acc[i]})}
                }
            })

        lineage_writer = LineageWriter(SUMMARY_BASE_DIR)
        lineage_writer.create_summaries(train_id_prefix=train_id_prefix, train_job_num=5, params=params)

        MOCK_DATA_MANAGER.start_load_data().join()

    def teardown_class(self):
        """Delete the summary directory."""
        for train_id in self._train_ids:
            summary_dir = os.path.join(SUMMARY_BASE_DIR, train_id)
            if os.path.exists(summary_dir):
                shutil.rmtree(summary_dir)

    @pytest.mark.level0
    @pytest.mark.env_single
    @pytest.mark.platform_x86_cpu
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.usefixtures("init_summary_logs")
    def test_targets_search_success(self, client):
        """Test searching targets successfully."""
        search_conditions = {
            'summary_dir': {
                'in': self._train_ids
            }
        }
        response = client.post(BASE_URL, data=json.dumps(search_conditions))
        result = json.loads(response.data)

        # test metric name
        metric_names = [target.get('name') for target in result.get('targets')]
        acc_name = '[M]acc'
        assert acc_name in metric_names

        # test target bucket
        acc_index = metric_names.index(acc_name)
        acc_info = result.get('targets')[acc_index]
        buckets = acc_info.get('buckets')
        test_bucket_index = 3
        expected_bucket = [0.78, 0.06, 2]

        for index, exp_value in enumerate(expected_bucket):
            assert abs(buckets[test_bucket_index][index] - exp_value) < 1e-5

        # test importance
        hyper_params_info = acc_info.get('hyper_parameters')
        hyper_names = [param_info.get('name') for param_info in hyper_params_info]
        assert Metadata.learning_rate in hyper_names

        exp_value = 0.9714143567416961
        lr_index = hyper_names.index(Metadata.learning_rate)
        assert abs(hyper_params_info[lr_index].get('importance') - exp_value) < 1e-5
