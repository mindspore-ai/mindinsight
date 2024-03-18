# Copyright 2021 Huawei Technologies Co., Ltd
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
"""The cluster parallel proposer."""
import os

from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.log import logger


class ParallelProposer(Proposer):
    """The cluster parallel proposer."""

    _DATA_PARALLEL = 'data-parallel'
    _MODEL_PARALLEL = 'model-parallel'
    _PIPELINE_PARALLEL = 'pipeline-parallel'

    # the threshold for cluster data
    _step_interval_threshold = 0.2
    _flops_per_second_threshold = 0.2
    _rank_link_threshold = 0.2
    _data_parallel_communication_threshold = 0.1
    _model_parallel_communication_threshold = 0.1
    _between_stage_communication_threshold = 0.1
    _within_stage_communication_threshold = 0.1
    _flops_threshold = 0.2

    _VAL_DECIMAL_PLACES = 4
    _PERCENT_DECIMAL_PLACES = 2

    def __init__(self, profiling_dir, rank_id):
        super().__init__(profiling_dir, rank_id)
        self._parallel_analyser = AnalyserFactory.instance().get_analyser(
            'parallel', self.profiling_path, self.rank_id)
        self._parallel_mode = self._parallel_analyser.parallel_mode
        self._stage_num = self._parallel_analyser.stage_num
        self._rank_size = self._parallel_analyser.rank_size

        self._proposal_dict = {
            "step_interval": {},
            "flops_per_second": {},
            "cluster_link": [],
            "parallel_strategy": {
                "data_parallel_communication_rate": {},
                "model_parallel_communication_rate": {},
                "pipeline_parallel_between_stage": {},
                "pipeline_parallel_within_stage": {},
                "pipeline_parallel_flops": {}
            }
        }

        self._analyse_hccl = True
        self._analyse_flops = True
        self._analyse_op_segmentation = True
        self._validate_parallel_profiler_files()

    def analyze(self, options=None):
        """
        Get the proposal from proposer.

        Args:
            options (dict): The options for proposer analysis.

        Examples:
            >>> proposer_type = 'Parallel'
            >>> proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_dir, self.rank_id)
            >>> result = proposer.analyze(options)
        """
        if self._parallel_analyser.parallel_mode == self._DATA_PARALLEL:
            self._data_model_parallel_analyze()
        elif self._parallel_analyser.parallel_mode == self._MODEL_PARALLEL:
            self._data_model_parallel_analyze()
        elif self._parallel_analyser.parallel_mode == self._PIPELINE_PARALLEL:
            self._pipeline_parallel_analyze()
        self._clear_warning_node()

        return self._proposal_dict

    def _data_model_parallel_analyze(self):
        """The data-parallel and model-parallel analyze."""
        self._step_interval_analyze()
        self._flops_per_second_analyze()
        self._rank_link_analyze()
        self._communication_analyze()

    def _pipeline_parallel_analyze(self):
        """The pipeline-parallel analyze."""
        self._step_interval_analyze()
        self._flops_per_second_analyze()
        self._rank_link_analyze()
        self._between_stage_communication_analyze()
        self._within_stage_communication_analyze()
        self._flops_analyze()

    def _step_interval_analyze(self):
        """The step interval analyze, find the device with a long step time."""
        if not self._analyse_op_segmentation:
            return

        step_intervals = self._parallel_analyser.get_step_interval()
        avg_step_interval = sum([s["step_interval"] for s in step_intervals]) / len(step_intervals)
        rank_id = -1
        val = 0.0
        percent = 0.0
        for step_interval in step_intervals:
            # get how much more than the average
            if avg_step_interval == 0:
                proportion = 0.0
            else:
                proportion = step_interval["step_interval"] / avg_step_interval - 1
            if proportion > self._step_interval_threshold and proportion > percent:
                rank_id = step_interval["rank_id"]
                val = step_interval["step_interval"]
                percent = proportion
        if rank_id >= 0:
            self._proposal_dict["step_interval"]["rank_id"] = rank_id
            self._proposal_dict["step_interval"]["val"] = round(val, self._VAL_DECIMAL_PLACES)
            self._proposal_dict["step_interval"]["percent"] = round(percent * 100, self._PERCENT_DECIMAL_PLACES)

    def _flops_per_second_analyze(self):
        """The flops per second analyze, find slow rank."""
        if not self._analyse_flops:
            return

        flops_per_seconds = self._parallel_analyser.get_rank_flops_per_second()
        avg_flop = sum([f["FLOPS"] for f in flops_per_seconds]) / len(flops_per_seconds)
        rank_id = -1
        val = 0.0
        percent = 0.0
        for flops in flops_per_seconds:
            proportion = (avg_flop - flops["FLOPS"]) / avg_flop
            if proportion > self._flops_per_second_threshold and proportion > percent:
                rank_id = flops["rank_id"]
                val = flops["FLOPS"]
                percent = proportion
        if rank_id >= 0:
            self._proposal_dict["flops_per_second"]["rank_id"] = rank_id
            self._proposal_dict["flops_per_second"]["val"] = round(val, self._VAL_DECIMAL_PLACES)
            self._proposal_dict["flops_per_second"]["percent"] = round(percent * 100, self._PERCENT_DECIMAL_PLACES)

    def _rank_link_analyze(self):
        """The bandwidth of rank link analyze, find slow rank link."""
        if not self._analyse_hccl:
            return

        rank_links = self._parallel_analyser.get_rank_link_summary()

        # distinguish between RDMA and SDMA
        type_links = {}
        sum_bandwidth = {}
        for rank_link in rank_links:
            src, des = [int(r) for r in rank_link[0].split('-')]
            if src == des:
                continue
            link_type = rank_link[1]
            if link_type not in type_links.keys():
                type_links[link_type] = []
                sum_bandwidth[link_type] = 0
            type_links[link_type].append([src, des, rank_link[4]])
            sum_bandwidth[link_type] = sum_bandwidth[link_type] + rank_link[4]

        warning_link = {}
        for link_type in type_links:
            warning_link[link_type] = []
            avg_bandwidth = sum_bandwidth[link_type] / len(type_links[link_type])
            for link in type_links[link_type]:
                if not avg_bandwidth:
                    continue
                proportion = (avg_bandwidth - link[2]) / avg_bandwidth
                if proportion > self._rank_link_threshold and \
                        (not warning_link[link_type] or proportion > warning_link[link_type][4]):
                    warning_link[link_type] = (link[0], link[1], link_type, link[2], proportion)

        for link in warning_link:
            link_info = warning_link.get(link)
            if link_info:
                self._proposal_dict.get("cluster_link").append({
                    "src_rank": link_info[0],
                    "des_rank": link_info[1],
                    "link_type": link_info[2],
                    "val": round(link_info[3], self._VAL_DECIMAL_PLACES),
                    "percent": round(link_info[4] * 100, self._PERCENT_DECIMAL_PLACES)
                })

    def _communication_analyze(self):
        """The communication time analyze, get the percentage of communication time."""
        if not self._analyse_op_segmentation:
            return

        communication_rate = self._parallel_analyser.get_communication_rate()
        if self._parallel_mode == self._DATA_PARALLEL and \
                communication_rate > self._data_parallel_communication_threshold:
            self._proposal_dict.get("parallel_strategy").get("data_parallel_communication_rate")["val"] = \
                round(communication_rate * 100, self._PERCENT_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("data_parallel_communication_rate")["threshold"] = \
                round(self._data_parallel_communication_threshold * 100, self._PERCENT_DECIMAL_PLACES)
        elif self._parallel_mode == self._MODEL_PARALLEL and \
                communication_rate > self._model_parallel_communication_threshold:
            self._proposal_dict.get("parallel_strategy").get("model_parallel_communication_rate")["val"] = \
                round(communication_rate * 100, self._PERCENT_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("model_parallel_communication_rate")["threshold"] = \
                round(self._model_parallel_communication_threshold * 100, self._PERCENT_DECIMAL_PLACES)

    def _between_stage_communication_analyze(self):
        """The communication time of between stages analyze, get the percentage of communication time."""
        if not self._analyse_op_segmentation:
            return

        communication_rate = self._parallel_analyser.get_between_stage_communication_rate()
        if communication_rate > self._between_stage_communication_threshold:
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_between_stage")["val"] = \
                round(communication_rate * 100, self._PERCENT_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_between_stage")["threshold"] = \
                round(self._between_stage_communication_threshold * 100, self._PERCENT_DECIMAL_PLACES)

    def _within_stage_communication_analyze(self):
        """The communication time of within stage analyze, get the percentage of communication time."""
        if not self._analyse_op_segmentation:
            return

        communication_rates = self._parallel_analyser.get_within_stage_communication_rate()
        stage_id = -1
        val = 0.0
        for communication_rate in communication_rates:
            if communication_rate['rate'] > self._within_stage_communication_threshold and \
                    communication_rate['rate'] > val:
                stage_id = communication_rate['stage_id']
                val = communication_rate['rate']
        if stage_id > 0:
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_within_stage")["val"] = \
                round(val * 100, self._PERCENT_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_within_stage")["threshold"] = \
                round(self._within_stage_communication_threshold * 100, self._PERCENT_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_within_stage")["stage"] = stage_id

    def _flops_analyze(self):
        """The flops of stage analyze, find the stage with the most computation."""
        if not self._analyse_flops:
            return

        rank_flops = self._parallel_analyser.get_rank_flops()

        stage_rank_avg_flops = {}
        stage_rank_size = self._rank_size // self._stage_num
        for rank_flop in rank_flops:
            stage = int(rank_flop["rank_id"] // stage_rank_size + 1)
            stage_rank_avg_flops[stage] = stage_rank_avg_flops.get(stage, 0) + rank_flop["FLOPs"] / stage_rank_size

        stage_avg = sum([stage_rank_avg_flops[stage] for stage in stage_rank_avg_flops]) / len(stage_rank_avg_flops)

        warn_stage = -1
        percent = 0.0
        val = 0.0
        for stage in stage_rank_avg_flops:
            proportion = stage_rank_avg_flops[stage] / stage_avg - 1
            if proportion > self._flops_threshold and proportion > percent:
                warn_stage = stage
                percent = proportion
                val = stage_rank_avg_flops.get(stage)
        if warn_stage >= 0:
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_flops")["stage"] = warn_stage
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_flops")["val"] = \
                round(val, self._VAL_DECIMAL_PLACES)
            self._proposal_dict.get("parallel_strategy").get("pipeline_parallel_flops")["percent"] = \
                round(percent * 100, self._PERCENT_DECIMAL_PLACES)

    def _clear_warning_node(self):
        """Clear useless warning node."""
        for warning in list(self._proposal_dict.get("parallel_strategy").keys()):
            if not self._proposal_dict["parallel_strategy"][warning]:
                del self._proposal_dict.get("parallel_strategy")[warning]

        for warning in list(self._proposal_dict.keys()):
            if not self._proposal_dict[warning]:
                del self._proposal_dict[warning]

    def _validate_parallel_profiler_files(self):
        """validate the parallel files"""
        step_trace_filename = 'step_trace_raw_{rank_id}_detail_time.csv'
        cluster_filename = 'ascend_cluster_analyse_{parallel_mode}_{stage_num}_{rank_size}_{rank_id}.csv'
        flops_filename = 'flops_summary_{rank_id}.json'
        hccl_filename = 'hccl_raw_{rank_id}.csv'

        file_warning = 'parallel performance analysis cannot find the file %s, Please collect all device files.'

        files = os.listdir(self.profiling_path)

        for rank_id in range(self._rank_size):

            file_name = step_trace_filename.format(rank_id=rank_id)
            if file_name not in files and self._analyse_op_segmentation:
                self._analyse_op_segmentation = False
                logger.warning(file_warning, file_name)

            file_name = cluster_filename.format(parallel_mode=self._parallel_mode, stage_num=self._stage_num
                                                , rank_size=self._rank_size, rank_id=rank_id)
            if file_name not in files and self._analyse_op_segmentation:
                self._analyse_op_segmentation = False
                logger.warning(file_warning, file_name)

            file_name = flops_filename.format(rank_id=rank_id)
            if file_name not in files and self._analyse_flops:
                self._analyse_flops = False
                logger.warning(file_warning, file_name)

            file_name = hccl_filename.format(rank_id=rank_id)
            if file_name not in files and self._analyse_hccl:
                self._analyse_hccl = False
                logger.warning(file_warning, file_name)
