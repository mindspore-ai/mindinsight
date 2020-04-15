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
"""This module is used to collect lineage information of model training."""
import json
import os

import numpy as np

from mindinsight.lineagemgr.summary.summary_record import LineageSummary
from mindinsight.utils.exceptions import \
    MindInsightException
from mindinsight.lineagemgr.common.validator.validate import validate_train_run_context, \
    validate_eval_run_context, validate_file_path, validate_network, \
    validate_int_params, validate_summary_record, validate_raise_exception,\
    validate_user_defined_info
from mindinsight.lineagemgr.common.exceptions.error_code import LineageErrors, LineageErrorMsg
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageParamRunContextError, \
    LineageGetModelFileError, LineageLogError
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.utils import try_except
from mindinsight.lineagemgr.common.validator.model_parameter import RunContextArgs, \
    EvalParameter
from mindinsight.lineagemgr.collection.model.base import Metadata

try:
    from mindspore.common.tensor import Tensor
    from mindspore.train.callback import Callback, RunContext, ModelCheckpoint, SummaryStep
    from mindspore.nn import Cell, Optimizer, WithLossCell, TrainOneStepWithLossScaleCell
    from mindspore.nn.loss.loss import _Loss
    from mindspore.dataset.engine import Dataset, MindDataset
    import mindspore.dataset as ds
except (ImportError, ModuleNotFoundError):
    log.warning('MindSpore Not Found!')


class TrainLineage(Callback):
    """
    Collect lineage of a training job.

    Args:
        summary_record (SummaryRecord): SummaryRecord is used to record
            the summary value, and summary_record is an instance of SummaryRecord,
            see mindspore.train.summary.SummaryRecord.
        raise_exception (bool): Whether to raise exception when error occurs in
            TrainLineage. If True, raise exception. If False, catch exception
            and continue. Default: False.

    Raises:
        MindInsightException: If validating parameter fails.
        LineageLogError: If recording lineage information fails.

    Examples:
        >>> from mindinsight.lineagemgr import TrainLineage
        >>> from mindspore.train.callback import ModelCheckpoint, SummaryStep
        >>> from mindspore.train.summary import SummaryRecord
        >>> model = Model(train_network)
        >>> model_ckpt = ModelCheckpoint(directory='/dir/to/save/model/')
        >>> summary_writer = SummaryRecord(log_dir='./')
        >>> summary_callback = SummaryStep(summary_writer, flush_step=2)
        >>> lineagemgr = TrainLineage(summary_record=summary_writer)
        >>> model.train(epoch_num, dataset, callbacks=[model_ckpt, summary_callback, lineagemgr])
    """
    def __init__(self, summary_record, raise_exception=False, user_defined_info=None):
        super(TrainLineage, self).__init__()
        try:
            validate_raise_exception(raise_exception)
            self.raise_exception = raise_exception

            validate_summary_record(summary_record)
            self.summary_record = summary_record

            summary_log_path = summary_record.full_file_name
            validate_file_path(summary_log_path)
            self.lineage_log_path = summary_log_path + '_lineage'

            self.initial_learning_rate = None

            self.user_defined_info = user_defined_info
            if user_defined_info:
                validate_user_defined_info(user_defined_info)

        except MindInsightException as err:
            log.error(err)
            if raise_exception:
                raise

    @try_except(log)
    def begin(self, run_context):
        """
        Initialize the training progress when the training job begins.

        Args:
            run_context (RunContext): It contains all lineage information,
                see mindspore.train.callback.RunContext.

        Raises:
            MindInsightException: If validating parameter fails.
        """
        log.info('Initialize training lineage collection...')

        if self.user_defined_info:
            lineage_summary = LineageSummary(summary_log_path=self.lineage_log_path)
            lineage_summary.record_user_defined_info(self.user_defined_info)

        if not isinstance(run_context, RunContext):
            error_msg = f'Invalid TrainLineage run_context.'
            log.error(error_msg)
            raise LineageParamRunContextError(error_msg)

        run_context_args = run_context.original_args()
        if not self.initial_learning_rate:
            optimizer = run_context_args.get('optimizer')
            if optimizer and not isinstance(optimizer, Optimizer):
                log.error("The parameter optimizer is invalid. It should be an instance of "
                          "mindspore.nn.optim.optimizer.Optimizer.")
                raise MindInsightException(error=LineageErrors.PARAM_OPTIMIZER_ERROR,
                                           message=LineageErrorMsg.PARAM_OPTIMIZER_ERROR.value)
            if optimizer:
                log.info('Obtaining initial learning rate...')
                self.initial_learning_rate = AnalyzeObject.analyze_optimizer(optimizer)
                log.debug('initial_learning_rate: %s', self.initial_learning_rate)
            else:
                network = run_context_args.get('train_network')
                validate_network(network)
                optimizer = AnalyzeObject.get_optimizer_by_network(network)
                self.initial_learning_rate = AnalyzeObject.analyze_optimizer(optimizer)
                log.debug('initial_learning_rate: %s', self.initial_learning_rate)

        # get train dataset graph
        train_dataset = run_context_args.get('train_dataset')
        dataset_graph_dict = ds.serialize(train_dataset)
        dataset_graph_json_str = json.dumps(dataset_graph_dict, indent=2)
        dataset_graph_dict = json.loads(dataset_graph_json_str)
        log.info('Logging dataset graph...')
        try:
            lineage_summary = LineageSummary(self.lineage_log_path)
            lineage_summary.record_dataset_graph(dataset_graph=dataset_graph_dict)
        except Exception as error:
            error_msg = f'Dataset graph log error in TrainLineage begin: {error}'
            log.error(error_msg)
            raise LineageLogError(error_msg)
        log.info('Dataset graph logged successfully.')

    @try_except(log)
    def end(self, run_context):
        """
        Collect lineage information when the training job ends.

        Args:
            run_context (RunContext): It contains all lineage information,
                see mindspore.train.callback.RunContext.

        Raises:
            LineageLogError: If recording lineage information fails.
        """
        log.info('Start to collect training lineage...')
        if not isinstance(run_context, RunContext):
            error_msg = f'Invalid TrainLineage run_context.'
            log.error(error_msg)
            raise LineageParamRunContextError(error_msg)

        run_context_args = run_context.original_args()
        validate_train_run_context(RunContextArgs, run_context_args)

        train_lineage = dict()
        train_lineage = AnalyzeObject.get_network_args(
            run_context_args, train_lineage
        )

        train_dataset = run_context_args.get('train_dataset')
        callbacks = run_context_args.get('list_callback')
        list_callback = getattr(callbacks, '_callbacks', [])

        log.info('Obtaining model files...')
        ckpt_file_path, _ = AnalyzeObject.get_file_path(list_callback)

        train_lineage[Metadata.learning_rate] = self.initial_learning_rate
        train_lineage[Metadata.epoch] = run_context_args.get('epoch_num')
        train_lineage[Metadata.step_num] = run_context_args.get('cur_step_num')
        train_lineage[Metadata.parallel_mode] = run_context_args.get('parallel_mode')
        train_lineage[Metadata.device_num] = run_context_args.get('device_number')
        train_lineage[Metadata.batch_size] = run_context_args.get('batch_num')
        model_path_dict = {
            'ckpt': ckpt_file_path
        }
        train_lineage[Metadata.model_path] = json.dumps(model_path_dict)

        log.info('Calculating model size...')
        train_lineage[Metadata.model_size] = AnalyzeObject.get_model_size(
            ckpt_file_path
        )
        log.debug('model_size: %s', train_lineage[Metadata.model_size])

        log.info('Analyzing dataset object...')
        train_lineage = AnalyzeObject.analyze_dataset(train_dataset, train_lineage, 'train')

        log.info('Logging lineage information...')
        try:
            lineage_summary = LineageSummary(self.lineage_log_path)
            lineage_summary.record_train_lineage(train_lineage)
        except IOError as error:
            error_msg = f'End error in TrainLineage: {error}'
            log.error(error_msg)
            raise LineageLogError(error_msg)
        except Exception as error:
            error_msg = f'End error in TrainLineage: {error}'
            log.error(error_msg)
            log.error('Fail to log the lineage of the training job.')
            raise LineageLogError(error_msg)
        log.info('The lineage of the training job has logged successfully.')


class EvalLineage(Callback):
    """
    Collect lineage of an evaluation job.

    Args:
        summary_record (SummaryRecord): SummaryRecord is used to record
            the summary value, and summary_record is an instance of SummaryRecord,
            see mindspore.train.summary.SummaryRecord.
        raise_exception (bool): Whether to raise exception when error occurs in
            EvalLineage. If True, raise exception. If False, catch exception
            and continue. Default: False.

    Raises:
        MindInsightException: If validating parameter fails.
        LineageLogError: If recording lineage information fails.

    Examples:
        >>> from mindinsight.lineagemgr import EvalLineage
        >>> from mindspore.train.callback import ModelCheckpoint, SummaryStep
        >>> from mindspore.train.summary import SummaryRecord
        >>> model = Model(train_network)
        >>> model_ckpt = ModelCheckpoint(directory='/dir/to/save/model/')
        >>> summary_writer = SummaryRecord(log_dir='./')
        >>> summary_callback = SummaryStep(summary_writer, flush_step=2)
        >>> lineagemgr = EvalLineage(summary_record=summary_writer)
        >>> model.eval(epoch_num, dataset, callbacks=[model_ckpt, summary_callback, lineagemgr])
    """
    def __init__(self, summary_record, raise_exception=False, user_defined_info=None):
        super(EvalLineage, self).__init__()
        try:
            validate_raise_exception(raise_exception)
            self.raise_exception = raise_exception

            validate_summary_record(summary_record)
            self.summary_record = summary_record

            summary_log_path = summary_record.full_file_name
            validate_file_path(summary_log_path)
            self.lineage_log_path = summary_log_path + '_lineage'

            self.user_defined_info = user_defined_info
            if user_defined_info:
                validate_user_defined_info(user_defined_info)

        except MindInsightException as err:
            log.error(err)
            if raise_exception:
                raise

    @try_except(log)
    def end(self, run_context):
        """
        Collect lineage information when the training job ends.

        Args:
            run_context (RunContext): It contains all lineage information,
                see mindspore.train.callback.RunContext.

        Raises:
            MindInsightException: If validating parameter fails.
            LineageLogError: If recording lineage information fails.
        """
        if self.user_defined_info:
            lineage_summary = LineageSummary(summary_log_path=self.lineage_log_path)
            lineage_summary.record_user_defined_info(self.user_defined_info)

        if not isinstance(run_context, RunContext):
            error_msg = f'Invalid EvalLineage run_context.'
            log.error(error_msg)
            raise LineageParamRunContextError(error_msg)

        run_context_args = run_context.original_args()
        validate_eval_run_context(EvalParameter, run_context_args)

        valid_dataset = run_context_args.get('valid_dataset')

        eval_lineage = dict()
        metrics = run_context_args.get('metrics')
        eval_lineage[Metadata.metrics] = json.dumps(metrics)
        eval_lineage[Metadata.step_num] = run_context_args.get('cur_step_num')

        log.info('Analyzing dataset object...')
        eval_lineage = AnalyzeObject.analyze_dataset(valid_dataset, eval_lineage, 'valid')

        log.info('Logging evaluation job lineage...')
        try:
            lineage_summary = LineageSummary(self.lineage_log_path)
            lineage_summary.record_evaluation_lineage(eval_lineage)
        except IOError as error:
            error_msg = f'End error in EvalLineage: {error}'
            log.error(error_msg)
            log.error('Fail to log the lineage of the evaluation job.')
            raise LineageLogError(error_msg)
        except Exception as error:
            error_msg = f'End error in EvalLineage: {error}'
            log.error(error_msg)
            log.error('Fail to log the lineage of the evaluation job.')
            raise LineageLogError(error_msg)
        log.info('The lineage of the evaluation job has logged successfully.')


class AnalyzeObject:
    """Analyze class object in MindSpore."""

    @staticmethod
    def get_optimizer_by_network(network):
        """
        Get optimizer by analyzing network.

        Args:
            network (Cell): See mindspore.nn.Cell.

        Returns:
            Optimizer, an Optimizer object.
        """
        optimizer = None
        net_args = vars(network) if network else {}
        net_cell = net_args.get('_cells') if net_args else {}
        for _, value in net_cell.items():
            if isinstance(value, Optimizer):
                optimizer = value
                break
        return optimizer

    @staticmethod
    def get_loss_fn_by_network(network):
        """
        Get loss function by analyzing network.

        Args:
            network (Cell): See mindspore.nn.Cell.

        Returns:
            Loss_fn, a Cell object.
        """
        loss_fn = None
        inner_cell_list = []
        net_args = vars(network) if network else {}
        net_cell = net_args.get('_cells') if net_args else {}
        for _, value in net_cell.items():
            if isinstance(value, Cell) and \
                    not isinstance(value, Optimizer):
                inner_cell_list.append(value)

        while inner_cell_list:
            inner_net_args = vars(inner_cell_list[0])
            inner_net_cell = inner_net_args.get('_cells')

            for value in inner_net_cell.values():
                if isinstance(value, _Loss):
                    loss_fn = value
                    break
                if isinstance(value, Cell):
                    inner_cell_list.append(value)
            if loss_fn:
                break

            inner_cell_list.pop(0)

        return loss_fn

    @staticmethod
    def get_backbone_network(network):
        """
        Get the name of backbone network.

        Args:
            network (Cell): The train network.

        Returns:
            str, the name of the backbone network.
        """
        with_loss_cell = False
        backbone = None
        net_args = vars(network) if network else {}
        net_cell = net_args.get('_cells') if net_args else {}

        for _, value in net_cell.items():
            if isinstance(value, WithLossCell):
                backbone = getattr(value, '_backbone')
                with_loss_cell = True
                break

        if with_loss_cell:
            backbone_name = type(backbone).__name__ \
                if backbone else None
        elif isinstance(network, TrainOneStepWithLossScaleCell):
            backbone = getattr(network, 'network')
            backbone_name = type(backbone).__name__ \
                if backbone else None
        else:
            backbone_name = type(network).__name__ \
                if network else None
        return backbone_name

    @staticmethod
    def analyze_optimizer(optimizer):
        """
        Analyze Optimizer, a Cell object of MindSpore.

        In this way, we can obtain the following attributes:
            learning_rate (float),
            weight_decay (float),
            momentum (float),
            weights (float).

        Args:
            optimizer (Optimizer): See mindspore.nn.optim.Optimizer.

        Returns:
            float, the learning rate that the optimizer adopted.
        """
        learning_rate = None
        if isinstance(optimizer, Optimizer):
            learning_rate = getattr(optimizer, 'learning_rate', None)

        if learning_rate:
            learning_rate = learning_rate.default_input

            # Get the real learning rate value
            if isinstance(learning_rate, Tensor):
                learning_rate = learning_rate.asnumpy()
                if learning_rate.ndim == 0:
                    learning_rate = np.atleast_1d(learning_rate)
                learning_rate = list(learning_rate)
            elif isinstance(learning_rate, float):
                learning_rate = [learning_rate]

        return learning_rate[0] if learning_rate else None

    @staticmethod
    def analyze_dataset(dataset, lineage_dict, dataset_type):
        """
        Analyze Dataset, a Dataset object of MindSpore.

        In this way, we can obtain the following attributes:
            dataset_path (str),
            train_dataset_size (int),
            valid_dataset_size (int),
            batch_size (int)

        Args:
            dataset (Dataset): See mindspore.dataengine.datasets.Dataset.
            lineage_dict (dict): A dict contains lineage metadata.
            dataset_type (str): Dataset type, train or valid.

        Returns:
            dict, the lineage metadata.
        """
        dataset_batch_size = dataset.get_dataset_size()
        if dataset_batch_size is not None:
            validate_int_params(dataset_batch_size, 'dataset_batch_size')
        log.debug('dataset_batch_size: %d', dataset_batch_size)
        dataset_path = AnalyzeObject.get_dataset_path_wrapped(dataset)
        if dataset_path:
            dataset_path = '/'.join(dataset_path.split('/')[:-1])

        step_num = lineage_dict.get('step_num')
        validate_int_params(step_num, 'step_num')
        log.debug('step_num: %d', step_num)

        if dataset_type == 'train':
            lineage_dict[Metadata.train_dataset_path] = dataset_path
            epoch = lineage_dict.get('epoch')
            train_dataset_size = dataset_batch_size * (step_num / epoch)
            lineage_dict[Metadata.train_dataset_size] = int(train_dataset_size)
        elif dataset_type == 'valid':
            lineage_dict[Metadata.valid_dataset_path] = dataset_path
            lineage_dict[Metadata.valid_dataset_size] = dataset_batch_size * step_num

        return lineage_dict

    def get_dataset_path(self, output_dataset):
        """
        Get dataset path of MindDataset object.

        Args:
            output_dataset (Union[MindDataset, Dataset]): See
                mindspore.dataengine.datasets.Dataset.

        Returns:
            str, dataset path.
        """
        if isinstance(output_dataset, MindDataset):
            return output_dataset.dataset_file
        return self.get_dataset_path(output_dataset.input[0])

    @staticmethod
    def get_dataset_path_wrapped(dataset):
        """
        A wrapper for obtaining dataset path.

        Args:
            dataset (Union[MindDataset, Dataset]): See
                mindspore.dataengine.datasets.Dataset.

        Returns:
            str, dataset path.
        """
        dataset_path = None
        if isinstance(dataset, Dataset):
            try:
                dataset_path = AnalyzeObject().get_dataset_path(dataset)
            except IndexError:
                dataset_path = None
        validate_file_path(dataset_path, allow_empty=True)
        return dataset_path

    @staticmethod
    def get_file_path(list_callback):
        """
        Get ckpt_file_name and summary_log_path from MindSpore callback list.

        Args:
            list_callback (list[Callback]): The MindSpore training Callback list.

        Returns:
            tuple, contains ckpt_file_name and summary_log_path.
        """
        ckpt_file_path = None
        summary_log_path = None
        for callback in list_callback:
            if isinstance(callback, ModelCheckpoint):
                ckpt_file_path = callback.latest_ckpt_file_name
            if isinstance(callback, SummaryStep):
                summary_log_path = callback.summary_file_name

        if ckpt_file_path:
            validate_file_path(ckpt_file_path)
            ckpt_file_path = os.path.realpath(ckpt_file_path)

        if summary_log_path:
            validate_file_path(summary_log_path)
            summary_log_path = os.path.realpath(summary_log_path)

        return ckpt_file_path, summary_log_path

    @staticmethod
    def get_file_size(file_path):
        """
        Get the file size.

        Args:
            file_path (str): The file path.

        Returns:
            int, the file size.
        """
        try:
            return os.path.getsize(file_path)
        except (OSError, IOError) as error:
            error_msg = f"Error when get model file size: {error}"
            log.error(error_msg)
            raise LineageGetModelFileError(error_msg)

    @staticmethod
    def get_model_size(ckpt_file_path):
        """
        Get model the total size of the model file and the checkpoint file.

        Args:
            ckpt_file_path (str): The checkpoint file path.

        Returns:
            int, the total file size.
        """
        if ckpt_file_path:
            ckpt_file_path = os.path.realpath(ckpt_file_path)
            ckpt_file_size = AnalyzeObject.get_file_size(ckpt_file_path)
        else:
            ckpt_file_size = 0

        return ckpt_file_size

    @staticmethod
    def get_network_args(run_context_args, train_lineage):
        """
        Get the parameters related to the network,
        such as optimizer, loss function.

        Args:
            run_context_args (dict): It contains all information of the training job.
            train_lineage (dict): A dict contains lineage metadata.

        Returns:
            dict, the lineage metadata.
        """
        network = run_context_args.get('train_network')
        validate_network(network)
        optimizer = run_context_args.get('optimizer')
        if not optimizer:
            optimizer = AnalyzeObject.get_optimizer_by_network(network)
        loss_fn = run_context_args.get('loss_fn')
        if not loss_fn:
            loss_fn = AnalyzeObject.get_loss_fn_by_network(network)
            loss = None
        else:
            loss = run_context_args.get('net_outputs')

        if loss:
            log.info('Calculating loss...')
            loss_numpy = loss.asnumpy()
            loss = float(np.atleast_1d(loss_numpy)[0])
            log.debug('loss: %s', loss)
            train_lineage[Metadata.loss] = loss
        else:
            train_lineage[Metadata.loss] = None

        # Analyze classname of optimizer, loss function and training network.
        train_lineage[Metadata.optimizer] = type(optimizer).__name__ \
            if optimizer else None
        train_lineage[Metadata.train_network] = AnalyzeObject.get_backbone_network(network)
        train_lineage[Metadata.loss_function] = type(loss_fn).__name__ \
            if loss_fn else None

        return train_lineage
