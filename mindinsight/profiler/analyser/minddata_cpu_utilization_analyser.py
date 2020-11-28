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
"""The MindDataCpuUtilizationAnalyser analyser class."""
import json
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerRawFileException, ProfilerFileNotFoundException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.analyser.minddata_analyser import MinddataAnalyser


class MinddataCpuUtilizationAnalyser(BaseAnalyser):
    """The analyser for analyzing minddata cpu utilization."""
    _cpu_utilization_display_filename = "minddata_cpu_utilization_{}.json"
    _minddata_pipeline_display_filename = "pipeline_profiling_{}.json"

    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self._steps_info = self._get_minddata_cpu_utilization_steps_info()

    def query(self, condition=None):
        """
        Query data according to the condition.

        Args:
            condition (dict): The search condition, only contains `filter_condition` parameter.
                Default: None.

        Returns:
            dict, the result after filtered, sorted and grouped.
        """
        if condition is None:
            condition = {}
        filter_condition = condition.get('filter_condition', {})
        log.info("Receive query request. %s", filter_condition)
        self._filter(filter_condition)
        result = dict()
        result["sampling_interval"] = self._data.get("sampling_interval")
        result["step_info"] = self._steps_info
        result["step_total_num"] = self._step_total_num
        result["cpu_processor_num"] = self._data.get("cpu_processor_num")
        # device average CPU utilization
        result["device_info"] = dict()
        for key in self._data.get("device_info").keys():
            arr = self._data.get("device_info")[key]
            avg_value = round(sum(arr) / len(arr))
            result["device_info"][key] = {"metrics": arr, "avg_value": avg_value}

        # process average CPU utilization
        result["process_info"] = dict()
        for key in self._data.get("process_info").keys():
            arr = self._data.get("process_info")[key]
            avg_value = round(sum(arr) / len(arr))
            result["process_info"][key] = {"metrics": arr, "avg_value": avg_value}

        # op average CPU utilization
        minddata_pipeline_op_info = self._get_minddata_pipeline_info()
        result["op_info"] = dict()
        result["op_info"]["op_list"] = []
        result["op_info"]["total_op_avg_value"] = dict()
        result["op_info"]["total_op_avg_value"]["user_utilization"] = 0
        result["op_info"]["total_op_avg_value"]["sys_utilization"] = 0

        for item in self._data.get("op_info"):
            # Filtering out non minddata pipeline operator
            if str(item.get("op_id")) == "-1":
                continue
            op_info_dict = dict()
            op_info_dict["metrics"] = dict()
            for key in item.get("metrics").keys():
                arr = item.get("metrics")[key]
                avg_value = round(sum(arr) / len(arr))
                op_info_dict["metrics"][key] = {"metrics": arr, "avg_value": avg_value}
                result["op_info"]["total_op_avg_value"][key] += avg_value
            op_info_dict["op_id"] = item.get("op_id")
            op_info = [i for i in minddata_pipeline_op_info if i.get("op_id") == item.get("op_id")]
            # op_info is like [{"num_workers":int,"op_id":int}]
            op_info_dict["num_workers"] = op_info[0].get("num_workers")
            result["op_info"]["op_list"].append(op_info_dict)
        return result

    def _load(self):
        """Load cpu_utilization info."""
        file_name = self._cpu_utilization_display_filename.format(self._device_id)
        file_path = os.path.join(self._profiling_dir, file_name)
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid cpu_utilization_info file path.")
        if not os.path.exists(file_path):
            log.error('Did not find the cpu utilization file: %s', file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the cpu utilization file:{}'.format(file_path))

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                self._data = json.load(file)
            except json.JSONDecodeError as err:
                log.exception(err)
                raise ProfilerRawFileException("Fail to parse cpu_utilization info file")

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.

                - start_step_id (int): The selected start step id.

                - end_step_id (int): The selected end step id.

        """
        start_step = filter_condition.get("start_step", 1)
        end_step = filter_condition.get("end_step", self._step_total_num)
        if start_step == 1 and end_step == self._step_total_num:
            return
        while not self._steps_info.count(str(start_step)):
            start_step += 1
        left_index = self._steps_info.index(str(start_step))
        while not self._steps_info.count(str(end_step)):
            end_step -= 1
        right_index = self._steps_info.index(str(end_step)) + \
            self._steps_info.count(str(end_step)) - 1
        self._steps_info = self._steps_info[left_index:right_index + 1]
        # filter device CPU utilization
        for key in self._data.get("device_info").keys():
            self._data["device_info"][key] = \
                self._data.get("device_info").get(key)[left_index:right_index + 1]

        # filter process CPU utilization
        for key in self._data.get("process_info").keys():
            self._data["process_info"][key] = self._data.get("process_info").get(key)[left_index:right_index + 1]

        # filter op CPU utilization
        for item in self._data.get("op_info"):
            for key in item.get("metrics").keys():
                item["metrics"][key] = item.get("metrics").get(key)[left_index:right_index + 1]

    def _get_minddata_cpu_utilization_steps_info(self):
        """Establish a connection between cpu utilization sampling points and host queue capacity"""
        steps_info = []
        left_index = 0
        right_index = 0
        time_stamp = self._data.get("time_stamp")
        queue_step_time_info = self._get_minddata_queue_step_time_info()
        self._step_total_num = len(queue_step_time_info)
        for item in time_stamp:
            while right_index < len(queue_step_time_info):
                # queue_step_time_info[][0]:step_num
                # queue_step_time_info[][1]:sample time
                if float(item) <= float(queue_step_time_info[right_index][1]):
                    if float(item) < (float(queue_step_time_info[left_index][1])) \
                            + float(queue_step_time_info[right_index][1]) / 2:
                        steps_info.append(queue_step_time_info[right_index][0])
                    else:
                        steps_info.append(queue_step_time_info[left_index][0])
                    break
                left_index = right_index
                right_index += 1

            if right_index == len(queue_step_time_info):
                steps_info.append(queue_step_time_info[right_index - 1][0])

        return steps_info

    def _get_minddata_queue_step_time_info(self):
        """Get the sampling time information at the steps of the host queue"""
        minddata_queue_step_time_info = []
        minddata_analyser = MinddataAnalyser(self._profiling_dir, self._device_id)
        file_path = minddata_analyser.get_device_queue_file_path()
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid device_queue file path")
        if not os.path.exists(file_path):
            log.error('Did not find the device queue file: %s', file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the device queue file:{}'.format(file_path))

        with open(file_path) as data_file:
            for line in data_file.readlines():
                op_info = line.split()
                # op_info[0]=="1":queue info, op_info[1]:Connector capacity,
                # op_info[2]:step_num, op_info[3]:Connector size, op_info[4]:sampling time
                if op_info and op_info[0] == "1":
                    minddata_queue_step_time_info.append([op_info[2], op_info[4]])
        return minddata_queue_step_time_info

    def _get_minddata_pipeline_info(self):
        """Get the number of thread cores in minddata pipeline operator"""
        file_name = self._minddata_pipeline_display_filename.format(self._device_id)
        file_path = os.path.join(self._profiling_dir, file_name)
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid minddata_pipeline_info file path.")
        if not os.path.exists(file_path):
            log.error('Did not find the minddata_pipeline file: %s', file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the minddata_pipeline file:{}'.format(file_path))

        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                minddata_pipeline_info = json.load(file)
            except json.JSONDecodeError as err:
                log.exception(err)
                raise ProfilerRawFileException("Fail to parse minddata pipeline file")

        minddata_pipeline_op_info = []
        for item in minddata_pipeline_info.get("op_info"):
            op_info_dict = dict()
            op_info_dict["op_id"] = item.get("op_id")
            op_info_dict["num_workers"] = item.get("num_workers")
            minddata_pipeline_op_info.append(op_info_dict)
        return minddata_pipeline_op_info
