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
"""The Parallel Data Analyser."""
import os
import re

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory


class ParallelAnalyser(BaseAnalyser):
    """Analyse parallel data from file."""

    _cluster_filename_reg = r'ascend_cluster_analyse_[a-z]+-parallel_[0-9]+_[0-9]+_[0-9]+\.csv'
    _step_trace_filename = 'step_trace_raw_{}_detail_time.csv'
    _flops_summary_filename = 'flops_summary_{}.json'
    _hccl_raw_filename = 'hccl_raw_{}.csv'
    _ascend_timeline_display_filename = 'ascend_timeline_display_{}.json'
    _cluster_filename = r'ascend_cluster_analyse_{}_{}_{}_{}.csv'

    _PIPELINE_PARALLEL = 'pipeline-parallel'

    _parallel_mode = ''
    _stage_num = 0
    _rank_size = 0
    _default_step = 0
    _cluster_step_trace_summary = []
    _flops_summary = []
    _rank_link_summary = []

    _RATE_DECIMAL_PLACES = 4

    def __init__(self, profiling_dir, rank_id):
        super().__init__(profiling_dir, rank_id)

        files = os.listdir(self._profiling_dir)
        for file in files:
            if not re.match(self._cluster_filename_reg, file):
                continue

            file_parts = file.split('_')
            self._parallel_mode = file_parts[3]
            self._stage_num = int(file_parts[4])
            self._rank_size = int(file_parts[5])
            break

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def _set_cluster_step_trace_summary(self):
        """
        Get step interval summary.

        Returns:
            dict,the cluster step trace summary
            if parallel_mode =='data-parallel':['step_interval', 'computation_time', 'communication_alone_time']
            elif parallel_mode =='model-parallel':['step_interval','computation_time', 'communication_alone_time']
            elif parallel_mode =='pipeline-parallel':['step_interval','computation_time', 'communication_alone_time'
                , 'stage_time','receive_alone_time', 'collective_communication_alone_time']
        """
        self._cluster_step_trace_summary = []
        for rank_id in range(self._rank_size):
            cluster_step_trace_analyser = AnalyserFactory.instance().get_analyser(
                'cluster_step_trace', self._profiling_dir, self._device_id)
            cluster_step_trace = cluster_step_trace_analyser.get_step_bottleneck_info(rank_id, self._default_step)
            if cluster_step_trace:
                self._cluster_step_trace_summary.append({
                    'rank_id': rank_id,
                    'data': cluster_step_trace
                })

    def get_step_interval(self):
        """
        Get step interval summary.

        Returns:
            list, the step interval of ranks,list({"rank_id":0, "step_interval":23.45})
        """
        step_interval_summary = []
        if not self._cluster_step_trace_summary:
            self._set_cluster_step_trace_summary()
        for step_trace in self._cluster_step_trace_summary:
            step_interval_summary.append({
                "rank_id": step_trace["rank_id"],
                "step_interval": step_trace["data"][0]
            })
        return step_interval_summary

    def _set_flops_summary(self):
        """Get the flops of rank."""
        cluster_flops_analyser = AnalyserFactory.instance().get_analyser(
            'cluster_flops', self._profiling_dir, self._device_id)
        self._flops_summary = cluster_flops_analyser.get_flops()

    def get_rank_flops_per_second(self):
        """
        Get the number of floating point operations per second (the unit is billion).

        Returns:
            list, the step interval of ranks,list({"rank_id":0, "data":23.45})
        """
        if not self._flops_summary:
            self._set_flops_summary()

        flops = []
        for flop in self._flops_summary:
            flops.append({
                "rank_id": flop["rank_id"],
                "FLOPS": flop["FLOPS"] if flop.get("FLOPS") else flop["cube_FLOPS"] + flop["vec_FLOPS"]
            })

        return flops

    def get_rank_link_summary(self):
        """
        Get the rank link data.

        Returns:
            list, the rank link data,list([src_des, link_type
            , communication_cost, communication_size, communication_brand_width])
        """
        if not self._rank_link_summary:
            cluster_hccl_analyser = AnalyserFactory.instance().get_analyser(
                'cluster_hccl', self._profiling_dir, self._device_id)
            self._rank_link_summary = cluster_hccl_analyser.get_cluster_link_info()["cluster_link_info"]
        return self._rank_link_summary

    def get_communication_rate(self):
        """Get the proportion of communication time in the entire step."""
        computation_time = 0
        communication_time = 0
        communication_rate = 0.0

        if not self._cluster_step_trace_summary:
            self._set_cluster_step_trace_summary()

        computation_time = sum([step_trace["data"][1] for step_trace in self._cluster_step_trace_summary])
        communication_time = sum([step_trace["data"][2] for step_trace in self._cluster_step_trace_summary])

        if computation_time > 0 and communication_time > 0:
            communication_rate = round(communication_time / (computation_time + communication_time)
                                       , self._RATE_DECIMAL_PLACES)

        return communication_rate

    def get_between_stage_communication_rate(self):
        """Get the proportion of communication time between stages, here use the receive operator time."""
        computation_time = 0
        communication_time = 0
        receive_time = 0
        communication_rate = 0.0
        if not self._cluster_step_trace_summary:
            self._set_cluster_step_trace_summary()

        if self._parallel_mode == self._PIPELINE_PARALLEL:
            computation_time = sum([step_trace["data"][1] for step_trace in self._cluster_step_trace_summary])
            communication_time = sum([step_trace["data"][2] for step_trace in self._cluster_step_trace_summary])
            receive_time = sum([step_trace["data"][4] for step_trace in self._cluster_step_trace_summary])

        if computation_time > 0 and communication_time > 0 and receive_time > 0:
            communication_rate = round(receive_time / (computation_time + communication_time)
                                       , self._RATE_DECIMAL_PLACES)

        return communication_rate

    def get_within_stage_communication_rate(self):
        """
        Get the proportion of communication time within the stage
        , Here is the communication time after excluding the receive operator time
        """

        communication_rates = []
        if self._parallel_mode != self._PIPELINE_PARALLEL:
            return communication_rates

        if not self._cluster_step_trace_summary:
            self._set_cluster_step_trace_summary()

        stage_summary = {}
        without_receive_summary = {}
        for step_trace in self._cluster_step_trace_summary:
            stage_id = int(step_trace["rank_id"] // (self._rank_size / self._stage_num) + 1)
            without_receive_summary[stage_id] = without_receive_summary.get(stage_id, 0) + step_trace["data"][5]
            stage_summary[stage_id] = stage_summary.get(stage_id, 0) + step_trace["data"][1] + step_trace["data"][2]
        for stage_id in stage_summary:
            communication_rates.append({
                'stage_id': stage_id,
                'rate': without_receive_summary[stage_id] / stage_summary[stage_id]
            })

        return communication_rates

    def get_rank_flops(self):
        """Get all flops of rank."""
        if not self._flops_summary:
            self._set_flops_summary()

        flops = []
        for flop in self._flops_summary:
            flops.append({
                "rank_id": flop["rank_id"],
                "FLOPs": flop["FLOPs"] if flop.get("FLOPs") else flop["cube_FLOPs"] + flop["vec_FLOPs"]
            })

        return flops

    @property
    def parallel_mode(self):
        """Get parallel model."""
        return self._parallel_mode

    @property
    def stage_num(self):
        """Get stage num."""
        return self._stage_num

    @property
    def rank_size(self):
        """Get rank size."""
        return self._rank_size
