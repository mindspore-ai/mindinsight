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
Fuction:
    Test the lineage information collection module.
Usage:
    pytest lineagemgr/collection/model/test_model_lineage.py
"""

import os
import shutil
import time
from unittest import TestCase, mock

import numpy as np
import pytest
from mindinsight.lineagemgr.model import filter_summary_lineage

from mindspore.application.model_zoo.resnet import ResNet
from mindspore.common.tensor import Tensor
from mindspore.dataset.engine import MindDataset
from mindspore.nn import Momentum, SoftmaxCrossEntropyWithLogits, WithLossCell
from mindspore.train.callback import ModelCheckpoint, RunContext, SummaryStep, _ListCallback
from mindspore.train.summary import SummaryRecord

from .train_one_step import TrainOneStep
from ...conftest import SUMMARY_DIR, SUMMARY_DIR_2, SUMMARY_DIR_3, BASE_SUMMARY_DIR, LINEAGE_DATA_MANAGER
from ......utils.lineage_writer.model_lineage import AnalyzeObject, EvalLineage, TrainLineage
from ......utils.tools import get_relative_path


@pytest.mark.usefixtures("create_summary_dir")
class TestModelLineage(TestCase):
    """Test mindinsight.lineagemgr.collection.model.model_lineage.py"""

    @classmethod
    def setup_class(cls):
        """Setup method."""
        cls.optimizer = Momentum(Tensor(0.12))
        cls.loss_fn = SoftmaxCrossEntropyWithLogits()
        cls.net = ResNet()

        cls.run_context = dict()
        cls.run_context['train_network'] = cls.net
        cls.run_context['loss_fn'] = cls.loss_fn
        cls.run_context['net_outputs'] = Tensor(np.array([0.03]))
        cls.run_context['optimizer'] = cls.optimizer
        cls.run_context['train_dataset'] = MindDataset(dataset_size=32)
        cls.run_context['epoch_num'] = 10
        cls.run_context['cur_step_num'] = 320
        cls.run_context['parallel_mode'] = "stand_alone"
        cls.run_context['device_number'] = 2
        cls.run_context['batch_num'] = 32
        cls.summary_record = SummaryRecord(SUMMARY_DIR)
        callback = [ModelCheckpoint(directory=SUMMARY_DIR),
                    SummaryStep(cls.summary_record),
                    TrainLineage(cls.summary_record)
                    ]
        cls.run_context['list_callback'] = _ListCallback(callback)
        cls.user_defined_info = {
            "info": "info1",
            "version": "v1"
        }

        train_id = get_relative_path(SUMMARY_DIR, BASE_SUMMARY_DIR)
        cls._search_condition = {
            'summary_dir': {
                'eq': train_id
            }
        }

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch.object(AnalyzeObject, 'get_file_size')
    def test_training_end(self, *args):
        """Test the end function in TrainLineage."""
        args[0].return_value = 64
        train_callback = TrainLineage(SUMMARY_DIR, True, self.user_defined_info)
        train_callback.initial_learning_rate = 0.12
        train_callback.end(RunContext(self.run_context))

        LINEAGE_DATA_MANAGER.start_load_data().join()
        res = filter_summary_lineage(data_manager=LINEAGE_DATA_MANAGER, search_condition=self._search_condition)
        assert res.get('object')[0].get('model_lineage', {}).get('epoch') == 10
        run_context = self.run_context
        run_context['epoch_num'] = 14
        train_callback.end(RunContext(run_context))

        LINEAGE_DATA_MANAGER.start_load_data().join()
        res = filter_summary_lineage(data_manager=LINEAGE_DATA_MANAGER, search_condition=self._search_condition)
        assert res.get('object')[0].get('model_lineage', {}).get('epoch') == 14

        eval_callback = EvalLineage(self.summary_record, True, self.user_defined_info)
        eval_run_context = self.run_context
        eval_run_context['metrics'] = {'accuracy': 0.78}
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['step_num'] = 32
        eval_callback.end(RunContext(eval_run_context))

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch('tests.utils.lineage_writer._summary_record.get_lineage_file_name')
    @mock.patch('os.path.getsize')
    def test_multiple_trains(self, *args):
        """
        Callback TrainLineage and EvalLineage for multiple times.

        Write TrainLineage and EvalLineage in different files under same directory.
        EvalLineage log file end with '_lineage'.
        """
        args[0].return_value = 10
        for i in range(2):
            summary_record = SummaryRecord(
                SUMMARY_DIR_2,
                create_time=int(time.time()) + i)
            eval_record = SummaryRecord(
                SUMMARY_DIR_2,
                create_time=int(time.time() + 10) + i)
            args[1].return_value = os.path.join(
                SUMMARY_DIR_2,
                f'train_out.events.summary.{str(int(time.time()) + 2*i)}.ubuntu_lineage'
            )
            train_callback = TrainLineage(summary_record, True, self.user_defined_info)
            train_callback.begin(RunContext(self.run_context))
            train_callback.end(RunContext(self.run_context))

            args[1].return_value = os.path.join(
                SUMMARY_DIR_2,
                f'eval_out.events.summary.{str(int(time.time())+ 2*i + 1)}.ubuntu_lineage'
            )
            eval_callback = EvalLineage(eval_record, True, {'eval_version': 'version2'})
            eval_run_context = self.run_context
            eval_run_context['metrics'] = {'accuracy': 0.78 + i + 1}
            eval_run_context['valid_dataset'] = self.run_context['train_dataset']
            eval_run_context['step_num'] = 32
            eval_callback.end(RunContext(eval_run_context))
        file_num = os.listdir(SUMMARY_DIR_2)
        assert len(file_num) == 8

    @pytest.mark.scene_train(3)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch.object(AnalyzeObject, 'get_file_size')
    def test_train_with_customized_network(self, *args):
        """Test train with customized network."""
        args[0].return_value = 64
        train_callback = TrainLineage(SUMMARY_DIR, True, self.user_defined_info)
        run_context_customized = self.run_context
        del run_context_customized['optimizer']
        del run_context_customized['net_outputs']
        del run_context_customized['loss_fn']
        net = WithLossCell(self.net, self.loss_fn)
        net_cap = net
        net_cap._cells = {'_backbone': self.net,
                          '_loss_fn': self.loss_fn}
        net = TrainOneStep(net, self.optimizer)
        net._cells = {'optimizer': self.optimizer,
                      'network': net_cap,
                      'backbone': self.net}
        run_context_customized['train_network'] = net
        train_callback.begin(RunContext(run_context_customized))
        train_callback.end(RunContext(run_context_customized))

        LINEAGE_DATA_MANAGER.start_load_data().join()
        res = filter_summary_lineage(data_manager=LINEAGE_DATA_MANAGER, search_condition=self._search_condition)
        assert res.get('object')[0].get('model_lineage', {}).get('loss_function') \
               == 'SoftmaxCrossEntropyWithLogits'
        assert res.get('object')[0].get('model_lineage', {}).get('network') == 'ResNet'
        assert res.get('object')[0].get('model_lineage', {}).get('optimizer') == 'Momentum'

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch.object(AnalyzeObject, 'get_file_size')
    def test_raise_exception_record_trainlineage(self, mock_analyze):
        """Test exception when error happened after recording training infos."""
        mock_analyze.return_value = 64
        if os.path.exists(SUMMARY_DIR_3):
            shutil.rmtree(SUMMARY_DIR_3)
        train_callback = TrainLineage(SUMMARY_DIR_3, True)
        train_callback.begin(RunContext(self.run_context))
        full_file_name = train_callback.lineage_summary.lineage_log_path
        file_size1 = os.path.getsize(full_file_name)
        train_callback.end(RunContext(self.run_context))
        file_size2 = os.path.getsize(full_file_name)
        assert file_size2 > file_size1
        eval_callback = EvalLineage(SUMMARY_DIR_3, False)
        eval_callback.end(RunContext(self.run_context))
        file_size3 = os.path.getsize(full_file_name)
        assert file_size3 == file_size2
