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
"""The Timeline Analyser."""
import json
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.parser.container import TimelineContainer
from mindinsight.profiler.common.exceptions.exceptions import ProfilerFileNotFoundException, \
    ProfilerIOException
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


SIZE_LIMIT = 20 * 1024 * 1024  # 20MB


class TimelineAnalyser(BaseAnalyser):
    """
    Analyse timeline data from file.
    """
    __col_names__ = ['op_name', 'stream_id', 'start_time', 'duration']
    _output_timeline_data_file_path = 'output_timeline_data_{}.txt'
    _min_cycle_counter_file_path = 'min_cycle_counter_{}.txt'
    _timeline_filename = 'timeline_detail_{}.json'
    _display_filename = 'timeline_display_{}.json'
    _timeline_summary_filename = 'timeline_summary_{}.json'
    _timeline_meta = []
    _timeline_summary = {
        'total_time': 0,
        'num_of_streams': 0,
        'num_of_ops': 0,
        'op_exe_times': 0
    }

    def _load(self):
        """Load data according to the parsed profiling files."""
        self.load_timeline_data()
        self._timeline_summary['op_exe_times'] = len(self._timeline_meta)

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def get_display_timeline(self):
        """
        Get timeline data for UI display.

        Returns:
            json, the content of timeline data.
        """
        # Search timeline json file under profiling dir.
        timeline_filename = self._timeline_filename.format(self._device_id)
        display_filename = self._display_filename.format(self._device_id)
        file_list = [filename for filename in os.listdir(self._profiling_dir)
                     if timeline_filename in filename or display_filename in filename]

        # Check if there is a timeline json file for display
        file_path = os.path.join(self._profiling_dir, display_filename)
        if display_filename not in file_list:
            file_path = os.path.join(self._profiling_dir, timeline_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline json path.'
        )

        timeline = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    timeline = json.load(f_obj)
            except (IOError, OSError) as err:
                logger.error('Error occurred when read timeline display file: %s', err)
                raise ProfilerIOException
        else:
            logger.info('No timeline file. Please check the output path.')

        return timeline

    def get_timeline_summary(self):
        """
        Get timeline summary information for UI display.

        Returns:
            json, the content of timeline summary information.
        """
        file_path = None
        summary_file_name = 'timeline_summary_{}.json'.format(self._device_id)
        if summary_file_name in os.listdir(self._profiling_dir):
            file_path = os.path.join(self._profiling_dir, summary_file_name)

        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline summary path.'
        )

        timeline_summary = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    timeline_summary = json.load(f_obj)
            except (IOError, OSError) as err:
                logger.error('Error occurred when read timeline summary file: %s', err)
                raise ProfilerIOException

        return timeline_summary

    def write_timeline(self):
        """Load data according to the parsed profiling files."""
        # Write timeline to file.
        file_size = self.write_timeline_to_json()

        # If the file size is larger than 20MB, open a new file and
        # write the first 20MB content into it.
        if file_size > SIZE_LIMIT:
            logger.debug('File size is larger than 20MB, will be resized...')
            # write to json file for display
            self.write_timeline_to_json_by_limitation()

    def write_timeline_to_json(self):
        """Write timeline to json."""
        timeline_filename = self._timeline_filename.format(self._device_id)
        timeline_file_path = os.path.join(
            self._profiling_dir,
            timeline_filename
        )

        timeline_file_path = validate_and_normalize_path(
            timeline_file_path, raise_key='Invalid timeline json path.'
        )

        try:
            with open(timeline_file_path, 'w') as json_file:
                json.dump(self._timeline_meta, json_file)
            file_size = os.path.getsize(timeline_file_path)
        except (IOError, OSError) as err:
            logger.error('Error occurred when write timeline full details: %s', err)
            raise ProfilerIOException

        return file_size

    def write_timeline_to_json_by_limitation(self):
        """Write timeline to json by limitation."""
        display_filename = self._display_filename.format(self._device_id)
        display_file_path = os.path.join(
            self._profiling_dir,
            display_filename
        )

        display_file_path = validate_and_normalize_path(
            display_file_path, raise_key='Invalid timeline display json path.'
        )

        try:
            with open(display_file_path, 'w') as json_file:
                json_file.write('[')
                for item in self._timeline_meta:
                    json.dump(item, json_file)
                    file_size = os.path.getsize(display_file_path)
                    if file_size > SIZE_LIMIT:
                        break
                    json_file.write(',')
                json_file.write(']')
        except (IOError, OSError) as err:
            logger.error('Error occurred when write timeline display file: %s', err)
            raise ProfilerIOException

    def write_timeline_summary(self):
        """Write timeline summary to json."""
        timeline_summary_file_path = os.path.join(
            self._profiling_dir,
            self._timeline_summary_filename.format(self._device_id)
        )

        timeline_summary_file_path = validate_and_normalize_path(
            timeline_summary_file_path, raise_key='Invalid timeline summary path.'
        )

        try:
            with open(timeline_summary_file_path, 'w') as json_file:
                json.dump(self._timeline_summary, json_file)
        except (IOError, OSError) as err:
            logger.error('Error occurred when write timeline summary file: %s', err)
            raise ProfilerIOException

    def load_timeline_data(self):
        """Load timeline data from file."""
        file_path = os.path.join(
            self._profiling_dir,
            self._output_timeline_data_file_path.format(self._device_id)
        )
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline txt file path.'
        )
        if not os.path.exists(file_path):
            logger.error("Failed to find parsed timeline file.")
            raise ProfilerFileNotFoundException('parsed timeline file')

        stream_count_dict = {}
        try:
            with open(file_path, 'r') as f_obj:
                for line in f_obj:
                    if not line.startswith('op_name'):
                        line_list = line.strip('\n').split(',')
                        self._parse_timeline_data(line_list)
                        self._update_num_of_streams(line_list, stream_count_dict)
        except (IOError, OSError) as err:
            logger.error('Error occurred when read timeline intermediate file: %s', err)
            raise ProfilerIOException

        # Update timeline summary info
        self._timeline_summary['num_of_streams'] = len(stream_count_dict.keys())

    def _parse_timeline_data(self, line_list):
        """Parse timeline data."""
        factor = 1000
        op_meta = TimelineContainer(line_list)
        timeline_dict = {}
        timeline_dict['name'] = op_meta.op_name
        timeline_dict['ph'] = 'X'
        timeline_dict['pid'] = int(self._device_id)
        timeline_dict['tid'] = op_meta.stream_id
        timeline_dict['ts'] = op_meta.start_time * factor
        dur = op_meta.duration * factor
        timeline_dict['dur'] = dur
        self._timeline_summary['total_time'] += dur
        self._timeline_meta.append(timeline_dict)

    @staticmethod
    def _update_num_of_streams(line_list, stream_count_dict):
        """Update number of streams."""
        stream_id = line_list[1]
        if stream_id not in stream_count_dict.keys():
            stream_count_dict[stream_id] = 1
        else:
            stream_count_dict[stream_id] += 1

    def get_min_cycle_counter_from_file(self):
        """
        Get minimum cycle counter.

        Returns:
            float, the minimum value of the cycle counter.
        """
        file_path = os.path.join(
            self._profiling_dir,
            self._min_cycle_counter_file_path.format(self._device_id)
        )

        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid min cycle counter file path.'
        )

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    min_cycle_counter = f_obj.read()
                    min_cycle_counter = float(min_cycle_counter) \
                        if not min_cycle_counter == 'inf' else 0
            except (IOError, OSError) as err:
                logger.error('Error occurred when read minimum cycle counter: %s', err)
                raise ProfilerIOException
        else:
            min_cycle_counter = 0
            logger.info("No min cycle counter recorded.")

        return min_cycle_counter

    def add_all_reduce_info(self, all_reduce_info):
        """
        Add all reduce info into timeline metadata.

        Args:
            all_reduce_info (list<dict>): The metadata of AllReduce operator.
                [
                    {
                        'stream_id_1': [(start_time, end_time, duration, field_name)],
                        ...
                    },
                    {...}
                ]
        """
        logger.info('Adding AllReduce info...')
        factor = 100
        min_cycle_counter = self.get_min_cycle_counter_from_file()
        for step_meta in all_reduce_info:
            for stream_id, time_info_list in step_meta.items():
                for time_info in time_info_list:
                    start, _, dur, name = time_info
                    all_reduce_dict = {}
                    all_reduce_dict['name'] = name
                    all_reduce_dict['ph'] = 'X'
                    # Using 10000 to represent AllReduce
                    all_reduce_dict['pid'] = 10000
                    all_reduce_dict['tid'] = int(stream_id)
                    all_reduce_dict['ts'] = (start - min_cycle_counter) / factor
                    all_reduce_dict['dur'] = dur / factor
                    self._timeline_meta.append(all_reduce_dict)
                    self._timeline_summary['total_time'] += all_reduce_dict['dur']

    def add_framework_info(self, framework_info):
        """
        Add framework info into timeline metadata.

        Args:
            framework_info (dict): The framework metadata.
        """
        logger.info('Adding framework info...')
        framework_obj_list = framework_info.get('object')
        self._timeline_summary['num_of_ops'] = len(framework_obj_list)
        for framework_obj in framework_obj_list:
            op_name = framework_obj[0]
            op_type = framework_obj[1]
            op_full_name = framework_obj[4]
            op_info = framework_obj[5]
            for timeline_obj in self._timeline_meta:
                if op_full_name == timeline_obj.get('name'):
                    timeline_obj['name'] = op_name
                    timeline_obj['args'] = {
                        'type': op_type,
                        'fullname': op_full_name
                    }
                    timeline_obj['args'].update(op_info)
