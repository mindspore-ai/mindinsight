# Copyright 2022-2022 Huawei Technologies Co., Ltd
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
"""The msadvisor proposer."""
import os
import json
import stat

from collections import OrderedDict

from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerDirNotFoundException


class MsadvisorProposer(Proposer):
    """The msadvisor proposer."""

    def __init__(self, profiling_dir, rank_id):
        super().__init__(profiling_dir, rank_id)
        self.__proposer_type = "msadvisor"
        self.__proposal_dict = OrderedDict()

    def analyze(self, options=None):
        """
        Get the proposal from msadvisor proposer.

        Args:
            options (dict): options for proposer analysis. Default: None.

        Returns:
            dict, the proposal from msadvisor proposer instance，the dictionary key is "msadvisor-proposer"
            including different models in msadvisor, such as AICPUModel, TransDataModel.

        Examples:
            >>> proposer_type = 'msadvisor'
            >>> proposer = MsadvisorProposer.instance().get_proposer(proposer_type, self.profiling_dir, self.device_id)
            >>> result = proposer.analyze(options)
        """
        try:
            logger.info("The MsadvisorProposer is running.")
            self.read_recommendation()
        except ProfilerDirNotFoundException as err:
            logger.warning(err)
        finally:
            pass

        return self.__proposal_dict

    def read_recommendation(self):
        """
        Get advice from msadvisor recommendation json file.

        Raises:
            ProfilerDirNotFoundException: If recommendation path does not exist.
        """
        recommendation_path = os.path.join(self.profiling_path, "msadvisor")
        recommendation_path = os.path.join(recommendation_path, "device_" + self.rank_id)
        recommendation_path = os.path.join(recommendation_path, "recommendation")
        if not os.path.exists(recommendation_path):
            raise ProfilerDirNotFoundException("Msadvisor recommendation dir does not exist!")
        file_list = os.listdir(recommendation_path)
        file_list.sort(key=lambda fn: os.path.getmtime(os.path.join(recommendation_path, fn)), reverse=True)
        for rec_file in file_list:
            if rec_file.endswith('.json'):
                recommendation_path = os.path.join(recommendation_path, rec_file)
                recommendation_path = validate_and_normalize_path(recommendation_path,
                                                                  'recommendation', allow_parent_dir=True)
                with os.fdopen(os.open(recommendation_path, os.O_RDONLY,
                                       stat.S_IRUSR | stat.S_IWUSR), "r") as recommendation_file:
                    recommendation = json.load(recommendation_file)
                    recommendation['msadvisor-proposer'] = recommendation.pop('model', None)
                    logger.info(recommendation)
                    self.__proposal_dict.update(recommendation)
                    logger.info("The MsadvisorProposer ran successfully.")
                break
