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
"""Op compute time files parser."""
from tabulate import tabulate
from mindinsight.profiler.common._utils import fwrite_format

class OPComputeTimeParser:
    """
    Join hwts info and framework info, get op time info, and output to the result file.

    Args:
         hwts_output_file (str): The file path of hwts_output_file. Such as: './output_format_data_hwts_0.txt".
         output_filename (str): The output data file path and name. Such as: './output_op_compute_time_0.txt'.
         op_task_info (dict): The task and op relation info. The format: {task_id, [opname, stream_id, block dim]}.
    """

    _dst_file_title = 'title:op compute time'
    _dst_file_column_title = ['op_name', 'compute_time(ms)', 'stream_id']

    def __init__(self, hwts_output_file, output_filename, op_task_info):
        self._hwts_output_file = hwts_output_file
        self._output_filename = output_filename
        self._op_task_info = op_task_info

    def _get_op_task_id_map(self):
        """
        Read hwts data file, get the task time info.

        Returns:
           list: all hwts task time info.
        """

        op_map_result = []
        hwts_list = []
        with(open(self._hwts_output_file, 'r')) as data_file:
            lines = data_file.readlines()
            for line in lines:
                if line.startswith("Start of task"):
                    line_split = line.split()
                    hwts_list.append([line_split[0], line_split[6], line_split[7], line_split[8]])
                if line.startswith('End of task'):
                    line_split = line.split()
                    hwts_list.append([line_split[0], line_split[6], line_split[7], line_split[8]])

        # hwts op map by taskId
        for hwts in hwts_list:
            if hwts[1] in self._op_task_info.keys():
                op_map_result.append([self._op_task_info[hwts[1]], hwts[0], hwts[1], hwts[2], hwts[3]])

        return op_map_result

    def execute(self):
        """Execute the parser, compute all op, get op time, and write it to the output file."""

        result_data = []
        tmp_result_data = []
        op_map_list = self._get_op_task_id_map()

        cur_index = 0
        length = len(op_map_list)

        while cur_index < length:
            if cur_index + 1 == length:
                break
            op_start = op_map_list[cur_index]
            op_end = op_map_list[cur_index+1]

            if op_start[1] == "Start" and op_end[1] == "End"\
                and op_start[0] == op_end[0]:
                # op_name, task_id, cycle counter, stream_id
                tmp_result_data.append([op_start[0], op_start[2], int(op_end[3]) - int(op_start[3]), op_start[4]])
                cur_index += 2
            else:
                cur_index += 1

        op_name_time_dict = {}
        op_name_steamid_dict = {}
        op_name_count_dict = {}
        op_name_task_dict = {}

        # compute all op
        for item in tmp_result_data:
            if item[0] in op_name_time_dict.keys():
                op_name_time_dict[item[0]] += float(item[2])/1e5  # cycle counter/1*10^5 ms
                if item[1] == op_name_task_dict[item[0]]:
                    op_name_count_dict[item[0]] += 1

            else:
                op_name_time_dict[item[0]] = float(item[2])/1e5
                op_name_steamid_dict[item[0]] = item[-1]
                op_name_task_dict[item[0]] = item[1]
                op_name_count_dict[item[0]] = 1

        for op_name, time in op_name_time_dict.items():
            if op_name in op_name_steamid_dict.keys():
                stream_id = op_name_steamid_dict[op_name]
                avg_time = time / op_name_count_dict[op_name]
                result_data.append([op_name, avg_time, stream_id])

        result_data.sort(key=lambda x: x[0])
        total_time = 0
        for item in result_data:
            total_time += item[1]
        result_data.append(["total op", total_time, 0])

        fwrite_format(self._output_filename, data_source=self._dst_file_title, is_start=True)
        fwrite_format(self._output_filename, data_source=tabulate(result_data,
                                                                  self._dst_file_column_title,
                                                                  tablefmt='simple'))
