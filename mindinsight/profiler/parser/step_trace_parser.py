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
"""The parser for step trace data."""
import csv
import os
import stat
import struct
from collections import namedtuple
from decimal import Decimal

from mindinsight.profiler.common.exceptions.exceptions import ProfilerPathErrorException, \
    JobIdMismatchException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.util import get_summary_for_step_trace
from mindinsight.utils.exceptions import MindInsightException

StepTraceStruct = namedtuple(
    'TrainingTraceStruct', ['tag_id', 'task_id', 'stream_id', 'sys_count']
)


class StepTraceParser:
    """
    The parser for step trace data.

    Args:
        input_dir (str): The directory that contains original step trace data.
        output_file_path (str): The output file path.
        skip_first_step (bool): Whether skip the first step or not.
    """
    _event_size = 20

    def __init__(self, input_dir, output_file_path, job_id, skip_first_step=False):
        self._input_dir = input_dir
        self._output_path = output_file_path
        self._job_id = job_id
        self._skip_first_step = skip_first_step
        self._result = []
        self._header = []
        self._step_num = 0

    @property
    def output_file(self):
        """The property of step trace header."""
        file_name = self._output_path.rsplit('/', 2)
        return file_name[-1] if len(file_name) == 3 else ''

    def show(self):
        """The property of step trace info."""
        summary_info = {}
        if self._result:
            summary_info = get_summary_for_step_trace(self._result[-1], self._header)
            summary_info['total_steps'] = len(self._result) - 1
        print('\nStep trace summary info (unit: syscnt):')
        print(summary_info)
        print('\nThe step trace parse result saves under ${summary_dir}/profiler/%s'
              % self.output_file)

    def parse_and_save(self):
        """Parse step trace files and save the result."""
        try:
            source_file = self._get_step_trace_file()
            self._parse(source_file)
            self._save()
        except MindInsightException as err:
            log.error("Failed to parse and save step trace files.")
            log.exception(err)
        else:
            log.info("Finish to save intermediate result for step trace file.")

    def _get_step_trace_file(self):
        """Get step trace file."""
        profiling_path = self._input_dir
        # validate input_dir
        if not os.path.isdir(profiling_path):
            raise ProfilerPathErrorException(
                '{} does not exist or is not a dir'.format(profiling_path)
            )
        # get step trace files
        files = os.listdir(profiling_path)
        step_trace_files = list(
            filter(
                lambda file: file.startswith('training_trace') and not file.endswith('.done'),
                files
            )
        )
        # validate result
        if not step_trace_files:
            raise ProfilerPathErrorException('training trace file does not exist')
        if len(step_trace_files) > 1:
            log.warning("Not enable to parse multiple step trace files yet.")
        step_trace_file = os.path.join(profiling_path, step_trace_files[0])
        return step_trace_file

    def _parse(self, source_file):
        """Parse source step trace file."""
        log.info("Start to parse step  trace file.")
        with open(source_file, 'rb') as handler:
            content = handler.read()
            for step_trace in self._get_next_step_trace(content):
                if self._skip_first_step:
                    self._skip_first_step = False
                else:
                    self._record_trace_event(step_trace)
        self._record_average_info()
        log.info("Finish to parse step trace file.")

    def _get_next_step_trace(self, content):
        """
        Get next step trace info.

        Args:
            content (bytes): The input step trace info
        Returns:
            Generator, return the step trace one by one.
        """
        event_info = {}
        for pos in range(0, len(content), 20):
            next_event = self._get_trace_struct(content[pos:pos + self._event_size])
            self._construct_event_info(next_event, event_info)
            if event_info.get('end'):
                yield event_info

    def _get_trace_struct(self, bin_info):
        """Translate event info to StepTraceStruct."""
        if len(bin_info) == self._event_size:
            parsed_info = struct.unpack('=QHHQ', bin_info)
            return StepTraceStruct(*parsed_info)
        return None

    def _construct_event_info(self, next_event, event_info):
        """Construct event info according to next_event."""
        min_job_id = 255
        step_flag: bool = lambda tag: tag > min_job_id or tag == 0
        end_flag: bool = lambda tag: tag == min_job_id
        fp_flag: bool = lambda tag: tag == 1
        bp_flag: bool = lambda tag: tag == 2

        def _on_step_event():
            """Handle step event."""
            self._validate_tag_id(tag_id)
            start_time = event_info.get('end', '-')
            event_info.clear()
            event_info['start'] = start_time
            event_info['reduce'] = {}

        def _on_reduce_event():
            """Handle reduce event."""
            stream_id = next_event.stream_id
            if event_info['reduce'].get(stream_id):
                event_info['reduce'][stream_id].append(sys_count)
            else:
                event_info['reduce'][stream_id] = [sys_count]

        tag_id = next_event.tag_id
        sys_count = next_event.sys_count
        if end_flag(tag_id):
            event_info['end'] = sys_count
        elif step_flag(tag_id):
            _on_step_event()
        elif fp_flag(tag_id):
            event_info['fp'] = sys_count
        elif bp_flag(tag_id):
            event_info['bp'] = sys_count
        else:
            _on_reduce_event()

    def _validate_tag_id(self, job_id):
        """Check the job id in source step trace file is same os user set."""
        if not self._job_id:
            self._job_id = job_id
        elif self._job_id != job_id:
            raise JobIdMismatchException()

    def _record_trace_event(self, step_trace):
        """Record trace event."""
        self._step_num += 1
        start_time = step_trace.get('start')
        end_time = step_trace.get('end')
        fp_time = step_trace.get('fp')
        bp_time = step_trace.get('bp')
        if not (start_time and end_time and fp_time and bp_time):
            log.warning("The step %d is missing basic time.", self._step_num)
            return
        if start_time == '-':
            start_time = fp_time
        row_data = {
            'step_num': self._step_num,
            'start_point': start_time,
            'end_point': end_time,
            'total': end_time - start_time,
            'fp_point': fp_time,
            'bp_point': bp_time,
            'iteration_interval': fp_time - start_time,
            'fp_and_bp': bp_time - fp_time,
            'tail': end_time - bp_time
        }
        # update reduce info
        self._update_reduce_info(step_trace, row_data)
        # save the row data
        if not self._header:
            self._header = list(row_data.keys())
        row_data_list = [row_data.get(header_name, 0) for header_name in self._header]
        self._result.append(row_data_list)

    @staticmethod
    def _update_reduce_info(step_trace, row_data):
        """Extract reduce info."""
        reduce_time = step_trace.get('reduce', {})
        for stream_id, time_points in reduce_time.items():
            time_point_num = len(time_points)
            if time_point_num % 2:
                log.warning("Stream %d has %d reduce time points.", stream_id, time_point_num)
                continue
            for index, point_id in enumerate(range(0, time_point_num, 2)):
                field_name = f'stream_{stream_id}_parallel_{index}'
                row_data[field_name + '_start_point'] = time_points[point_id]
                row_data[field_name + '_end_point'] = time_points[point_id + 1]
                row_data[field_name] = time_points[point_id + 1] - time_points[point_id]

    def _record_average_info(self):
        """Calculate average info."""
        result_size = len(self._result)
        # calculate average data for each column in result data
        average_data = [0] * len(self._header)
        if result_size >= 2:
            for row_info in self._result[1:]:
                average_data = [
                    Decimal(i) + Decimal(j) for i, j in zip(row_info, average_data)
                ]
            average_data = [
                round((item / (result_size - 1))) for item in average_data
            ]
            # change step num info in average_data to None
            step_num_index = self._header.index('step_num')
            average_data[step_num_index] = '-'
        self._result.append(average_data)
        log.info("Finish add average info for step trace.")

    def _save(self):
        log.info("Start to save step  trace file.")
        if not self._header:
            return
        with open(self._output_path, 'w') as file_handle:
            csv_writer = csv.writer(file_handle)
            csv_writer.writerow(self._header)
            for row_data in self._result:
                csv_writer.writerow(row_data)
        os.chmod(self._output_path, stat.S_IREAD | stat.S_IWRITE)
