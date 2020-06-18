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
The parser for AI CPU preprocess data.
"""
import os

from tabulate import tabulate

from mindinsight.profiler.common._utils import fwrite_format, get_file_join_name
from mindinsight.profiler.common.log import logger


class DataPreProcessParser:
    """
    The Parser for AI CPU preprocess data.

    Args:
         input_path(str): The profiling job path.
         output_filename(str): The output data path and name.

    """

    _source_file_target = 'DATA_PREPROCESS.dev.AICPU.'
    _dst_file_title = 'title:DATA_PREPROCESS AICPU'
    _dst_file_column_title = ['serial_number', 'node_type_name', 'total_time(us)',
                              'dispatch_time(us)', 'run_start', 'run_end']

    def __init__(self, input_path, output_filename):
        self._input_path = input_path
        self._output_filename = output_filename
        self._source_file_name = self.get_source_file()

    def get_source_file(self):
        """Get log file name, which was created by ada service."""
        file_name = get_file_join_name(self._input_path, self._source_file_target)
        if not file_name:
            data_path = os.path.join(self._input_path, "data")
            file_name = get_file_join_name(data_path, self._source_file_target)
        return file_name

    def execute(self):
        """Execute the parser, get result data, and write it to the output file."""

        if not os.path.exists(self._source_file_name):
            logger.info("Did not find the aicpu profiling source file")
            return

        with open(self._source_file_name, 'rb') as ai_cpu_data:
            ai_cpu_str = str(ai_cpu_data.read().replace(b'\n\x00', b' ___ ')
                             .replace(b'\x00', b' ___ '))[2:-1]
            ai_cpu_lines = ai_cpu_str.split(" ___ ")

        node_list = list()
        ai_cpu_total_time_summary = 0
        # Node serial number.
        serial_number = 1
        for i in range(len(ai_cpu_lines) - 1):
            node_line = ai_cpu_lines[i]
            thread_line = ai_cpu_lines[i + 1]
            if "Node" in node_line and "Thread" in thread_line:
                # Get the node data from node_line
                node_type_name = node_line.split(',')[0].split(':')[-1]
                run_start = node_line.split(',')[1].split(':')[-1]
                run_end = node_line.split(',')[2].split(':')[-1]
                total_time = thread_line.split(',')[-1].split('=')[-1].split()[0]
                dispatch_time = thread_line.split(',')[-2].split('=')[-1].split()[0]
                node_list.append([serial_number, node_type_name, total_time,
                                  dispatch_time, run_start, run_end])
                # Calculate the total time.
                ai_cpu_total_time_summary += int(total_time)
                # Increase node serial number.
                serial_number += 1
            elif "Node" in node_line and "Thread" not in thread_line:
                node_type_name = node_line.split(',')[0].split(':')[-1]
                logger.warning("The node type:%s cannot find thread data", node_type_name)

        if node_list:
            node_list.append(["AI CPU Total Time(us):", ai_cpu_total_time_summary])
            fwrite_format(self._output_filename, data_source=self._dst_file_title, is_print=True,
                          is_start=True)
            fwrite_format(self._output_filename,
                          data_source=tabulate(node_list, self._dst_file_column_title,
                                               tablefmt='simple'),
                          is_start=True, is_print=True)
