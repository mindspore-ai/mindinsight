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
"""
Parser for AI CPU preprocess data.
"""

from mindinsight.profiler.common._utils import fwrite_format, get_file_join_name
from tabulate import tabulate

_source_file_target = 'DATA_PREPROCESS.dev.AICPU'
_dst_file_title = 'title:DATA_PREPROCESS AICPU'
_dst_file_column_title = ['serial_number', 'node_name', 'total_time(us)', 'dispatch_time(us)',
                          'RunV2_start', 'compute_start', 'memcpy_start', 'memcpy_end', 'RunV2_end']


class DataPreProcessParser:
    """
    The Parser for AI CPU preprocess data.

    Args:
         input_path(str): The profiling job path.
         output_filename(str): The output data path and name.

    """

    def __init__(self, input_path, output_filename):
        self._input_path = input_path
        self._output_filename = output_filename
        self._source_file_name = self._get_source_file()

    def _get_source_file(self):
        """get log file name, which was created by ada service"""

        return get_file_join_name(self._input_path, _source_file_target)

    def execute(self):
        """execute the parser, get result data, and write it to the output file"""
        ai_cpu_lines = list()
        with open(self._source_file_name, 'rb') as ai_cpu_data:
            ai_cpu_str = str(ai_cpu_data.read().replace(b'\n\x00', b' ___ ')
                             .replace(b'\x00', b' ___ '))[2:-1]
            ai_cpu_lines = ai_cpu_str.split(" ___ ")
        create_session_cnt = 0
        for line in ai_cpu_lines:
            if "Create session start" in line:
                create_session_cnt += 1
        start_idx = create_session_cnt * 2
        ai_cpu_lines = ai_cpu_lines[start_idx:-3]
        node_list = list()
        ai_cpu_total_time_summary = 0

        if start_idx > 0:
            serial_number = 1
            for line in ai_cpu_lines:
                if "Node" in line:
                    node_name = line.split(',')[0].split(':')[-1]
                    run_v2_start = line.split(',')[1].split(':')[-1]
                    compute_start = line.split(',')[2].split(':')[-1]
                    mercy_start = line.split(',')[3].split(':')[-1]
                    mercy_end = line.split(',')[4].split(':')[-1]
                    run_v2_end = line.split(',')[5].split(':')[-1]
                    node_data = [serial_number, node_name, run_v2_start, compute_start,
                                 mercy_start, mercy_end, run_v2_end]
                    node_list.append(node_data)
                    serial_number += 1
                elif "Thread" in line:
                    # total_time and dispatch_time joins node list
                    total_time = line.split(',')[-1].split('=')[-1].split()[0]
                    dispatch_time = line.split(',')[-2].split('=')[-1].split()[0]
                    if node_list:
                        node_list[-1][2:2] = [total_time, dispatch_time]
                        ai_cpu_total_time_summary += int(total_time)
            node_list.append(["AI CPU Total Time:", ai_cpu_total_time_summary])

            if node_list:
                fwrite_format(self._output_filename, data_source=_dst_file_title, is_print=True,
                              is_start=True)
                fwrite_format(self._output_filename,
                              data_source=tabulate(node_list, _dst_file_column_title,
                                                   tablefmt='simple'),
                              is_start=True, is_print=True)
