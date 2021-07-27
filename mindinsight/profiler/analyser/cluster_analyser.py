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
    _host_ips_mapping_filename = 'host_ips_mapping.txt'

    def __init__(self, cluster_profiler_dir, device_id):
        super().__init__(cluster_profiler_dir, device_id)
        self._cluster_profiler_dir = cluster_profiler_dir
        self._host_ips_mapping_info = self._get_host_ips_mapping_info()
        self._host_ips_dir = self._get_host_ips_dir()
        self._host_device_rank_relation = self._get_host_device_rank_relation()

    def _get_host_ips_mapping_info(self):
        """Get host ips mapping info."""
        host_ips_mapping_info = list()
        file_path = os.path.join(self._cluster_profiler_dir, self._host_ips_mapping_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid file path.")
        if not os.path.exists(file_path):
            log.error('Did not find host_ips_mapping file: %s', file_path)
            raise ProfilerDirNotFoundException(msg='Did not find host_ips_mapping:{}'.format(file_path))

        with open(file_path, 'r') as src_file:
            for line in src_file.readlines():
                mapping_info = line.split()
                if len(mapping_info) > 1:
                    # mapping_info[0]:host_ip, mapping_info[1]:host_mapping_ip
                    host_ips_mapping_info.append([mapping_info[0], mapping_info[1]])

        return host_ips_mapping_info

    def _get_host_ips_dir(self):
        """Get host ips dir."""
        host_ips_dir = []
        target_dir_path = os.path.join(self._cluster_profiler_dir, 'cluster_profiler')
        target_dir_path = validate_and_normalize_path(
            target_dir_path, raise_key="Invalid cluster_profiler dir path.")
        if not os.path.exists(target_dir_path):
            log.error('Did not find cluster_profiler dir : %s', target_dir_path)
            raise ProfilerDirNotFoundException(msg='Did not find cluster_profiler dir:{}'.format(target_dir_path))

        entries = os.scandir(target_dir_path)
        # host_mapping_id_index:1
        host_mapping_ips = [i[1] for i in self._host_ips_mapping_info]
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in host_mapping_ips:
                    host_ips_dir.append(entry.name)
        return host_ips_dir

    def _get_host_device_rank_relation(self):
        """Get host_ip device_id rank_id relation."""
        rank_table_file_path = self._get_rank_table_file_path()
        if not os.path.exists(rank_table_file_path):
            log.error('Did not find rank table file under %s', self._cluster_profiler_dir)
            raise ProfilerFileNotFoundException(msg='Did not find rank table file')
        with open(rank_table_file_path, 'r', encoding='utf-8') as file:
            try:
                relation_info = json.load(file)
            except json.JSONDecodeError as err:
                log.exception(err)
        host_device_rank_relation = list()
        servers_info = relation_info.get("server_list")
        for server_info in servers_info:
            server_id = server_info.get("server_id")
            devices_info = server_info.get("device")
            for device_info in devices_info:
                device_id = device_info.get("device_id")
                rank_id = device_info.get("rank_id")
                host_device_rank_relation.append([server_id, device_id, rank_id])

        host_ips_mapping_info = self._get_host_ips_mapping_info()
        for item in host_device_rank_relation:
            # host_ip_index:0,host_mapping_id_index:1
            target_info = [i for i in host_ips_mapping_info if item[0] == i[0]]
            # target_info is like:[[host_ip, host_mapping_ip]]
            item[0] = target_info[0][1]

        return host_device_rank_relation

    def _get_rank_table_file_path(self):
        """Get rank table file path."""
        file_path = ''
        target_dir_path = self._cluster_profiler_dir
        entries = os.scandir(target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.endswith('.json'):
                file_path = os.path.join(target_dir_path, entry.name)
                break
        return file_path

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
    _col_names = ['iteration_interval', 'fp_and_bp', 'tail']

    def __init__(self, cluster_profiler_dir, device_id):
        super().__init__(cluster_profiler_dir, device_id)
        self._none_sort_col_names = []
        self._total_step_num = self._get_total_step_num()

    def _get_total_step_num(self):
        """Get the num of train step."""
        total_step_num = 0
        # take the data of one of the machines to get the total number of steps.
        host_ip_dir = self._host_ips_dir[0]
        target_dir_path = os.path.join(self._cluster_profiler_dir, 'cluster_profiler', host_ip_dir, 'profiler')
        target_dir_path = validate_and_normalize_path(
            target_dir_path, raise_key="Invalid profiler dir path.")
        if not os.path.exists(target_dir_path):
            log.error('Did not find cluster_profiler dir : %s', target_dir_path)
            raise ProfilerDirNotFoundException(msg='Did not find cluster_profiler dir:{}'.format(target_dir_path))

        entries = os.scandir(target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.startswith('step_trace_raw'):
                file_path = os.path.join(target_dir_path, entry.name)
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
        for item in self._host_device_rank_relation:
            # item[0]:host_ip, item[1]:device_id, item[2]:rank_id
            step_trace_info = self._get_step_trace_info(item[0], item[1], step_num)
            step_trace_info.append(item[0])
            step_trace_info.append(item[1])
            step_trace_info.append(item[2])
            cluster_step_trace_info.append(step_trace_info)
        self._cluster_step_trace_info_size = len(cluster_step_trace_info)
        return cluster_step_trace_info

    def _get_step_trace_info(self, host_ip, device_id, step_num):
        """Get step trace info."""
        file_name = 'step_trace_raw_{}_detail_time.csv'.format(device_id)
        step_trace_file_path = \
            os.path.join(self._cluster_profiler_dir, 'cluster_profiler', host_ip, 'profiler', file_name)
        step_trace_file_path = validate_and_normalize_path(
            step_trace_file_path, raise_key="Invalid step trace file path.")
        if not os.path.exists(step_trace_file_path):
            log.error('Did not find the file: %s', step_trace_file_path)
            raise ProfilerFileNotFoundException(msg='Did not find the file:{}'.format(step_trace_file_path))
        step_trace_info = list()
        step_num = str(step_num)
        with open(step_trace_file_path, 'r') as src_file:
            lines = src_file.readlines()
            # when the step_num value is 0, it means the average value.
            # The last line of the step_trace_raw_{}_detail_time.csv records the average value.
            if step_num == '0':
                step_trace_info = lines[-1].strip('\n').split(',')
            else:
                for line in lines:
                    line = line.strip('\n').split(',')
                    if line[0] == step_num:
                        step_trace_info = line
        # step_trace_info[6]: iteration_interval time
        # step_trace_info[7]: fp_and_bp time
        # step_trace_info[8]: tail time
        # divided by 1e5, the unit becomes a millisecond
        iteration_interval = float(step_trace_info[6])/1e5
        fp_and_bp = float(step_trace_info[7])/1e5
        tail = float(step_trace_info[8])/1e5
        step_trace_info = [iteration_interval, fp_and_bp, tail]
        return step_trace_info

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.

                - step_id (int): The selected  step id.
        """

        step_id = filter_condition.get("step_id", 0)
        self._result = self._get_cluster_step_trace_info(step_id)

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        result = list()
        # item[0]:iteration_interval, item[1]:fp_and_bp, item[2]:tail
        # item[4]:host_ip, item[5]:device_id, item[6]:rank_id
        for item in self._result:
            step_trace_info = dict()
            step_trace_info["step_trace_info"] = item[0:3]
            step_trace_info["host_ip"] = item[3]
            step_trace_info["device_id"] = item[4]
            step_trace_info["rank_id"] = item[5]
            step_trace_info["profiler_dir"] = 'profiler'
            result.append(step_trace_info)

        return {
            'total_step_num': self._total_step_num,
            'step_trace': result,
            'size': self._cluster_step_trace_info_size
        }


class ClusterMemoryAnalyser(ClusterAnalyser):
    """The analyser for analyzing the cluster memory usage."""
    _summary_filename = 'memory_usage_summary_{}.json'

    def __init__(self, cluster_profiler_dir, device_id='0'):
        super().__init__(cluster_profiler_dir, device_id)
        self._cluster_dir = os.path.join(cluster_profiler_dir, 'cluster_profiler')

    def get_peak_memory(self):
        """Get peak memory for each device."""
        peak_mem_list = []

        for host_map_ip, device_id, rank_id in self._host_device_rank_relation:
            host_dir = os.path.join(self._cluster_dir, host_map_ip, 'profiler')
            validate_and_normalize_path(host_dir, raise_key='Invalid host directory {}.'.format(host_map_ip))
            file_path = self._get_memory_file_for_each_device(host_dir, device_id)
            file_content = self._get_file_content(file_path)
            capacity = file_content.get('capacity')
            peak_mem = file_content.get('peak_mem')

            mem_dict = {
                'host_ip': host_map_ip,
                'device_id': device_id,
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
        self._cluster_dir = os.path.join(cluster_profiler_dir, 'cluster_profiler')

    def get_flops(self):
        """Get flops for each device."""
        flops_info_list = []
        max_flops = 0

        for host_map_ip, device_id, rank_id in self._host_device_rank_relation:
            host_dir = os.path.join(self._cluster_dir, host_map_ip, 'profiler')
            validate_and_normalize_path(host_dir, raise_key='Invalid host directory {}.'.format(host_map_ip))
            file_path = self._get_flops_file_for_each_device(host_dir, device_id)

            # Forward compatible. If flops file do not exist, return empty data.
            if not os.path.exists(file_path):
                flops_info_list = []
                break

            file_content = self._get_file_content(file_path)
            max_flops = max(max_flops, file_content.get('FLOPs'))

            flops_dict = {
                'host_ip': host_map_ip,
                'device_id': device_id,
                'rank_id': rank_id,
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
        # Take the data of one of the machines to get the total number of steps.
        host_ip_dir = self._host_ips_dir[0]
        target_dir_path = os.path.join(self._cluster_profiler_dir, 'cluster_profiler', host_ip_dir, 'profiler')
        target_dir_path = validate_and_normalize_path(
            target_dir_path, raise_key="Invalid profiler dir path.")
        if not os.path.exists(target_dir_path):
            log.error('Did not find cluster_profiler dir : %s', target_dir_path)
            raise ProfilerDirNotFoundException(msg='Did not find cluster_profiler dir:{}'.format(target_dir_path))

        entries = os.scandir(target_dir_path)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_file() and entry.name.startswith('hccl_raw'):
                file_path = os.path.join(target_dir_path, entry.name)
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
        for item in self._host_device_rank_relation:
            # item[0]:host_ip, item[1]:device_id, item[2]:rank_id
            communication_info = self._get_communication_info(item[0], item[1], step_num)
            communication_info.append(item[0])
            communication_info.append(item[1])
            communication_info.append(item[2])
            cluster_communication_info.append(communication_info)
        self._cluster_communication_info_size = len(cluster_communication_info)

        return cluster_communication_info

    def _get_communication_info(self, host_ip, device_id, step_num):
        """Get step trace info."""
        file_name = 'hccl_raw_{}.csv'.format(device_id)
        communication_file_path = \
            os.path.join(self._cluster_profiler_dir, 'cluster_profiler', host_ip, 'profiler', file_name)
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
        # item[4]:communication_operator_cost, item[5]:host_ip, item[6]:device_id, item[7]:rank_id,
        for item in self._result:
            communication_info = dict()
            communication_info["communication_info"] = item[1:5]
            communication_info["host_ip"] = item[5]
            communication_info["device_id"] = item[6]
            communication_info["rank_id"] = item[7]
            result.append(communication_info)

        return {
            'total_step_num': self._total_step_num,
            'communication': result,
            'size': self._cluster_communication_info_size
        }
