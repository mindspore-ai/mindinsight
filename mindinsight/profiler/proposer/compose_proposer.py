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
"""The Compose Proposals."""
from collections import OrderedDict

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.util import get_options
from mindinsight.profiler.proposer.proposer_factory import ProposerFactory


class ComposeProposal:
    """Get the proposals from multiple different proposers."""
    def __init__(self, profiling_path, device_id, type_list=None):
        self.profiling_path = profiling_path
        self.device_id = device_id
        self.compose_proposer_type_list = type_list
        # Postfix of category label, used for UI to identify the label as category label.
        self.type_label_postfix = "-proposer_type_label"

    def get_proposal(self, options=None):
        """
        Get compose proposals.

        Args:
            options (dict): options for composed proposal.
                - compose_proposal_result: execution results of the already running proposers.
                - step_trace: include optional parameters for step trace，The dictionary key is iter_interval
                  used to get the analyser options for iteration interval time.

        Returns:
            dict, the proposals from multiple different proposers.

        Examples:
            >>> type_list = ['common', 'step_trace']
            >>> condition = {"filter_condition": {'mode': "proc", "proc_name": "iteration_interval"}}
            >>> options = {'step_trace': {"iter_interval": condition}}
            >>> cp = ComposeProposal(self.profiling_dir, self.device_id, type_list)
            >>> result_proposal = cp.get_proposal(options=options)
        """
        logger.info("The ComposeProposal is running")
        options = get_options(options)
        logger.debug("The 'options'　is %s", str(options))
        # The flag whether to write category label.
        type_label_flag = options.get("type_label_flag", True)
        compose_proposal_result = OrderedDict()
        logger.debug("The 'compose_proposer_type_list'　is %s", str(self.compose_proposer_type_list))
        for proposer_type in self.compose_proposer_type_list:
            proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_path, self.device_id)

            if proposer is None:
                continue

            # Write the result of proposals to option for other proposer to get.
            options["compose_proposal_result"] = compose_proposal_result

            result = proposer.analyze(options)
            # Insert category label.
            if result and type_label_flag:
                proposer_type_label = proposer_type + "-type_label"
                # Get the name of the category label, the default is the same as the proposer type.
                type_label_name = options.get(proposer_type_label, proposer_type)
                # Add postfix to category label name
                type_proposal_label = type_label_name + self.type_label_postfix
                compose_proposal_result[type_proposal_label] = None
                # Merge results to the proposals dictionary.
                compose_proposal_result.update(result)
            elif result and not type_label_flag:
                # Merge results to the proposals dictionary.
                compose_proposal_result.update(result)

        logger.debug("The 'compose_proposal_result' is %s", str(compose_proposal_result))
        return compose_proposal_result
