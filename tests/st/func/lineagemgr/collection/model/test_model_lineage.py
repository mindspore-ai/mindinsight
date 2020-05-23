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
from unittest import mock, TestCase

import numpy as np
import pytest

from mindinsight.lineagemgr import get_summary_lineage
from mindinsight.lineagemgr.collection.model.model_lineage import TrainLineage, EvalLineage, \
    AnalyzeObject
from mindinsight.lineagemgr.common.utils import make_directory
from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamRunContextError
from mindinsight.utils.exceptions import MindInsightException
from mindspore.application.model_zoo.resnet import ResNet
from mindspore.common.tensor import Tensor
from mindspore.dataset.engine import MindDataset
from mindspore.nn import Momentum, SoftmaxCrossEntropyWithLogits, WithLossCell
from mindspore.train.callback import RunContext, ModelCheckpoint, SummaryStep, _ListCallback
from mindspore.train.summary import SummaryRecord
from ...conftest import SUMMARY_DIR, SUMMARY_DIR_2, SUMMARY_DIR_3, BASE_SUMMARY_DIR
from .train_one_step import TrainOneStep


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

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_train_begin(self):
        """Test the begin function in TrainLineage."""
        train_callback = TrainLineage(self.summary_record, True)
        train_callback.begin(RunContext(self.run_context))
        assert train_callback.initial_learning_rate == 0.12
        lineage_log_path = train_callback.lineage_summary.lineage_log_path
        assert os.path.isfile(lineage_log_path) is True

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_train_begin_with_user_defined_info(self):
        """Test TrainLineage with nested user defined info."""
        user_defined_info = {"info": {"version": "v1"}}
        train_callback = TrainLineage(
            self.summary_record,
            False,
            user_defined_info
        )
        train_callback.begin(RunContext(self.run_context))
        assert train_callback.initial_learning_rate == 0.12
        lineage_log_path = train_callback.lineage_summary.lineage_log_path
        assert os.path.isfile(lineage_log_path) is True

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_train_lineage_with_log_dir(self):
        """Test TrainLineage with log_dir."""
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'log_dir')
        train_callback = TrainLineage(summary_record=summary_dir)
        train_callback.begin(RunContext(self.run_context))
        assert summary_dir == train_callback.lineage_log_dir
        lineage_log_path = train_callback.lineage_summary.lineage_log_path
        assert os.path.isfile(lineage_log_path) is True
        if os.path.exists(summary_dir):
            shutil.rmtree(summary_dir)

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
        train_callback = TrainLineage(self.summary_record, True)
        train_callback.initial_learning_rate = 0.12
        train_callback.end(RunContext(self.run_context))
        res = get_summary_lineage(SUMMARY_DIR)
        assert res.get('hyper_parameters', {}).get('epoch') == 10
        run_context = self.run_context
        run_context['epoch_num'] = 14
        train_callback.end(RunContext(run_context))
        res = get_summary_lineage(SUMMARY_DIR)
        assert res.get('hyper_parameters', {}).get('epoch') == 14

    @pytest.mark.scene_eval(3)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_eval_end(self):
        """Test the end function in EvalLineage."""
        eval_callback = EvalLineage(self.summary_record, True)
        eval_run_context = self.run_context
        eval_run_context['metrics'] = {'accuracy': 0.78}
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['step_num'] = 32
        eval_callback.end(RunContext(eval_run_context))

    @pytest.mark.scene_eval(3)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_eval_only(self):
        """Test record evaluation event only."""
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'eval_only_dir')
        summary_record = SummaryRecord(summary_dir)
        eval_run_context = self.run_context
        eval_run_context['metrics'] = {'accuracy': 0.58}
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['step_num'] = 32
        eval_only_callback = EvalLineage(summary_record)
        eval_only_callback.end(RunContext(eval_run_context))
        res = get_summary_lineage(summary_dir,
                                  ['metric', 'dataset_graph'])
        expect_res = {
            'summary_dir': summary_dir,
            'dataset_graph': {},
            'metric': {'accuracy': 0.58}
        }
        assert res == expect_res
        shutil.rmtree(summary_dir)

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch('mindinsight.lineagemgr.summary.summary_record.get_lineage_file_name')
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
            train_callback = TrainLineage(summary_record, True)
            train_callback.begin(RunContext(self.run_context))
            train_callback.end(RunContext(self.run_context))

            args[1].return_value = os.path.join(
                SUMMARY_DIR_2,
                f'eval_out.events.summary.{str(int(time.time())+ 2*i + 1)}.ubuntu_lineage'
            )
            eval_callback = EvalLineage(eval_record, True)
            eval_run_context = self.run_context
            eval_run_context['metrics'] = {'accuracy': 0.78 + i + 1}
            eval_run_context['valid_dataset'] = self.run_context['train_dataset']
            eval_run_context['step_num'] = 32
            eval_callback.end(RunContext(eval_run_context))
        file_num = os.listdir(SUMMARY_DIR_2)
        assert len(file_num) == 8

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch('mindinsight.lineagemgr.summary.summary_record.get_lineage_file_name')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_size')
    def test_train_eval(self, *args):
        """Callback for train once and eval once."""
        args[0].return_value = 10
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'train_eval')
        make_directory(summary_dir)
        args[1].return_value = os.path.join(
            summary_dir,
            f'train_out.events.summary.{str(int(time.time()))}.ubuntu_lineage'
        )
        train_callback = TrainLineage(summary_dir)
        train_callback.begin(RunContext(self.run_context))
        train_callback.end(RunContext(self.run_context))
        args[1].return_value = os.path.join(
            summary_dir,
            f'eval_out.events.summary.{str(int(time.time())+1)}.ubuntu_lineage'
        )
        eval_callback = EvalLineage(summary_dir)
        eval_run_context = self.run_context
        eval_run_context['metrics'] = {'accuracy': 0.78}
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['step_num'] = 32
        eval_callback.end(RunContext(eval_run_context))
        res = get_summary_lineage(summary_dir)
        assert res.get('hyper_parameters', {}).get('loss_function') \
            == 'SoftmaxCrossEntropyWithLogits'
        assert res.get('algorithm', {}).get('network') == 'ResNet'
        if os.path.exists(summary_dir):
            shutil.rmtree(summary_dir)

    @pytest.mark.scene_train(2)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch('mindinsight.lineagemgr.summary.summary_record.get_lineage_file_name')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_size')
    def test_train_multi_eval(self, *args):
        """Callback for train once and eval twice."""
        args[0].return_value = 10
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'train_multi_eval')
        make_directory(summary_dir)
        args[1].return_value = os.path.join(
            summary_dir,
            'train_out.events.summary.1590107366.ubuntu_lineage')
        train_callback = TrainLineage(summary_dir, True)
        train_callback.begin(RunContext(self.run_context))
        train_callback.end(RunContext(self.run_context))

        args[1].return_value = os.path.join(
            summary_dir,
            'eval_out.events.summary.1590107367.ubuntu_lineage')
        eval_callback = EvalLineage(summary_dir, True)
        eval_run_context = self.run_context
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['metrics'] = {'accuracy': 0.79}
        eval_callback.end(RunContext(eval_run_context))
        res = get_summary_lineage(summary_dir)
        assert res.get('metric', {}).get('accuracy') == 0.79

        args[1].return_value = os.path.join(
            summary_dir,
            'eval_out.events.summary.1590107368.ubuntu_lineage')
        eval_callback = EvalLineage(summary_dir, True)
        eval_run_context = self.run_context
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        eval_run_context['metrics'] = {'accuracy': 0.80}
        eval_callback.end(RunContext(eval_run_context))
        res = get_summary_lineage(summary_dir)
        assert res.get('metric', {}).get('accuracy') == 0.80
        if os.path.exists(summary_dir):
            shutil.rmtree(summary_dir)

    @pytest.mark.scene_train(2)
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
        train_callback = TrainLineage(self.summary_record, True)
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
        res = get_summary_lineage(SUMMARY_DIR)
        assert res.get('hyper_parameters', {}).get('loss_function') \
               == 'SoftmaxCrossEntropyWithLogits'
        assert res.get('algorithm', {}).get('network') == 'ResNet'
        assert res.get('hyper_parameters', {}).get('optimizer') == 'Momentum'

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_raise_exception(self):
        """Test exception when raise_exception is set True."""
        summary_record = SummaryRecord(SUMMARY_DIR_3)
        full_file_name = summary_record.full_file_name
        assert os.path.isfile(full_file_name) is True
        assert os.path.isfile(full_file_name + "_lineage") is False
        train_callback = TrainLineage(summary_record, True)
        eval_callback = EvalLineage(summary_record, False)
        with self.assertRaises(LineageParamRunContextError):
            train_callback.begin(self.run_context)
            eval_callback.end(self.run_context)
        file_num = os.listdir(SUMMARY_DIR_3)
        assert len(file_num) == 1
        assert os.path.isfile(full_file_name + "_lineage") is False

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_raise_exception_init(self):
        """Test exception when error happened during the initialization process."""
        if os.path.exists(SUMMARY_DIR_3):
            shutil.rmtree(SUMMARY_DIR_3)
        summary_record = SummaryRecord(SUMMARY_DIR_3)
        train_callback = TrainLineage('fake_summary_record', False)
        eval_callback = EvalLineage('fake_summary_record', False)
        train_callback.begin(RunContext(self.run_context))
        eval_callback.end(RunContext(self.run_context))
        file_num = os.listdir(SUMMARY_DIR_3)
        full_file_name = summary_record.full_file_name
        assert len(file_num) == 1
        assert os.path.isfile(full_file_name + "_lineage") is False

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_raise_exception_create_file(self):
        """Test exception when error happened after creating file."""
        if os.path.exists(SUMMARY_DIR_3):
            shutil.rmtree(SUMMARY_DIR_3)
        summary_record = SummaryRecord(SUMMARY_DIR_3)
        eval_callback = EvalLineage(summary_record, False)
        full_file_name = summary_record.full_file_name + "_lineage"
        eval_run_context = self.run_context
        eval_run_context['metrics'] = {'accuracy': 0.78}
        eval_run_context['step_num'] = 32
        eval_run_context['valid_dataset'] = self.run_context['train_dataset']
        with open(full_file_name, 'ab'):
            with mock.patch('builtins.open') as mock_handler:
                mock_handler.return_value.__enter__.return_value.write.side_effect = IOError
                eval_callback.end(RunContext(eval_run_context))
        assert os.path.isfile(full_file_name) is True
        assert os.path.getsize(full_file_name) == 0

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_eval_run_context')
    @mock.patch.object(AnalyzeObject, 'get_file_size', return_value=64)
    def test_raise_exception_record_trainlineage(self, *args):
        """Test exception when error happened after recording training infos."""
        if os.path.exists(SUMMARY_DIR_3):
            shutil.rmtree(SUMMARY_DIR_3)
        args[1].side_effect = MindInsightException(error=LineageErrors.PARAM_RUN_CONTEXT_ERROR,
                                                   message="RunContext error.")
        summary_record = SummaryRecord(SUMMARY_DIR_3)
        train_callback = TrainLineage(summary_record, True)
        train_callback.begin(RunContext(self.run_context))
        full_file_name = train_callback.lineage_summary.lineage_log_path
        file_size1 = os.path.getsize(full_file_name)
        train_callback.end(RunContext(self.run_context))
        file_size2 = os.path.getsize(full_file_name)
        assert file_size2 > file_size1
        eval_callback = EvalLineage(summary_record, False)
        eval_callback.end(RunContext(self.run_context))
        file_size3 = os.path.getsize(full_file_name)
        assert file_size3 == file_size2

    @pytest.mark.scene_exception(1)
    @pytest.mark.level0
    @pytest.mark.platform_arm_ascend_training
    @pytest.mark.platform_x86_gpu_training
    @pytest.mark.platform_x86_ascend_training
    @pytest.mark.platform_x86_cpu
    @pytest.mark.env_single
    def test_raise_exception_non_lineage_file(self):
        """Test exception when lineage summary file cannot be found."""
        summary_dir = os.path.join(BASE_SUMMARY_DIR, 'run4')
        if os.path.exists(summary_dir):
            shutil.rmtree(summary_dir)
        summary_record = SummaryRecord(summary_dir, file_suffix='_MS_lineage_none')
        full_file_name = summary_record.full_file_name
        assert full_file_name.endswith('_lineage_none')
        assert os.path.isfile(full_file_name)
