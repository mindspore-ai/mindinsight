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
"""The minddata pipeline proposer."""
from collections import OrderedDict

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerParamValueErrorException
from mindinsight.profiler.common.util import get_options
from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer


class MinddataPipelineProposer(Proposer):
    """
    The minddata pipeline proposer.

    Args:
        profiling_dir (str): The directory in which the parsed profiling data
            resides.
        device_id (str): The device ID.
    """
    _general_label = "minddata_pipeline-general"
    _map_op_label = 'minddata_pipeline-map_op'
    _generator_op_label = 'minddata_pipeline-generator_op'
    _dataset_op_label = 'minddata_pipeline-dataset_op'
    _batch_op_label = 'minddata_pipeline-batch_op'

    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self.__proposer_type = "minddata_pipeline"
        self.__proposal_dict = OrderedDict()

    def analyze(self, options=None):
        """
        Analyse and get proposal.

        Args:
            options (dict): The options for analysis. Default: None.

        Returns:
            OrderedDict, the proposal for minddata pipeline.
        """
        threshold = self._get_threshold(options)
        condition = {
            'filter_condition': {
                'threshold': threshold
            }
        }
        analyser_result = self.get_analyser_result(
            self.__proposer_type, condition=condition
        )
        self._organize_proposal_result(analyser_result)

        return self.__proposal_dict if self.__proposal_dict else None

    def _get_threshold(self, options):
        """
        Get the threshold of the minddata pipeline queue usage rate.

        Args:
            options (dict): The options for analysis.

        Returns:
            list[float], the threshold of the minddata pipeline queue usage rate.

        Raises:
            ProfilerParamValueErrorException: If the threshold is invalid.
        """
        options = get_options(options)
        pipeline_options = options.get(self.__proposer_type)
        threshold = None
        if pipeline_options:
            threshold = options.get('threshold')
        if threshold is None:
            threshold = [0.8, 0.2]
        if not isinstance(threshold, list) or len(threshold) != 2:
            raise ProfilerParamValueErrorException('The threshold is invalid.')
        return threshold

    def _organize_proposal_result(self, analyser_result):
        """
        Organize the proposal result.

        Args:
            analyser_result (dict): The result data of the minddata pipeline
                analyser.
        """
        all_op_names = []
        dataset_op_names = []
        generator_op_names = []
        batch_op_names = []
        map_op_names = []
        pipeline_op_infos = analyser_result.get('object')
        for op_info in pipeline_op_infos:
            op_id = op_info[0]
            op_type = op_info[1]
            op_name = '_'.join([op_type, str(op_id)])
            all_op_names.append(op_name)

            children_ids = op_info[-1]
            if not children_ids:
                dataset_op_names.append(op_name)
            elif op_type == 'MapOp':
                map_op_names.append(op_name)
            elif op_type == 'GeneratorOp':
                generator_op_names.append(op_name)
            elif op_type == 'BatchOp':
                batch_op_names.append(op_name)

        if all_op_names:
            self.__proposal_dict[self._general_label] = ['/'.join(all_op_names)]
        if dataset_op_names:
            self.__proposal_dict[self._dataset_op_label] = [
                '/'.join(dataset_op_names)
            ]
        if generator_op_names:
            self.__proposal_dict[self._generator_op_label] = [
                '/'.join(generator_op_names)
            ]
        if map_op_names:
            self.__proposal_dict[self._map_op_label] = ['/'.join(map_op_names)]
        if batch_op_names:
            self.__proposal_dict[self._batch_op_label] = [
                '/'.join(batch_op_names)
            ]
