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
"""The common proposer."""
from collections import OrderedDict

from mindinsight.profiler.common.util import get_options
from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer
from mindinsight.profiler.common.log import logger


class CommonProposer(Proposer):
    """The common proposer."""
    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self.__proposal_dict = OrderedDict()
        self.__proposal_dict["common-profiler_tutorial"] = None

    def analyze(self, options=None):
        """
        Get the proposal from proposer.

        Args:
            options: options for proposer analysis

        Returns:
            dict, the proposal from proposer instance.
        """
        logger.info('The CommonProposer　is running')
        options = get_options(options)
        return self.__proposal_dict
