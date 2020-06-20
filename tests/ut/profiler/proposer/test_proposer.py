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
"""Test the proposer module."""
import os
from unittest import TestCase
from collections import OrderedDict

from mindinsight.profiler.proposer.proposer_factory import ProposerFactory
from mindinsight.profiler.proposer.compose_proposer import ComposeProposal


class TestPropose(TestCase):
    """Test the class of Proposer."""

    def setUp(self) -> None:
        """Initialization before test case execution."""
        self.profiling_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                           '../../../utils/resource/profiler'))
        self.device_id = "0"
        self.common_proposal_dict = OrderedDict()
        self.common_proposal_dict["common-profiler_tutorial"] = None
        self.step_trace_proposal_dict = OrderedDict()
        self.step_trace_proposal_dict["step_trace-iter_interval"] = ['0.5']

    def test_propose_compose(self):
        """Test the class of ComposeProposal."""
        proposal_dict = OrderedDict()
        proposal_dict["step_trace-proposer_type_label"] = None
        proposal_dict.update(self.step_trace_proposal_dict)
        proposal_dict["common-proposer_type_label"] = None
        proposal_dict.update(self.common_proposal_dict)
        type_list = ['step_trace', 'minddata', 'minddata_pipeline', 'common']
        condition = {"filter_condition": {'mode': "proc",
                                          "proc_name": "iteration_interval",
                                          "step_id": 0}}
        options = {'step_trace': {"iter_interval": condition}}
        cp = ComposeProposal(self.profiling_dir, self.device_id, type_list)
        result = cp.get_proposal(options=options)
        self.assertDictEqual(proposal_dict, result)

    def test_propose_compose_exception(self):
        """Test the class of ComposeProposal."""
        profiling_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../../../utils/resource/'))
        proposal_dict = OrderedDict()
        proposal_dict["common-proposer_type_label"] = None
        proposal_dict.update(self.common_proposal_dict)
        type_list = ['step_trace', 'common']
        condition = {"filter_condition": {'mode': "proc",
                                          "proc_name": "iteration_interval",
                                          "step_id": 0}}
        options = {'step_trace': {"iter_interval": condition}}
        cp = ComposeProposal(profiling_dir, self.device_id, type_list)
        result = cp.get_proposal(options=options)
        self.assertDictEqual(proposal_dict, result)

    def test_propose_compose_type_label(self):
        """Test the class of ComposeProposal."""
        proposal_dict = OrderedDict()
        proposal_dict["test_label-proposer_type_label"] = None
        proposal_dict.update(self.step_trace_proposal_dict)
        proposal_dict["common-proposer_type_label"] = None
        proposal_dict.update(self.common_proposal_dict)
        type_list = ['step_trace', 'common']
        condition = {"filter_condition": {'mode': "proc",
                                          "proc_name": "iteration_interval",
                                          "step_id": 0}}
        options = {'step_trace': {"iter_interval": condition}, "step_trace-type_label": "test_label"}
        cp = ComposeProposal(self.profiling_dir, self.device_id, type_list)
        result = cp.get_proposal(options=options)
        self.assertDictEqual(proposal_dict, result)

    def test_propose_compose_type_label_flag(self):
        """Test the class of ComposeProposal."""
        proposal_dict = OrderedDict()
        proposal_dict.update(self.step_trace_proposal_dict)
        proposal_dict.update(self.common_proposal_dict)

        type_list = ['step_trace', 'common']
        condition = {"filter_condition": {'mode': "proc",
                                          "proc_name": "iteration_interval",
                                          "step_id": 0}}
        options = {'step_trace': {"iter_interval": condition},
                   "step_trace-type_label": "test_label",
                   "type_label_flag": False}
        cp = ComposeProposal(self.profiling_dir, self.device_id, type_list)
        result = cp.get_proposal(options=options)
        self.assertDictEqual(proposal_dict, result)

    def test_propose_common(self):
        proposer_type = 'common'
        proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_dir, self.device_id)
        result = proposer.analyze()
        self.assertDictEqual(self.common_proposal_dict, result)

    def test_propose_step_trace(self):
        """Test the class of step trace."""
        proposer_type = 'step_trace'
        proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_dir, self.device_id)
        condition = {"filter_condition": {'mode': "proc",
                                          "proc_name": "iteration_interval",
                                          "step_id": 0}}
        options = {'step_trace': {"iter_interval": condition}}
        result = proposer.analyze(options)
        self.assertDictEqual(self.step_trace_proposal_dict, result)
