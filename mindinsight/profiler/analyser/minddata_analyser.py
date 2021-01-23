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
"""Data process analyser."""
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path

class MinddataAnalyser(BaseAnalyser):
    """The Minddata profiling analyser."""

    DEVICE_QUEUE_EMPTY_WARNING_THRESHOLD = 0.7
    DEVICE_QUEUE_NOT_EMPTY_THRESHOLD = 0.95

    def analyse_get_next_info(self, info_type="all"):
        """
        Analyse the get_next operation info.

        Args:
            info_type (str): The info type to return, default return both queue and time info,
            other options are ["queue", "time"].

        Returns:
            list[list], all get_next operation info, each info contains node_name, start, end, queue_size.
        """
        # init queue info result
        queue_info = dict()
        queue_size_list = []
        empty_step_count = 0

        # init time info result
        time_info = dict()
        time_list = []
        total_cost = 0

        file_name = "minddata_aicpu_" + self._device_id + ".txt"
        file_path = MinddataAnalyser.find_target_file(self._profiling_dir, file_name)

        # the GPU minddata profiler file
        if not file_path:
            file_name = "minddata_getnext_profiling_" + self._device_id + ".txt"
            file_path = MinddataAnalyser.find_target_file(self._profiling_dir, file_name)

        if file_path:
            file_path = validate_and_normalize_path(
                file_path, raise_key="Invalid minddata_getnext file path.")
            with open(file_path) as data_file:
                for line in data_file.readlines():
                    node_info = line.split()
                    # Ascend:GetNext_dequeue_wait GPU:GetNext
                    if node_info and node_info[0][0:7] == "GetNext":
                        # analyse target info type
                        if len(node_info) > 3 and info_type in ["all", "queue"]:
                            queue_size_list.append(int(node_info[3]))
                            if node_info[3] == '0':
                                empty_step_count += 1
                        if len(node_info) > 2 and info_type in ["all", "time"]:
                            one_step_cost_time = (float(node_info[2]) - float(node_info[1]))/1e3
                            # The time stamp in Ascend is μs but in GPU is ns.
                            if 'minddata_getnext_profiling' in file_name:
                                one_step_cost_time = one_step_cost_time/1e3
                            time_list.append(one_step_cost_time)
                            total_cost += one_step_cost_time
                if info_type in ["all", "queue"]:
                    queue_info["size"] = len(queue_size_list)
                    queue_info["info"] = {"queue": queue_size_list}
                    queue_info["summary"] = {
                        "queue_summary": {
                            "empty_queue": empty_step_count
                        }
                    }
                if len(node_info) > 2 and info_type in ["all", "time"]:
                    time_info["size"] = len(time_list)
                    time_info["info"] = {"get_next": time_list}
                    if time_info["size"]:
                        time_info["summary"] = {
                            "time_summary": {
                                "avg_cost": "0" if not time_list else str(total_cost / len(time_list))
                            }
                        }

        return queue_info, time_info

    def analyse_device_queue_info(self, info_type="all"):
        """
        Analyse the device_queue operation info.

        Args:
            info_type (str): The info type to return, default return both queue and time info,
            other options are ["queue", "time"].

        Returns:
            dict, queue size info.
            dict, time cost info.
        """
        # init queue info result
        queue_info = dict()
        get_time_list, push_time_list, total_time_list = [], [], []
        total_cost, total_push, total_get = 0, 0, 0

        # init time info result
        time_info = dict()
        queue_size_list = []
        empty_step, full_step = 0, 0

        file_path = self.get_device_queue_file_path()

        if file_path:
            file_path = validate_and_normalize_path(
                file_path, raise_key="Invalid device_queue file path.")
            with open(file_path) as data_file:
                for line in data_file.readlines():
                    op_info = line.split()
                    # time info
                    if op_info and op_info[0] == "0" and info_type in ["all", "time"]:
                        # sub_type: 0 get_time, 1 push time, 2 total time
                        # op_info: 2: step num 3: cost time
                        if op_info[1] == "0":
                            get_time_list.append([int(op_info[2]), float(op_info[3])])
                            total_get += float(op_info[3])
                        elif op_info[1] == "1":
                            push_time_list.append([int(op_info[2]), float(op_info[3])])
                            total_push += float(op_info[3])
                        elif op_info[1] == "2":
                            total_time_list.append([int(op_info[2]), float(op_info[3])])
                            total_cost += float(op_info[3])
                    elif op_info and op_info[0] == "1" and info_type in ["all", "queue"]:
                        queue_size_list.append([int(op_info[2]), int(op_info[3])])
                        if op_info[1] == op_info[3]:
                            full_step += 1
                        if op_info[3] == "0":
                            empty_step += 1
            if info_type in ["all", "time"]:
                total_time_list = MinddataAnalyser.sort_step(total_time_list)
                push_time_list = MinddataAnalyser.sort_step(push_time_list)
                get_time_list = MinddataAnalyser.sort_step(get_time_list)

                time_info["size"] = len(total_time_list)
                time_info["info"] = {"total_cost": total_time_list,
                                     "push_cost": push_time_list,
                                     "get_cost": get_time_list}
                if time_info["size"]:
                    time_info["summary"] = {"time_summary": {"avg_cost": total_cost/time_info["size"]}}
                    time_info["summary"]["time_summary"]["get_cost"] = total_get/time_info["size"]
                    time_info["summary"]["time_summary"]["push_cost"] = total_push/time_info["size"]

            if info_type in ["all", "queue"]:
                queue_size_list = MinddataAnalyser.sort_step(queue_size_list)

                queue_info["size"] = len(queue_size_list)
                queue_info["info"] = {"queue": queue_size_list}
                queue_info["summary"] = {"queue_summary": {"empty_queue": empty_step}}
                queue_info["summary"]["queue_summary"]["full_queue"] = full_step

        return queue_info, time_info

    def get_device_queue_file_path(self):
        """
        Get device queue file path.

        Returns:
            str, the file path.
        """
        device_queue_file_name = "device_queue_profiling_" + self._device_id + ".txt"
        device_queue_file_path = MinddataAnalyser.find_target_file(self._profiling_dir, device_queue_file_name)
        feed_file_name = "dataset_iterator_profiling_" + self._device_id + ".txt"
        feed_file_path = MinddataAnalyser.find_target_file(self._profiling_dir, feed_file_name)
        file_path = ""
        if device_queue_file_path:
            file_path = device_queue_file_path
        elif not device_queue_file_path and feed_file_path:
            file_path = feed_file_path

        return file_path

    @staticmethod
    def analyse_queue_summary(get_next_queue_info, device_queue_info):
        """
        Analyse the queue summary info.

        Args:
            get_next_queue_info (dict): the get_next queue info return by ananlyser.
            device_queue_info (dict): the device queue info return by ananlyser.

        Returns:
            dict, the summary of queue.
        """
        result = {}
        if get_next_queue_info and device_queue_info:
            result = {"data_process": {"status": "normal"},
                      "device_queue_op": {"status": "normal"},
                      "data_transmission": {"status": "normal"},
                      "get_next": {"status": "normal"}}

            get_next_queue_empty_count = get_next_queue_info.get(
                "summary", {}).get("queue_summary", {}).get("empty_queue", 0)
            result["get_next_queue_info"] = {
                "summary": {
                    "empty_batch_count": get_next_queue_empty_count,
                    "total_batch": get_next_queue_info.get("size")
                }
            }

            device_queue_empty_count = device_queue_info.get(
                "summary", {}).get("queue_summary", {}).get("empty_queue", 0)
            device_queue_full_count = device_queue_info.get(
                "summary", {}).get("queue_summary", {}).get("full_queue", 0)

            result["device_queue_info"] = {"summary": {
                "empty_batch_count": device_queue_empty_count,
                "full_batch_count": device_queue_full_count,
                "total_batch": device_queue_info.get("size")}}

            # Adapt to the case that the first step data in the GPU is always empty
            if get_next_queue_empty_count > 1:
                if device_queue_empty_count > device_queue_info.get("size", 0)*\
                        MinddataAnalyser.DEVICE_QUEUE_EMPTY_WARNING_THRESHOLD:
                    result["data_process"]["status"] = "warning"
                elif device_queue_empty_count < device_queue_info.get("size", 0)*\
                        MinddataAnalyser.DEVICE_QUEUE_NOT_EMPTY_THRESHOLD:
                    result["data_transmission"]["status"] = "warning"
                    result["device_queue_op"]["status"] = "warning"

        elif device_queue_info and not get_next_queue_info:
            result = {"data_process": {"status": "normal"},
                      "fpbp": {"status": "normal"}}

            device_queue_empty_count = device_queue_info.get(
                "summary", {}).get("queue_summary", {}).get("empty_queue", 0)
            device_queue_full_count = device_queue_info.get(
                "summary", {}).get("queue_summary", {}).get("full_queue", 0)

            result["device_queue_info"] = {
                "summary": {
                    "empty_batch_count": device_queue_empty_count,
                    "full_batch_count": device_queue_full_count,
                    "total_batch": device_queue_info.get("size")
                }
            }

            if device_queue_empty_count > device_queue_info.get("size", 0)*0.7:
                result["data_process"]["status"] = "warning"

        return result


    @staticmethod
    def sort_step(step_info_list):
        """
        Sorting the list by the first item and return the list of second item.

        Args:
            step_info_list (list): the step info, contains [step_num, info].

        Returns:
            list, the info list sorted by step.
        """
        step_info_list.sort(key=lambda x: x[0])
        result = []
        for item in step_info_list:
            result.append(item[1])
        return result

    @staticmethod
    def find_target_file(file_dir, file_name):
        """
        Find the target file in dir, and return the find file's abs path or "".

        Args:
            file_dir (str): The target file dir.
            file_name (str): The target file name.

        Returns:
            str, the abs file path.
        """
        target_file_path = ""
        for root_path, _, file_names in os.walk(file_dir):
            for item in file_names:
                if item == file_name:
                    target_file_path = os.path.join(root_path, file_name)

        return target_file_path

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def _load(self):
        """Load data according to the parsed profiling files."""
