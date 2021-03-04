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

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException, \
    ProfilerDirNotFoundException
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
