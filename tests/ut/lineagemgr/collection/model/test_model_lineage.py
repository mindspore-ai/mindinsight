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
"""Unittest for model_lineage.py"""
import os
import shutil
import unittest
from unittest import TestCase, mock
from unittest.mock import MagicMock

from mindinsight.lineagemgr.collection.model.model_lineage import AnalyzeObject, EvalLineage, TrainLineage
from mindinsight.lineagemgr.common.exceptions.exceptions import (LineageGetModelFileError, LineageLogError,
                                                                 MindInsightException)
from mindspore.common.tensor import Tensor
from mindspore.dataset.engine import Dataset, MindDataset
from mindspore.nn import Optimizer, SoftmaxCrossEntropyWithLogits, TrainOneStepWithLossScaleCell, WithLossCell
from mindspore.train.callback import ModelCheckpoint, RunContext, SummaryStep
from mindspore.train.summary import SummaryRecord


@mock.patch('builtins.open')
@mock.patch('os.makedirs')
class TestModelLineage(TestCase):
    """Test TrainLineage and EvalLineage class in model_lineage.py."""

    @classmethod
    def setUpClass(cls):
        cls.lineage_list = ['train_network', 'loss_fn', 'optimizer', 'train_dataset',
                            'valid_dataset', 'epoch', 'valid_step',
                            'hybrid_parallel', 'data_parallel_size', 'auto_parallel',
                            'device_number', 'batch_num', 'summary_log_path',
                            'model_ckpt']
        cls.run_context = {key: None for key in cls.lineage_list}
        cls.run_context['net_outputs'] = Tensor()
        cls.my_run_context = RunContext
        cls.my_train_module = TrainLineage
        cls.my_eval_module = EvalLineage
        cls.my_analyze_module = AnalyzeObject
        cls.my_summary_record = SummaryRecord
        cls.summary_log_path = '/path/to/summary_log'

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_summary_record_exception(self, *args):
        """Test SummaryRecord with exception."""
        args[0].return_value = None
        summary_record = self.my_summary_record(self.summary_log_path)
        with self.assertRaises(MindInsightException) as context:
            self.my_train_module(summary_record=summary_record, raise_exception=1)
        self.assertTrue(f'Invalid value for raise_exception.' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.ds')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.LineageSummary.record_dataset_graph')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_optimizer_by_network')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_optimizer')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_network')
    def test_begin(self, *args):
        """Test TrainLineage.begin method."""
        args[1].return_value = None
        args[2].return_value = Optimizer(Tensor(0.1))
        args[3].return_value = None
        args[5].serialize.return_value = {}
        run_context = {'optimizer': Optimizer(Tensor(0.1)),
                       'epoch_num': 10}
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path))
        train_lineage.begin(self.my_run_context(run_context))
        args[4].assert_called()

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.ds')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.LineageSummary.record_dataset_graph')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_optimizer_by_network')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_optimizer')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_network')
    def test_begin_error(self, *args):
        """Test TrainLineage.begin method."""
        args[1].return_value = None
        args[2].return_value = Optimizer(Tensor(0.1))
        args[3].return_value = None
        args[4].side_effect = Exception
        args[5].serialize.return_value = {}
        run_context = {'optimizer': Optimizer(Tensor(0.1)),
                       'epoch_num': 10}
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaisesRegex(LineageLogError, 'Dataset graph log error'):
            train_lineage.begin(self.my_run_context(run_context))
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path))
        train_lineage.begin(self.my_run_context(run_context))
        args[4].assert_called()

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_begin_exception(self, *args):
        """Test TrainLineage.begin method with exception."""
        args[0].return_value = None
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(Exception) as context:
            train_lineage.begin(self.run_context)
        self.assertTrue('Invalid TrainLineage run_context.' in str(context.exception))

        run_context = {key: None for key in self.lineage_list}
        run_context['optimizer'] = 1
        with self.assertRaises(Exception) as context:
            train_lineage.begin(self.my_run_context(run_context))
        self.assertTrue('The parameter optimizer is invalid.' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_model_size')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_path')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.LineageSummary.record_train_lineage')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_optimizer')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_network')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_train_run_context')
    @mock.patch('builtins.float')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_train_end(self, *args):
        """Test TrainLineage.end method."""
        args[1].return_value = 2.0
        args[2].return_value = True
        args[3].return_value = True
        args[4].return_value = None
        args[5].return_value = None
        args[6].return_value = None
        args[7].return_value = (None, None)
        args[8].return_value = 10
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        train_lineage.end(self.my_run_context(self.run_context))
        args[6].assert_called()

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_train_end_exception(self, *args):
        """Test TrainLineage.end method when exception."""
        args[0].return_value = True
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(Exception) as context:
            train_lineage.end(self.run_context)
        self.assertTrue('Invalid TrainLineage run_context.' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_model_size')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_path')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.LineageSummary.record_train_lineage')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_optimizer')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_network')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_train_run_context')
    @mock.patch('builtins.float')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_train_end_exception_log_error(self, *args):
        """Test TrainLineage.end method with logging errors."""
        args[1].return_value = 2.0
        args[2].return_value = True
        args[3].return_value = True
        args[4].return_value = None
        args[5].return_value = None
        args[6].side_effect = Exception
        args[7].return_value = (None, None)
        args[8].return_value = 10
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(LineageLogError) as context:
            train_lineage.end(self.my_run_context(self.run_context))
        self.assertTrue('End error in TrainLineage:' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_model_size')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_path')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.LineageSummary.record_train_lineage')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.analyze_optimizer')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_network')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_train_run_context')
    @mock.patch('builtins.float')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_train_end_exception_log_error2(self, *args):
        """Test TrainLineage.end method with logging errors."""
        args[1].return_value = 2.0
        args[2].return_value = True
        args[3].return_value = True
        args[4].return_value = None
        args[5].return_value = None
        args[6].side_effect = IOError
        args[7].return_value = (None, None)
        args[8].return_value = 10
        run_context = {key: None for key in self.lineage_list}
        run_context['loss_fn'] = MagicMock()
        run_context['net_outputs'] = Tensor(0.11)
        train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(LineageLogError) as context:
            train_lineage.end(self.my_run_context(run_context))
        self.assertTrue('End error in TrainLineage:' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_eval_exception_train_id_none(self, *args):
        """Test EvalLineage.end method with initialization error."""
        args[0].return_value = True
        with self.assertRaises(MindInsightException) as context:
            self.my_eval_module(self.my_summary_record(self.summary_log_path), raise_exception=2)
        self.assertTrue('Invalid value for raise_exception.' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.make_directory')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_eval_run_context')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'LineageSummary.record_evaluation_lineage')
    def test_eval_end(self, *args):
        """Test EvalLineage.end method."""
        args[1].return_value = True
        args[2].return_value = True
        args[3].return_value = None
        args[4].return_value = '/path/to/lineage/log/dir'
        args[0].return_value = None
        eval_lineage = self.my_eval_module(self.my_summary_record(self.summary_log_path))
        eval_lineage.end(self.my_run_context(self.run_context))
        args[0].assert_called()

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.make_directory')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    def test_eval_end_except_run_context(self, *args):
        """Test EvalLineage.end method when run_context is invalid.."""
        args[0].return_value = True
        args[1].return_value = '/path/to/lineage/log/dir'
        eval_lineage = self.my_eval_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(Exception) as context:
            eval_lineage.end(self.run_context)
        self.assertTrue('Invalid EvalLineage run_context.' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.make_directory')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_eval_run_context')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'LineageSummary.record_evaluation_lineage')
    def test_eval_end_except_log_error(self, *args):
        """Test EvalLineage.end method with logging error."""
        args[0].side_effect = Exception
        args[1].return_value = True
        args[2].return_value = True
        args[3].return_value = None
        args[4].return_value = '/path/to/lineage/log/dir'
        eval_lineage = self.my_eval_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(LineageLogError) as context:
            eval_lineage.end(self.my_run_context(self.run_context))
        self.assertTrue('End error in EvalLineage' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.make_directory')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'AnalyzeObject.analyze_dataset')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_summary_record')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.validate_eval_run_context')
    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'LineageSummary.record_evaluation_lineage')
    def test_eval_end_except_log_error2(self, *args):
        """Test EvalLineage.end method with logging error."""
        args[0].side_effect = IOError
        args[1].return_value = True
        args[2].return_value = True
        args[3].return_value = None
        args[4].return_value = '/path/to/lineage/log/dir'
        eval_lineage = self.my_eval_module(self.my_summary_record(self.summary_log_path), True)
        with self.assertRaises(LineageLogError) as context:
            eval_lineage.end(self.my_run_context(self.run_context))
        self.assertTrue('End error in EvalLineage' in str(context.exception))

    def test_epoch_is_zero(self, *args):
        """Test TrainLineage.end method."""
        args[0].return_value = None
        run_context = self.run_context
        run_context['epoch_num'] = 0
        with self.assertRaises(MindInsightException):
            train_lineage = self.my_train_module(self.my_summary_record(self.summary_log_path), True)
            train_lineage.end(self.my_run_context(run_context))

    def tearDown(self):
        """Teardown."""
        if os.path.exists(self.summary_log_path):
            try:
                shutil.rmtree(self.summary_log_path)
            except IOError:
                pass


class TestAnalyzer(TestCase):
    """Test Analyzer class in model_lineage.py."""

    def setUp(self):
        """SetUp config."""
        self.analyzer = AnalyzeObject()

    def test_analyze_optimizer(self):
        """Test analyze_optimizer method."""
        optimizer = Optimizer(Tensor(0.12))
        res = self.analyzer.analyze_optimizer(optimizer)
        assert res == 0.12

    def test_get_dataset_path(self):
        """Test get_dataset_path method."""
        dataset = MindDataset(
            dataset_file='/path/to/mindrecord'
        )
        res = self.analyzer.get_dataset_path(dataset)
        assert res == '/path/to/mindrecord'

    def test_get_dataset_path_wrapped(self):
        """Test get_dataset_path_wrapped method."""
        dataset = Dataset()
        dataset.input.append(
            MindDataset(
                dataset_size=10,
                dataset_file='/path/to/cifar10'
            ))

        res = self.analyzer.get_dataset_path_wrapped(dataset)
        assert res == '/path/to/cifar10'

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.'
                'AnalyzeObject.get_dataset_path_wrapped')
    def test_analyze_dataset(self, mock_get_path):
        """Test analyze_dataset method."""
        mock_get_path.return_value = '/path/to/mindinsightset'
        dataset = MindDataset(
            dataset_size=10,
            dataset_file='/path/to/mindinsightset'
        )
        res1 = self.analyzer.analyze_dataset(dataset, {'step_num': 10, 'epoch': 2}, 'train')
        res2 = self.analyzer.analyze_dataset(dataset, {'step_num': 5}, 'valid')
        assert res1 == {'step_num': 10,
                        'train_dataset_path': '/path/to',
                        'train_dataset_size': 50,
                        'epoch': 2}
        assert res2 == {'step_num': 5, 'valid_dataset_path': '/path/to',
                        'valid_dataset_size': 50}

    def test_get_dataset_path_dataset(self):
        """Test get_dataset_path method with Dataset."""
        dataset = Dataset(
            dataset_size=10,
            dataset_path='/path/to/cifar10'
        )

        with self.assertRaises(IndexError):
            self.analyzer.get_dataset_path(output_dataset=dataset)

    def test_get_dataset_path_mindrecord(self):
        """Test get_dataset_path method with MindDataset."""
        dataset = MindDataset(
            dataset_file='/path/to/cifar10'
        )
        dataset_path = self.analyzer.get_dataset_path(output_dataset=dataset)
        self.assertEqual(dataset_path, '/path/to/cifar10')

    def test_get_file_path(self):
        """Test get_file_path method."""
        model_ckpt = ModelCheckpoint(prefix='', directory='/path/to')
        summary_step = SummaryStep(MagicMock(full_file_name='/path/to/summary.log'))
        list_callback = [model_ckpt, summary_step]
        ckpt_file_path, _ = AnalyzeObject.get_file_path(list_callback)
        self.assertEqual(ckpt_file_path, '/path/to/test_model.ckpt')

    @mock.patch('os.path.getsize')
    def test_get_file_size(self, os_get_size_mock):
        """Test get_file_size method."""
        os_get_size_mock.return_value = 128
        file_size = AnalyzeObject.get_file_size('/file/path')
        self.assertEqual(file_size, 128)

    @mock.patch('os.path.getsize')
    def test_get_file_size_except(self, os_get_size_mock):
        """Test failed to get the size of file."""
        os_get_size_mock.side_effect = OSError
        analyzer = AnalyzeObject
        with self.assertRaises(LineageGetModelFileError) as context:
            analyzer.get_file_size('/file/path')
        self.assertTrue('Error when get model file size:' in str(context.exception))

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_size')
    def test_get_model_size(self, get_file_size_mock):
        """Test get_model_size method."""
        get_file_size_mock.return_value = 128
        analyzer = AnalyzeObject
        file_size = analyzer.get_model_size(ckpt_file_path='/file/path')
        self.assertEqual(file_size, 128)

    @mock.patch('mindinsight.lineagemgr.collection.model.model_lineage.AnalyzeObject.get_file_size')
    def test_get_model_size_no_ckpt(self, get_file_size_mock):
        """Test get_model_size method without ckpt file."""
        get_file_size_mock.return_value = 0
        analyzer = AnalyzeObject
        file_size = analyzer.get_model_size(ckpt_file_path='')
        self.assertEqual(file_size, 0)

    @mock.patch('builtins.vars')
    def test_get_optimizer_by_network(self, mock_vars):
        """Test get_optimizer_by_network."""
        mock_optimizer = Optimizer(Tensor(0.1))
        mock_cells = MagicMock()
        mock_cells.items.return_value = [{'key': mock_optimizer}]
        mock_vars.return_value = {
            '_cells': {
                'key': mock_optimizer
            }
        }
        res = AnalyzeObject.get_optimizer_by_network(MagicMock())
        self.assertEqual(res, mock_optimizer)

    @mock.patch('builtins.vars')
    def test_get_loss_fn_by_network(self, mock_vars):
        """Test get_loss_fn_by_network."""
        mock_cell1 = {'_cells': {'key': SoftmaxCrossEntropyWithLogits(0.2)}}
        mock_cell2 = {'_cells': {'opt': Optimizer(Tensor(0.1))}}
        mock_cell3 = {'_cells': {'loss': SoftmaxCrossEntropyWithLogits(0.1)}}
        mock_vars.side_effect = [mock_cell1, mock_cell2, mock_cell3]
        res = AnalyzeObject.get_loss_fn_by_network(MagicMock())
        self.assertEqual(res, mock_cell3['_cells']['loss'])

    @mock.patch('builtins.vars')
    def test_get_backbone_network_with_loss_cell(self, mock_vars):
        """Test get_backbone_network with loss_cell."""
        mock_cell = {'_cells': {'key': WithLossCell(MagicMock(),
                                                    SoftmaxCrossEntropyWithLogits(0.1))}
                     }
        mock_vars.return_value = mock_cell
        res = AnalyzeObject.get_backbone_network(MagicMock())
        self.assertEqual(res, 'MagicMock')

    @mock.patch('builtins.vars')
    def test_get_backbone_network(self, mock_vars):
        """Test get_backbone_network."""
        mock_net = TrainOneStepWithLossScaleCell()
        mock_net.network = MagicMock()
        mock_cell = {
            '_cells': {
                'key': mock_net
            }
        }
        mock_vars.return_value = mock_cell
        res = AnalyzeObject.get_backbone_network(MagicMock())
        self.assertEqual(res, 'MagicMock')


if __name__ == '__main__':
    unittest.main(verbosity=2)
