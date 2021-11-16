# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""The minddata proposer."""
import math
import os

from collections import OrderedDict

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.analyser.minddata_analyser import MinddataAnalyser
from mindinsight.profiler.proposer.allproposers.base_proposer import Proposer
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.exceptions.exceptions import ProfilerRawFileException, ProfilerFileNotFoundException

DATA_PROCESS_WARNING = 'data_process'
DATA_TRANSMISSION_WARNING = 'data_transmission'
DEVICE_QUEUE_WARNING = 'device_queue_warning'


class MinddataProposer(Proposer):
    """The Minddata proposer."""

    def __init__(self, profiling_dir, rank_id):
        super().__init__(profiling_dir, rank_id)
        self.__proposer_type = "minddata"
        self.__proposal_dict = OrderedDict()
        self.empty_warning_threshold = int(MinddataAnalyser.DEVICE_QUEUE_EMPTY_WARNING_THRESHOLD * 100)

    def analyze(self, options=None):
        """
        Get the proposal from proposer.

        Args:
            options (dict): The options for proposer analysis.

        Returns:
            dict, the proposal from proposer instance，the dictionary key is a language internationalization
            label, and the value is used to format the value in the language internationalization string.

        Examples:
            >>> proposer_type = 'minddata'
            >>> proposer = ProposerFactory.instance().get_proposer(proposer_type, self.profiling_dir, self.rank_id)
            >>> result = proposer.analyze(options)
        """
        self.minddata_outer_bounds_analyze()
        self.minddata_cpu_utilization_proposal()
        return self.__proposal_dict

    def minddata_outer_bounds_analyze(self):
        """Get the proposals of minddata outer bounds."""
        minddata_dict = OrderedDict()
        minddata_analyser = AnalyserFactory.instance().get_analyser(
            'minddata', self.profiling_path, self.rank_id)
        get_next_queue_info, _ = minddata_analyser.analyse_get_next_info(info_type="queue")
        device_queue_info, _ = minddata_analyser.analyse_device_queue_info(info_type="queue")

        result = MinddataAnalyser.analyse_queue_summary(get_next_queue_info, device_queue_info)
        if "get_next_queue_info" in result:
            get_next_queue_info_summary = result.get("get_next_queue_info").get("summary", {})
            empty_batch = get_next_queue_info_summary.get("empty_batch_count")
            total_batch = get_next_queue_info_summary.get("total_batch")

            minddata_dict["minddata_get_next_queue"] = [empty_batch, total_batch]
            self.__proposal_dict.update(minddata_dict)
        if "device_queue_info" in result:
            get_next_queue_info_summary = result.get("device_queue_info").get("summary", {})
            full_batch = get_next_queue_info_summary.get("full_batch_count", 0)
            empty_batch = get_next_queue_info_summary.get("empty_batch_count", 0)
            total_batch = get_next_queue_info_summary.get("total_batch", 0)
            device_queue_empty_rate = math.ceil(empty_batch / total_batch * 100)
            minddata_dict["minddata_device_queue"] = [empty_batch, total_batch, full_batch, total_batch]
            self.__proposal_dict.update(minddata_dict)

        minddata_device_queue_rate = dict()
        for key, value in result.items():
            if isinstance(value, dict):
                status = value.get("status")
                if status == "warning":
                    if key == DATA_PROCESS_WARNING:
                        minddata_device_queue_rate['empty_rate'] = device_queue_empty_rate
                        minddata_device_queue_rate['empty_warning_threshold'] = \
                            self.empty_warning_threshold
                        break
                    elif key == DATA_TRANSMISSION_WARNING:
                        minddata_device_queue_rate['empty_rate'] = device_queue_empty_rate
                        minddata_device_queue_rate['empty_warning_threshold'] = \
                            self.empty_warning_threshold
                        break
                    elif key == DEVICE_QUEUE_WARNING:
                        minddata_dict[key] = ['warning']
                        self.__proposal_dict.update(minddata_dict)
                        break

        if minddata_device_queue_rate:
            minddata_dict["minddata_device_queue_rate"] = minddata_device_queue_rate
            self.__proposal_dict.update(minddata_dict)

    def minddata_cpu_utilization_proposal(self):
        """Get the proposals of minddata cpu utilization"""
        filename = "minddata_cpu_utilization_{}.json".format(self.rank_id)
        file_path = os.path.join(self.profiling_path, filename)
        # Forward compatibility, it is reasonable that the file does not exist.
        if not os.path.exists(file_path):
            return
        minddata_cpu_utilization = OrderedDict()
        minddata_cpu_utilization_analyser = AnalyserFactory.instance().get_analyser(
            'minddata_cpu_utilization', self.profiling_path, self.rank_id)
        try:
            idle_utilization_avg = minddata_cpu_utilization_analyser.get_idle_utilization_avg()
            # The maximum value of this cpu_activate_utilization_avg is 100%.
            cpu_activate_utilization_avg = 100 - idle_utilization_avg
            cpu_activate_utilization_threshold = 80
            if cpu_activate_utilization_avg > cpu_activate_utilization_threshold:
                minddata_cpu_utilization["minddata_cpu_utilization"] = [cpu_activate_utilization_avg]
                self.__proposal_dict.update(minddata_cpu_utilization)
        except (ProfilerRawFileException, ProfilerFileNotFoundException) as err:
            log.exception(err)
