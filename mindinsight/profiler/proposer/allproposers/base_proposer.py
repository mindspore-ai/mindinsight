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
"""The proposer base class."""
from abc import ABC, abstractmethod

from marshmallow import ValidationError

from mindinsight.profiler.common.log import logger
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.profiler.common.validator.validate_path import \
    validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerPathErrorException


class Proposer(ABC):
    """The proposer base class."""

    def __init__(self, profiling_path, rank_id):
        self.profiling_path = self._normalize_profiling_dir(profiling_path)
        self.rank_id = rank_id

    def get_analyser_result(self, analyser_type, condition=None):
        logger.debug("The Proposer 'analyser_type' is %s, 'options' is %s", str(analyser_type), str(condition))
        analyser_result = {}
        try:
            analyser = AnalyserFactory.instance().get_analyser(analyser_type, self.profiling_path, self.rank_id)
            analyser_result = analyser.query(condition)
            logger.debug("The 'analyser_result' is %s, the 'condition' is %s.", str(analyser_result), str(condition))
        except MindInsightException as e:
            logger.warning(e)
        return analyser_result

    @abstractmethod
    def analyze(self, options=None):
        """analysis and get proposal."""
        raise NotImplementedError("Must define analyze function to inherit Class Propose")

    @staticmethod
    def _normalize_profiling_dir(profiling_dir):
        """
        Normalize the profiling dir.

        Args:
              profiling_dir (str): The directory where the parsed profiling files
                 are located.

        Returns:
              str, the normalized profiling dir.
        """
        try:
            normalized_profiling_dir = validate_and_normalize_path(
                profiling_dir, 'profiler'
            )
        except ValidationError:
            raise ProfilerPathErrorException('The profiling dir is invalid.')
        return normalized_profiling_dir
