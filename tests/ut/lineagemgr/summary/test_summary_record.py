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
"""Test class SummaryRecord."""
import json
from unittest import TestCase, mock

from mindinsight.lineagemgr.summary.event_writer import EventWriter
from mindinsight.lineagemgr.summary.summary_record import LineageSummary


class TestSummaryRecord(TestCase):
    """Test summary record."""
    def setUp(self):
        """The setup of test."""
        self.run_context_args = dict()
        self.run_context_args["train_network"] = "test_train_network"
        self.run_context_args["loss"] = 0.1
        self.run_context_args["learning_rate"] = 0.1
        self.run_context_args["optimizer"] = "test_optimizer"
        self.run_context_args["loss_function"] = "test_loss_function"
        self.run_context_args["epoch"] = 1
        self.run_context_args["parallel_mode"] = "test_parallel_mode"
        self.run_context_args["device_num"] = 1
        self.run_context_args["batch_size"] = 1
        self.run_context_args["train_dataset_path"] = "test_train_dataset_path"
        self.run_context_args["train_dataset_size"] = 1
        self.run_context_args["model_path"] = "test_model_path"
        self.run_context_args["model_size"] = 1

        self.eval_args = dict()
        self.eval_args["metrics"] = json.dumps({"acc": "test"})
        self.eval_args["valid_dataset_path"] = "test_valid_dataset_path"
        self.eval_args["valid_dataset_size"] = 1

        self.hard_info_args = dict()
        self.hard_info_args["pid"] = 1
        self.hard_info_args["process_start_time"] = 921226.0

    def test_package_train_message(self):
        """Test package_train_message."""
        event = LineageSummary.package_train_message(self.run_context_args)
        self.assertEqual(
            event.train_lineage.algorithm.network, self.run_context_args.get("train_network"))
        self.assertEqual(
            event.train_lineage.hyper_parameters.optimizer, self.run_context_args.get("optimizer"))
        self.assertEqual(
            event.train_lineage.train_dataset.train_dataset_path,
            self.run_context_args.get("train_dataset_path")
        )

    @mock.patch.object(EventWriter, "write_event_to_file")
    def test_record_train_lineage(self, write_file):
        """Test record_train_lineage."""
        write_file.return_value = True
        lineage_summray = LineageSummary(lineage_log_dir="test.log")
        lineage_summray.record_train_lineage(self.run_context_args)

    def test_package_evaluation_message(self):
        """Test package_evaluation_message."""
        event = LineageSummary.package_evaluation_message(self.eval_args)
        self.assertEqual(event.evaluation_lineage.metric, self.eval_args.get("metrics"))

    @mock.patch.object(EventWriter, "write_event_to_file")
    def test_record_eval_lineage(self, write_file):
        """Test record_eval_lineage."""
        write_file.return_value = True
        lineage_summray = LineageSummary(lineage_log_dir="test.log")
        lineage_summray.record_evaluation_lineage(self.eval_args)
