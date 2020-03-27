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
"""Test class EventWriter."""
import os
from unittest import TestCase

from mindinsight.lineagemgr.summary.event_writer import EventWriter
from mindinsight.lineagemgr.summary.summary_record import LineageSummary
from mindinsight.lineagemgr.summary.lineage_summary_analyzer import LineageSummaryAnalyzer


class TestEventWriter(TestCase):
    """Test write_event_to_file."""
    def setUp(self):
        """The setup of test."""
        self.log_path = "./test.log"

    def test_write_event_to_file(self):
        """Test write event to file."""
        run_context_args = {"train_network": "res"}
        content = LineageSummary.package_train_message(run_context_args).SerializeToString()
        event_writer = EventWriter(self.log_path, True)
        event_writer.write_event_to_file(content)

        lineage_info = LineageSummaryAnalyzer.get_summary_infos(self.log_path)
        self.assertEqual(
            lineage_info.train_lineage.train_lineage.algorithm.network,
            run_context_args.get("train_network")
        )

    def tearDown(self):
        """The setup of test."""
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except IOError:
                pass
