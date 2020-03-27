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
"""Record message to summary log."""
import time

from mindinsight.datavisual.proto_files.mindinsight_summary_pb2 import Event
from mindinsight.lineagemgr.summary.event_writer import EventWriter
from ._summary_adapter import package_dataset_graph


class LineageSummary:
    """
    Lineage summary record.
    Recording train lineage and evaluation lineage to summary log.

    Args:
        summary_log_path (str): Summary log path.
        override (bool): If override the summary log exist.

    Raises:
        IOError: Write to summary log failed or file_path is a dir.

    Examples:
        >>> summary_log_path = "./test.log"
        >>> train_lineage = {"train_network": "ResNet"}
        >>> lineage_summary = LineageSummary(summary_log_path=summary_log_path)
        >>> lineage_summary.record_train_lineage(train_lineage)
    """
    def __init__(self, summary_log_path=None, override=False):
        self.event_writer = EventWriter(summary_log_path, override)

    @staticmethod
    def package_train_message(run_context_args):
        """
        Package train message.

        Args:
            run_context_args (dict): The train lineage info to log.

        Returns:
            Event, the proto message event contains train lineage.
        """
        train_lineage_event = Event()
        train_lineage_event.wall_time = time.time()

        # Init train_lineage message.
        train_lineage = train_lineage_event.train_lineage

        # Construct algorithm message.
        if run_context_args.get('train_network') is not None:
            train_lineage.algorithm.network = run_context_args.get('train_network')
        if run_context_args.get('loss') is not None:
            train_lineage.algorithm.loss = run_context_args.get('loss')
        # Construct hyper_parameters message.
        LineageSummary.construct_hyper_parameters(train_lineage, run_context_args)
        # Construct train_dataset message.
        if run_context_args.get('train_dataset_path') is not None:
            train_lineage.train_dataset.train_dataset_path = run_context_args.get(
                'train_dataset_path')
        if run_context_args.get('train_dataset_size') is not None:
            train_lineage.train_dataset.train_dataset_size = run_context_args.get(
                'train_dataset_size')
        # Construct model message
        if run_context_args.get('model_path') is not None:
            train_lineage.model.path = run_context_args.get('model_path')
        if run_context_args.get('model_size') is not None:
            train_lineage.model.size = run_context_args.get('model_size')

        return train_lineage_event

    @staticmethod
    def construct_hyper_parameters(train_lineage, run_context_args):
        """
        Construct hyper-parameters.

        Args:
            train_lineage (TrainLineage): TrainLineage defined in  protobuf.
            run_context_args (dict): The run_context_args.
        """
        if run_context_args.get('learning_rate') is not None:
            train_lineage.hyper_parameters.learning_rate = run_context_args.get('learning_rate')
        if run_context_args.get('optimizer') is not None:
            train_lineage.hyper_parameters.optimizer = run_context_args.get('optimizer')
        if run_context_args.get('loss_function') is not None:
            train_lineage.hyper_parameters.loss_function = run_context_args.get('loss_function')
        if run_context_args.get('epoch') is not None:
            train_lineage.hyper_parameters.epoch = run_context_args.get('epoch')
        if run_context_args.get('parallel_mode') is not None:
            train_lineage.hyper_parameters.parallel_mode = run_context_args.get('parallel_mode')
        if run_context_args.get('device_num') is not None:
            train_lineage.hyper_parameters.device_num = run_context_args.get('device_num')
        if run_context_args.get('batch_size') is not None:
            train_lineage.hyper_parameters.batch_size = run_context_args.get('batch_size')

    def record_train_lineage(self, run_context_args):
        """
        Record train_lineage to summary log.

        Args:
            run_context_args (dict): The train lineage info to log.
        """
        self.event_writer.write_event_to_file(
            LineageSummary.package_train_message(run_context_args).SerializeToString()
        )

    @staticmethod
    def package_evaluation_message(run_context_args):
        """
        Record evaluation lineage.

        Args:
            run_context_args (dict): The evaluation lineage info to log.

        Returns:
            Event, the proto message event contains evaluation lineage.
        """
        train_lineage_event = Event()
        train_lineage_event.wall_time = time.time()

        # Init evaluation_lineage message.
        evaluation_lineage = train_lineage_event.evaluation_lineage
        if run_context_args.get('metrics') is not None:
            evaluation_lineage.metric = run_context_args.get('metrics')
        # Construct valid_dataset message.
        if run_context_args.get('valid_dataset_path') is not None:
            evaluation_lineage.valid_dataset.valid_dataset_path = \
                run_context_args.get('valid_dataset_path')
        if run_context_args.get('valid_dataset_size') is not None:
            evaluation_lineage.valid_dataset.valid_dataset_size = \
                run_context_args.get('valid_dataset_size')

        return train_lineage_event

    def record_evaluation_lineage(self, run_context_args):
        """
        Record evaluation_lineage to sumamry log.

        Args:
            run_context_args (dict): The evaluation lineage info to log.

        """
        self.event_writer.write_event_to_file(
            LineageSummary.package_evaluation_message(run_context_args).SerializeToString()
        )

    def record_dataset_graph(self, dataset_graph):
        """
        Record dataset graph to summary log.

        Args:
            dataset_graph (dict): The dataset graph to log.
        """
        self.event_writer.write_event_to_file(
            package_dataset_graph(dataset_graph).SerializeToString()
        )
