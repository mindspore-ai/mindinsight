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
"""The specific cluster analyser class"""
import json
import os
import csv
import re

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException, \
    ProfilerDirNotFoundException, ProfilerIOException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class ClusterAnalyser(BaseAnalyser):
    """The analyser for analyzing the cluster."""

    def __init__(self, cluster_profiler_dir, device_id):
        super().__init__(cluster_profiler_dir, device_id)
        self._cluster_profiler_dir = cluster_profiler_dir
        self._target_dir_path = self._get_target_dir_path()
        self._cluster_rank_ids = self._get_cluster_rank_ids()

    def _get_target_dir_path(self):
        """Get the target directory path."""
        target_dir_path = self._cluster_profiler_dir
        target_dir_path = validate_and_normalize_path(
            target_dir_path, raise_key="Invalid profiler dir path.")
        if not os.path.exists(target_dir_path):
            log.error('Did not find cluster_profiler dir : %s', target_dir_path)
            raise ProfilerDirNotFoundException(msg='Did not find cluster_profiler dir:{}'.format(target_dir_path))

        return target_dir_path

    def _get_cluster_rank_ids(self):
        """Get the logical card number list in cluster training."""
        cluster_rank_ids = []
        entries = os.scandir(self._target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.startswith('step_trace_raw'):
                # index3：rank_id
                rank_id = entry.name.split("_")[3]
                if not rank_id.isdigit():
                    log.error("The value of rank id should be a number.")
                    raise TypeError("The value of rank id should be a number.")
                cluster_rank_ids.append(int(rank_id))
        cluster_rank_ids.sort()
        # Judge whether the rank ids are continuous.
        if (cluster_rank_ids[-1] - cluster_rank_ids[0]) != len(cluster_rank_ids) - 1:
            log.warning("The rank ids are not continuous，"
                        "please check for missing files. Rank ids: %s", cluster_rank_ids)
        return cluster_rank_ids

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """


class ClusterStepTraceAnalyser(ClusterAnalyser):
    """The analyser for analyzing the cluster step trace."""
    def __init__(self, cluster_profiler_dir, device_id):
        super().__init__(cluster_profiler_dir, device_id)
        self._none_sort_col_names = []
        self._parallel_mode, self._stage_num, self._rank_size = \
            self._get_parallel_context()
        self._col_names = self._get_col_names()
        self._total_step_num = self._get_total_step_num()

    def _get_parallel_context(self):
        """Get the parallel mode from file name."""
        parallel_mode = "data-parallel"
        stage_num = 1
        rank_size = 1
        for filename in os.listdir(self._target_dir_path):
            if filename.startswith('ascend_cluster_analyse'):
                # the format of filename is
                # 'ascend_cluster_analyse_{parallel-mode}_{stage_num}_{rank_size}_{rank_id}.csv'
                parallel_mode = filename.split('_')[3]
                stage_num = int(filename.split('_')[4])
                rank_size = int(filename.split('_')[5])

        return parallel_mode, stage_num, rank_size

    def _get_col_names(self):
        """Get the column names depends on parallel mode."""
        col_names = ['iteration_interval', 'fp_and_bp', 'tail']
        if self._parallel_mode == 'model-parallel':
            col_names = ['iteration_interval', 'communication_alone', 'computation']
        elif self._parallel_mode == 'pipeline-parallel':
            col_names = ['iteration_interval', 'receive_alone', 'stage', 'communication_alone',
                         'computation', 'collective_communication_alone']

        return col_names

    def _get_total_step_num(self):
        """Get the num of train step."""
        total_step_num = 0

        entries = os.scandir(self._target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.startswith('step_trace_raw'):
                file_path = os.path.join(self._target_dir_path, entry.name)
                with open(file_path, 'r') as src_file:
                    lines = src_file.readlines()
                # The penultimate line represents the information of the last step
                # The step num index is 0
                if len(lines) > 1:
                    total_step_num = lines[-2].split(',')[0]
                break
        return total_step_num

    def _get_cluster_step_trace_info(self, step_num):
        """Get cluster step trace info."""
        cluster_step_trace_info = list()
        for item in self._cluster_rank_ids:
            step_trace_info = self._get_step_trace_info(item, step_num)
            step_trace_info.append(item)
            cluster_step_trace_info.append(step_trace_info)
        self._cluster_info_size = len(cluster_step_trace_info)
        return cluster_step_trace_info

    def _get_step_trace_info(self, rank_id, step_num):
        """Get step trace info."""
        file_name = 'step_trace_raw_{}_detail_time.csv'.format(rank_id)
        step_trace_file_path = \
            os.path.join(self._target_dir_path, file_name)
        step_trace_file_path = validate_and_normalize_path(
            step_trace_file_path, raise_key="Invalid step trace file path.")
        if not os.path.exists(step_trace_file_path):
            log.error('Did not find the file: %s', step_trace_file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the file:{}'.format(step_trace_file_path))

        with open(step_trace_file_path, 'r') as src_file:
            lines = src_file.readlines()
            # when the step_num value is 0, it means the average value.
            # The last line of the step_trace_raw_{}_detail_time.csv records the average value.
            if step_num == 0:
                step_trace_info = lines[-1].strip('\n').split(',')
            else:
                step_trace_info = lines[step_num].strip('\n').split(',')
        # step_trace_info[6]: iteration_interval time
        # step_trace_info[7]: fp_and_bp time
        # step_trace_info[8]: tail time
        # divided by 1e5, the unit becomes a millisecond
        iteration_interval = float(step_trace_info[6])/1e5
        fp_and_bp = float(step_trace_info[7])/1e5
        tail = float(step_trace_info[8])/1e5
        step_trace_info = [iteration_interval, fp_and_bp, tail]
        return step_trace_info

    def _get_cluster_step_bottleneck_info(self, step_num, stage_id):
        """Get cluster step bottleneck info."""
        cluster_step_bottleneck_info = []
        for rank_id in self._cluster_rank_ids:
            cur_stage_id = int(int(rank_id) / int((self._rank_size / self._stage_num))) + 1
            # If stage_id is 0 (default value), display all data.
            if stage_id not in (0, cur_stage_id):
                continue
            step_bottleneck_info = self._get_step_bottleneck_info(rank_id, step_num)
            step_bottleneck_info.append(rank_id)
            cluster_step_bottleneck_info.append(step_bottleneck_info)
        self._cluster_info_size = len(cluster_step_bottleneck_info)
        return cluster_step_bottleneck_info

    def _get_step_bottleneck_info(self, rank_id, step_num):
        """Get cluster analyse info."""
        file_name = f'ascend_cluster_analyse_{self._parallel_mode}_{self._stage_num}_{self._rank_size}_{rank_id}.csv'
        step_bottleneck_file_path = \
            os.path.join(self._target_dir_path, file_name)
        step_bottleneck_file_path = validate_and_normalize_path(
            step_bottleneck_file_path, raise_key="Invalid step trace file path.")
        if not os.path.exists(step_bottleneck_file_path):
            log.error('Did not find the file: %s', step_bottleneck_file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the file:{}'.format(step_bottleneck_file_path))

        with open(step_bottleneck_file_path, 'r') as src_file:
            lines = src_file.readlines()
            # when the step_num value is 0, it means the average value.
            # The last line of the ascend_cluster_analyse_xxx.csv records the average value.
            if step_num == 0:
                step_bottleneck_info = lines[-1].strip('\n').split(',')
            else:
                step_bottleneck_info = lines[step_num].strip('\n').split(',')

        step_trace_info = self._get_step_trace_info(rank_id, step_num)
        # Insert the step iteration_interval time into the cluster_bottleneck_info
        step_bottleneck_info.insert(0, str(step_trace_info[0]))
        step_bottleneck_info = list(map(float, step_bottleneck_info))

        return step_bottleneck_info

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.

                - step_id (int): The selected  step id.
        """

        step_id = int(filter_condition.get("step_id", 0))
        stage_id = int(filter_condition.get("stage_id", 0))
        if self._parallel_mode == "data-parallel":
            self._result = self._get_cluster_step_trace_info(step_id)
        else:
            self._result = self._get_cluster_step_bottleneck_info(step_id, stage_id)

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        result = list()
        # item[:-1] info depends on parallel mode, item[-1]:rank_id
        for item in self._result:
            info = dict()
            if self._parallel_mode == "data-parallel":
                info["step_trace_info"] = item[:-1]
            else:
                info["step_bottleneck_info"] = item[:-1]
            info["rank_id"] = item[-1]
            info["profiler_dir"] = 'profiler'
            result.append(info)

        return {
            'total_step_num': self._total_step_num,
            'stage_num': self._stage_num,
            'info': result,
            'size': self._cluster_info_size,
            'parallel-mode': self._parallel_mode
        }


class ClusterMemoryAnalyser(ClusterAnalyser):
    """The analyser for analyzing the cluster memory usage."""
    _summary_filename = 'memory_usage_summary_{}.json'

    def __init__(self, cluster_profiler_dir, device_id='0'):
        super().__init__(cluster_profiler_dir, device_id)

    def get_peak_memory(self):
        """Get peak memory for each device."""
        peak_mem_list = []

        for rank_id in self._cluster_rank_ids:
            file_path = self._get_memory_file_for_each_device(self._target_dir_path, rank_id)
            file_content = self._get_file_content(file_path)
            capacity = file_content.get('capacity')
            peak_mem = file_content.get('peak_mem')

            mem_dict = {
                'rank_id': rank_id,
                'capacity': capacity,
                'peak_mem': peak_mem
            }
            peak_mem_list.append(mem_dict)

        return peak_mem_list

    def _get_memory_file_for_each_device(self, path, device_id):
        """Get memory file for each device."""
        filename = self._summary_filename.format(device_id)
        file_path = os.path.join(path, filename)
        validate_and_normalize_path(
            file_path, raise_key='Invalid memory usage file path.'
        )

        return file_path

    @staticmethod
    def _get_file_content(file_path):
        """Get file content."""
        try:
            with open(file_path, 'r') as f_obj:
                file_content = json.load(f_obj)
        except (IOError, OSError, json.JSONDecodeError) as err:
            log.error('Error occurred when read memory file: %s', err)
            raise ProfilerIOException()

        return file_content


class ClusterFlopsAnalyser(ClusterAnalyser):
    """The analyser for analyzing the cluster flops."""
    _summary_filename = 'flops_summary_{}.json'

    def __init__(self, cluster_profiler_dir, device_id='0'):
        super().__init__(cluster_profiler_dir, device_id)

    def get_flops(self):
        """Get flops for each device."""
        flops_info_list = []
        max_flops = 0

        for rank_id in self._cluster_rank_ids:
            file_path = self._get_flops_file_for_each_device(self._target_dir_path, rank_id)

            # Forward compatible. If flops file do not exist, return empty data.
            if not os.path.exists(file_path):
                flops_info_list = []
                break

            file_content = self._get_file_content(file_path)
            max_flops = max(max_flops, file_content.get('FLOPs'))

            flops_dict = {
                'rank_id': rank_id
            }
            flops_dict.update(file_content)
            flops_info_list.append(flops_dict)

        # Normalize the flops by divide the max flops in all device.
        for flops_info in flops_info_list:
            flops_info['FLOPs_norm'] = flops_info['FLOPs'] / max_flops

        return flops_info_list

    def _get_flops_file_for_each_device(self, path, device_id):
        """Get memory file for each device."""
        filename = self._summary_filename.format(device_id)
        file_path = os.path.join(path, filename)
        validate_and_normalize_path(
            file_path, raise_key='Invalid flops file path.'
        )

        return file_path

    @staticmethod
    def _get_file_content(file_path):
        """Get file content."""
        try:
            with open(file_path, 'r') as f_obj:
                file_content = json.load(f_obj)
        except (IOError, OSError, json.JSONDecodeError) as err:
            log.error('Error occurred when read flops file: %s', err)
            raise ProfilerIOException()

        return file_content


class ClusterHcclAnalyser(ClusterAnalyser):
    """The analyser for analyzing the cluster communication info."""
    _col_names = ['step_num', 'communication_cost', 'wait_cost']

    def __init__(self, cluster_profiler_dir, device_id):
        super().__init__(cluster_profiler_dir, device_id)
        self._none_sort_col_names = []
        self._total_step_num = self._get_total_step_num()

    def get_cluster_link_info(self, condition=None):
        """Get cluster link info."""
        self._col_names = ["src_dst", "link_type", "communication_cost", "communication_size", "band_width"]
        if condition is None:
            condition = {}
        filter_condition = condition.get('filter_condition', {})
        sort_condition = condition.get('sort_condition')
        group_condition = condition.get('group_condition')
        self._analyser_cluster_link_info(filter_condition)
        self._filter_cluster_link_info(filter_condition)
        if sort_condition:
            self._sort(sort_condition)
        if group_condition:
            self._group(group_condition)

        return {
            'cluster_link_info': self._result,
            'size': self._cluster_link_info_size
        }

    def _get_total_step_num(self):
        """Get the num of train step."""
        total_step_num = 0
        # Take the data of one of the device to get the total number of steps.

        entries = os.scandir(self._target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.startswith('hccl_raw'):
                file_path = os.path.join(self._target_dir_path, entry.name)
                with open(file_path, 'r') as src_file:
                    lines = src_file.readlines()
                # The first row is col_name, the last row is the average.
                if len(lines) > 2:
                    total_step_num = len(lines)-2
                break
        return total_step_num

    def _filter_cluster_link_info(self, filter_condition):
        """Filter cluster link info."""
        src_rank = filter_condition.get("src_rank", ".*")
        dst_rank = filter_condition.get("dst_rank", ".*")
        src_dst = src_rank + '-' + dst_rank
        src_dst_regex = '^' + src_dst + '$'
        link_type = filter_condition.get("link_type", ".")
        if src_rank == ".*" and dst_rank == ".*" and link_type == ".":
            self._cluster_link_info_size = len(self._result)
            return

        def inner_filter(item: list):
            # index0:src_dst_rank_id, index1:link type
            src_dst_pattern = re.match(src_dst_regex, item[0])
            link_type_pattern = re.match(link_type, item[1])
            if src_dst_pattern and link_type_pattern:
                return True
            return False
        self._result = list(filter(inner_filter, self._result))
        self._cluster_link_info_size = len(self._result)

    def _analyser_cluster_link_info(self, filter_condition):
        """Get cluster link info."""
        link_info = []
        step_id = filter_condition.get("step_id", 0)
        cluster_communication_info = self._get_cluster_communication_info(step_id)
        # index3:link_info
        cluster_link_info = [i[3] for i in cluster_communication_info]
        for item in cluster_link_info:
            for src_dst_key, src_dst_value in item.items():
                for link_type_key, link_type_value in src_dst_value.items():
                    # index0:communication_cost,index1:communication_size,communication_brand_width
                    link_info.append([src_dst_key, link_type_key, link_type_value[0],
                                      link_type_value[1], link_type_value[2]])

        self._result = link_info

    def _get_cluster_communication_info(self, step_num):
        """Get cluster communication info."""
        cluster_communication_info = list()
        for item in self._cluster_rank_ids:
            communication_info = self._get_communication_info(item, step_num)
            communication_info.append(item)
            cluster_communication_info.append(communication_info)
        self._cluster_communication_info_size = len(cluster_communication_info)

        return cluster_communication_info

    def _get_communication_info(self, device_id, step_num):
        """Get step trace info."""
        file_name = 'hccl_raw_{}.csv'.format(device_id)
        communication_file_path = \
            os.path.join(self._target_dir_path, file_name)
        communication_file_path = validate_and_normalize_path(
            communication_file_path, raise_key="Invalid  communication file path.")
        if not os.path.exists(communication_file_path):
            log.error('Did not find the file: %s', communication_file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the file:{}'.format(communication_file_path))
        communication_info = list()
        step_num = str(step_num)
        with open(communication_file_path, 'r') as src_file:
            csv_reader = csv.reader(src_file)
            # when the step_num value is 0, it means the average value.
            # The last line of the step_trace_raw_{}_detail_time.csv records the average value.
            # The first element of the last line is '-'.
            step_num = '-' if step_num == '0' else step_num
            for row in csv_reader:
                if row[0] == step_num:
                    communication_info = row
                    break
        # Convert string to floating point and dictionary
        if communication_info:
            communication_info[1] = float(communication_info[1])
            communication_info[2] = float(communication_info[2])
            communication_info[3] = json.loads(communication_info[3])
        # Judge whether the communication operator information is recorded.
        # If recorded, the length of communication_info is 5.
        if len(communication_info) > 4:
            communication_info[4] = json.loads(communication_info[4])

        return communication_info

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.

                - step_id (int): The selected step id.
        """

        step_id = filter_condition.get("step_id", 0)
        self._result = self._get_cluster_communication_info(step_id)

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        result = list()
        # item[0]:step_num, item[1]:communication_cost, item[2]:wait_cost, item[3]:link_info,
        # item[4]:communication_operator_cost, item[5]:rank_id
        for item in self._result:
            communication_info = dict()
            communication_info["communication_info"] = item[1:5]
            communication_info["rank_id"] = item[5]
            result.append(communication_info)

        return {
            'total_step_num': self._total_step_num,
            'communication': result,
            'size': self._cluster_communication_info_size
        }
