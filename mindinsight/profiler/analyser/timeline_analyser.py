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
        display_filename = self._display_filename.format(self._device_id)
        # Check if there is a timeline json file for display
        file_path = os.path.join(self._profiling_dir, display_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid timeline json path.'
        )

        timeline = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f_obj:
                    timeline = json.load(f_obj)
            except (IOError, OSError, json.JSONDecodeError) as err:
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
            except (IOError, OSError, json.JSONDecodeError) as err:
                logger.error('Error occurred when read timeline summary file: %s', err)
                raise ProfilerIOException

        return timeline_summary

    def write_timeline(self):
        """Load data according to the parsed profiling files."""
        # Write timeline to file.
        logger.info('Writing timeline file...')
        self.write_timeline_to_json_by_limitation()
        logger.info('Finished file writing!')

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

        length = len(self._timeline_meta)
        try:
            with open(display_file_path, 'w') as json_file:
                json_file.write('[')
                for index, item in enumerate(self._timeline_meta):
                    json.dump(item, json_file)
                    file_size = os.path.getsize(display_file_path)
                    if file_size > SIZE_LIMIT:
                        break
                    if index == length - 1:
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

    def _load_timeline_data(self):
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

        timeline_list = []
        try:
            with open(file_path, 'r') as f_obj:
                for line in f_obj:
                    if not line.startswith('op_name'):
                        line_list = line.strip('\n').split(',')
                        timeline_list.append(line_list)
        except (IOError, OSError) as err:
            logger.error('Error occurred when read timeline intermediate file: %s', err)
            raise ProfilerIOException

        return timeline_list

    def _parse_timeline_data(self, timeline, min_cycle_counter):
        """Parse timeline data."""
        # factor to convert the time unit from 1ms to 1us for timeline display
        factor = 1000
        op_meta = TimelineContainer(timeline)
        timeline_dict = {}
        timeline_dict['name'] = op_meta.op_name
        timeline_dict['ph'] = 'X'
        timeline_dict['tid'] = op_meta.stream_id
        timeline_dict['ts'] = (op_meta.start_time - min_cycle_counter) * factor
        dur = op_meta.duration * factor
        timeline_dict['dur'] = dur
        if op_meta.pid is None:
            timeline_dict['pid'] = int(self._device_id)
            # Update total time of operator execution.
            self._timeline_summary['total_time'] += dur
        else:  # AllReduce and AI CPU pid
            timeline_dict['pid'] = op_meta.pid
        self._timeline_meta.append(timeline_dict)

    @staticmethod
    def _update_num_of_streams(timeline, stream_count_dict):
        """Update number of streams."""
        stream_id = timeline[1]
        if stream_id not in stream_count_dict.keys():
            stream_count_dict[stream_id] = 1
        else:
            stream_count_dict[stream_id] += 1

    def get_min_cycle_counter(self):
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

    def init_timeline(self, all_reduce_info, framework_info, aicpu_info, min_cycle_counter):
        """
        Init timeline metadata, adding all collected info.

        Args:
            all_reduce_info (list[list]): The metadata of AllReduce operator.
            framework_info (dict): The framework metadata.
            aicpu_info (dict): The metadata of AI CPU operator.
            min_cycle_counter (float): The minimum cycle counter of the timeline.
        """
        if min_cycle_counter == float('inf'):
            min_cycle_counter = 0

        logger.info('Initiating timeline...')
        timeline_list = self._load_timeline_data()
        self._timeline_summary['op_exe_times'] = len(timeline_list)

        # Add AllReduce info to timeline temp list and sort by start time.
        if all_reduce_info:
            logger.debug('AllReduce info found. Start adding info into timeline...')
            timeline_list.extend(all_reduce_info)
            timeline_list.sort(key=lambda x: float(x[2]))

        # Add AI CPU data into timeline temp list and sort by start time.
        aicpu_data = aicpu_info.get('info')
        if aicpu_data:
            timeline_list.extend(aicpu_data)
            timeline_list.sort(key=lambda x: float(x[2]))
            self._timeline_summary['op_exe_times'] += aicpu_info.get('op_exe_times', 0)
            self._timeline_summary['num_of_streams'] += aicpu_info.get('num_of_streams', 0)
            self._timeline_summary['num_of_ops'] += aicpu_info.get('num_of_ops', 0)
            self._timeline_summary['total_time'] += aicpu_info.get('total_time', 0)

        # Init a dict for counting the num of streams.
        stream_count_dict = {}
        for timeline in timeline_list:
            self._parse_timeline_data(timeline, min_cycle_counter)
            # Updating the collection of streams.
            if len(timeline) == 4:
                self._update_num_of_streams(timeline, stream_count_dict)

        # Get framework metadata.
        framework_obj_list = framework_info.get('object')
        # The length of list is the number of operators.
        self._timeline_summary['num_of_ops'] += len(framework_obj_list)
        self._add_framework_info(framework_obj_list)
        logger.info('Finished adding info into timeline...')

        # Update timeline summary info
        self._timeline_summary['num_of_streams'] += len(stream_count_dict.keys())

    def _add_framework_info(self, framework_obj_list):
        """
        Add framework info into timeline metadata.

        Args:
            framework_obj_list (list): The framework metadata.
        """
        logger.debug('Start adding framework info into timeline...')
        # Get the framework info that will be written into timeline.
        framework_info_dict = {}
        for framework_obj in framework_obj_list:
            op_name = framework_obj[0]
            op_type = framework_obj[1]
            op_full_name = framework_obj[4]
            op_info = framework_obj[5]
            framework_info_dict[op_full_name] = {
                'name': op_name,
                'args': {
                    'type': op_type,
                    'fullname': op_full_name
                }
            }
            framework_info_dict[op_full_name]['args'].update(op_info)

        # Insert framework info into timeline.
        for timeline_item in self._timeline_meta:
            op_full_name = timeline_item.get('name')
            framework_item = framework_info_dict.get(op_full_name)
            if framework_item:
                timeline_item['name'] = framework_item.get('name')
                timeline_item['args'] = framework_item.get('args')

        logger.debug('Finished adding framework info into timeline...')
