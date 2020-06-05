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
"""The step trace proposer."""
from collections import OrderedDict

from mindinsight.profiler.common.util import get_options
from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer
from mindinsight.profiler.common.log import logger


class StepTraceProposer(Proposer):
    """The step trace proposer."""

    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self.__step_trace_iter_interval_threshold = 0.5
        self.__proposer_type = "step_trace"
        self.__proposal_dict = OrderedDict()
        self.__iter_interval_label = "step_trace-iter_interval"

    def analyze(self, options=None):
        """
        Get the proposal from proposer.

        Args:
            options (dict): options for proposer analysis.
                - step_trace: include optional parameters for step trace，The dictionary key is iter_interval
                  used to get the analyser options for iteration interval time.

        Returns:
            dict, the proposal from proposer instance，the dictionary key is a language internationalization
            label, and the value is used to format the value in the language internationalization string.

        Examples:
            >>> proposer_type = 'step_trace'
            >>> proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_dir, self.device_id)
            >>> result = proposer.analyze(options)
        """
        logger.info("The StepTraceProposer is running")

        options = get_options(options)
        logger.debug("The StepTraceProposer 'options' is %s", str(options))
        step_trace_condition = options.get("step_trace", {})
        # Get the proposals of iteration interval.
        self._iter_interval_analyze(step_trace_condition)
        return self.__proposal_dict

    def _iter_interval_analyze(self, step_trace_condition):
        """Get the proposals of iteration interval."""
        iter_interval_dict = OrderedDict()
        default_iter_interval_lst = [0]
        iter_interval_condition = step_trace_condition.get("iter_interval", {})
        analyser_result = self.get_analyser_result(self.__proposer_type, condition=iter_interval_condition)
        iter_interval_length_lst = analyser_result.get("info", {}).get("iteration_interval",
                                                                       default_iter_interval_lst)
        logger.debug("The 'iter_interval_length_lst' is %s", str(iter_interval_length_lst))
        # Check the iter_interval_length_lst.
        if not isinstance(iter_interval_length_lst, list) or not iter_interval_length_lst:
            logger.warning("The 'iter_interval_length_lst' is %s,　it is null or not a list",
                           str(iter_interval_length_lst))
        else:
            if iter_interval_length_lst[0] > self.__step_trace_iter_interval_threshold:
                iter_interval_dict[self.__iter_interval_label] = [str(self.__step_trace_iter_interval_threshold)]
                self.__proposal_dict.update(iter_interval_dict)
