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
"""The StepTraceAnalyser analyser class."""
import csv
import json
import os

from mindinsight.datavisual.utils.tools import to_int
from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import ProfilerParamValueErrorException, \
    ProfilerFileNotFoundException, StepNumNotSupportedException, ProfilerRawFileException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.util import query_latest_trace_time_file, get_field_value, \
    get_summary_for_step_trace, to_millisecond
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class StepTraceAnalyser(BaseAnalyser):
    """The analyser for analyzing training steps."""

    _col_names = []
    _attr_ui_name = 'name'
    _attr_ui_start = 'start'
    _attr_ui_duration = 'duration'
    _point_info = {}

    @property
    def summary(self):
        """The property of summary info."""

        summary = get_summary_for_step_trace(self._data[-1], self.__column__)
        summary['total_steps'] = self._size
        return summary

    @property
    def point_info(self):
        """The property of point info."""
        return self._point_info

    def query(self, condition=None):
        """
        Query data according to the condition.

        Args:
            condition (dict): The search condition, only contains `filter_condition` parameter.
                Default: None.

        Returns:
            dict, the result after filtered, sorted and grouped.
        """
        if condition is None:
            condition = {}
        filter_condition = condition.get('filter_condition', {})
        log.info("Receive query request. %s", filter_condition)
        self._validate_filter_condition(filter_condition)
        self._result = {'size': self._size}
        self._filter(filter_condition)

        return self._result

    def query_for_all_reduce(self):
        """
        Query for all reduce info.

        Returns:
            list[dict], reduce information. Each item is the reduce info for one step.
            The reduce info is format like:
            {stream_id: List[Tuple(start_point, end_point, duration, field_name)]}.
        """
        reduce_infos = []
        for row_info in self._data[:-1]:
            row_info_dict = self._get_info_dict_from_row_data(row_info, 'systime')
            reduce_info = self._sort_reduce_by_time(row_info_dict)
            if reduce_info:
                reduce_infos.extend(reduce_info)

        return reduce_infos

    def _load(self):
        """Load data according to the parsed AICORE operator types file."""
        file_path = query_latest_trace_time_file(self._profiling_dir, self._device_id)
        if not file_path:
            log.error("Failed to find parsed trace time file.")
            raise ProfilerFileNotFoundException('parsed step trace time file')
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid latest_trace_trace_time file path.")
        with open(file_path, 'r') as handle:
            csv_reader = csv.reader(handle)
            self.__column__ = next(csv_reader)
            self._data = list(csv_reader)
        self._size = len(self._data) - 1
        self._display_col_names = self._col_names[:]
        self._load_point_info()

    def _load_point_info(self):
        """Load point info."""
        file_path = os.path.join(self._profiling_dir, 'step_trace_point_info.json')
        file_path = validate_and_normalize_path(
            file_path, raise_key="Invalid step_trace_point_info file path.")
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    self._point_info = json.load(file)
                except (json.JSONDecodeError, TypeError) as err:
                    log.exception(err)
                    raise ProfilerRawFileException('Fail to parse point info file.')

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.

                - mode (str): The kind of information. `step` return the info about specific
                    step. `proc` return the info about specific field in parsed trace file.

                - step_id (int): The selected step_id. If not given, it means all steps is required.
                    If the value is 0, it means average info for all steps except the first is
                    required.

                - proc_name (str): The selected field name.

                - time_type (str): The value type. `systime` keeps the original value.
                    `realtime` transforms the value in millisecond. Default: `realtime`.
        """
        mode = filter_condition.get('mode', 'step')
        if mode == 'step':
            self._get_step_details(step_id=filter_condition.get('step_id'),
                                   time_type=filter_condition.get('time_type', 'realtime'))
        else:
            self._get_proc_details(step_id=filter_condition.get('step_id'),
                                   proc_name=filter_condition.get('proc_name'),
                                   time_type=filter_condition.get('time_type', 'realtime'))

    def _construct_time_point(self, name, start, duration):
        """Construct time point."""
        point = {}
        if start >= 0 and duration >= 0:
            point = {
                self._attr_ui_name: name,
                self._attr_ui_start: round(start, 4),
                self._attr_ui_duration: round(duration, 4)
            }
        else:
            log.warning("Not invalid point info: "
                        "name: %s, start: %s, duration: %s", name, start, duration)
        return point

    def _get_step_details(self, step_id, time_type='realtime'):
        """
        Get step trace info for selected step and save the result.

        Args:
            step_id (int): The selected step_id. If the value is 0, it means average info
                for all steps except the first is required.
            time_type (str): The value type. `systime` keeps the original value.
                `realtime` transforms the value in millisecond. Default: `realtime`.
        """
        if step_id is None:
            step_id = 0
        row_info = self._data[step_id - 1]
        row_info_dict = self._get_info_dict_from_row_data(row_info, time_type)
        # first line only contains total time
        first_line = [self._construct_time_point('', 0, row_info_dict.get('total', 0))]
        # second line contains iteration_interval, fp_and_bp and tail
        second_line = self._get_main_proc_points(row_info_dict)
        # construct reduces lines
        reduce_lines = self._construct_reduce_lines(row_info_dict)

        graph = [first_line, second_line]
        graph.extend(reduce_lines)
        self._result['training_trace_graph'] = graph

    def _get_info_dict_from_row_data(self, row_info, time_type):
        """
        Get step info in dict format.

        Args:
            row_info (list[str]): Step info, the value is corresponding to `__column__`.
            time_type (str): The value type. `systime` keeps the original value.
                `realtime` transforms the value in millisecond. Default: `realtime`.

        Returns:
            dict, step trace information. The key is in `__column__`.
        """
        row_info_dict = {}
        for key, value in zip(self.__column__, row_info):
            if key == 'step_num':
                continue
            value = to_int(value, key)
            row_info_dict[key] = to_millisecond(value) if time_type == 'realtime' else value
        return row_info_dict

    def _get_main_proc_points(self, row_info_dict):
        """
        Get iteration_interval, fp_and_bp and tail points.

        Args:
            row_info_dict (dict): Step trace information.

        Returns:
            list[dict], the list of time points.
        """
        start_point = row_info_dict.get('start_point', 0)
        fp_point = row_info_dict.get('fp_point', 0)
        bp_point = row_info_dict.get('bp_point', 0)
        points_part = [
            self._construct_time_point(
                'iteration_interval', 0, row_info_dict.get('iteration_interval', 0)),
        ]
        # if fp key exist, inference scene
        if 'fp' in row_info_dict.keys():
            points = [
                self._construct_time_point(
                    'fp', fp_point - start_point, row_info_dict.get('fp', 0)),
            ]
        # training scene
        else:
            points = [
                self._construct_time_point(
                    'fp_and_bp', fp_point - start_point, row_info_dict.get('fp_and_bp', 0)),
                self._construct_time_point('tail', bp_point - start_point, row_info_dict.get('tail', 0))
            ]
        points = points_part + points
        return points

    def _get_reduce_time_in_order(self, row_info_dict):
        """
        Get reduce time in order.

        Args:
            row_info_dict (dict): Step trace information.

        Returns:
            dict, sorted reduce information. The reduce info is format like:
            {stream_id: List[Tuple(start_point, end_point, duration, field_name)]}
        """
        reduce_info = {}
        reduce_fields = [field_name for field_name in self.__column__
                         if field_name.startswith('stream_') and not field_name.endswith('point')]
        for reduce_field in reduce_fields:
            reduce_start = row_info_dict.get(reduce_field + '_start_point', 0)
            reduce_end = row_info_dict.get(reduce_field + '_end_point', 0)
            reduce_duration = row_info_dict.get(reduce_field, 0)
            if not (reduce_start and reduce_end and reduce_duration):
                log.info("Reduce event missing value.")
                continue
            cur_stream_id = reduce_field.split('_', 2)[1]
            cur_stream = reduce_info.get(cur_stream_id)
            if not cur_stream:
                cur_stream = []
                reduce_info[cur_stream_id] = cur_stream
            cur_stream.append((reduce_start, reduce_end, reduce_duration, reduce_field))
        for _, reduce_events in reduce_info.items():
            reduce_events.sort(key=lambda elem: elem[1])
        return reduce_info

    def _sort_reduce_by_time(self, row_info_dict):
        """
        Sort reduce info by time.

        Args:
            row_info_dict (dict): Step trace information.

        Returns:
            list, including the all reduce info sorted by start time only.
            [
                [reduce_field, stream_id, reduce_start, reduce_duration],
                [...],
                [...]
            ]
        """
        factor = 1e5  # convert time unit from 10ns to 1ms
        reduce_pid = 10000
        reduce_info = []
        reduce_fields = [field_name for field_name in self.__column__
                         if field_name.startswith('stream_') and not field_name.endswith('point')]
        for reduce_field in reduce_fields:
            reduce_start = row_info_dict.get(reduce_field + '_start_point')
            reduce_start = reduce_start / factor \
                if reduce_start else 0
            reduce_duration = row_info_dict.get(reduce_field)
            reduce_duration = reduce_duration / factor if reduce_duration else 0
            if not (reduce_start and reduce_duration):
                log.info("Reduce event missing value.")
                continue
            cur_stream_id = reduce_field.split('_', 2)[1]
            reduce_meta = [reduce_field, int(cur_stream_id), reduce_start,
                           reduce_duration, reduce_pid]
            reduce_info.append(reduce_meta)

        return reduce_info

    def _construct_reduce_lines(self, row_info_dict):
        """
        Construct first line in detailed graph.

        Args:
            row_info_dict (dict): Step trace information.

        Returns:
            list, list of reduce information of each stream. Each item is a list of time points.
        """
        reduce_lines = []
        start_point = row_info_dict.get('start_point', 0)
        fp_point = row_info_dict.get('fp_point', 0)
        end_point = row_info_dict.get('end_point', 0)
        reduce_info = self._get_reduce_time_in_order(row_info_dict)
        # construct time point for each line
        for _, reduce_events in reduce_info.items():
            current_line = self._construct_reduce_line(
                start_point, end_point, fp_point, reduce_events)
            reduce_lines.append(current_line)

        return reduce_lines

    def _construct_reduce_line(self, start_point, end_point, fp_point, reduce_events):
        """
        Construct list of time points for reduce line.

        Args:
            start_point (int): The start point of current step.
            end_point (int): The end point of current step.
            fp_point (int): The fp point of current step.
            reduce_events (list[Tuple]): The reduce information of current step. Each item
                contains the start, end duration and name of one reduce event.

        Returns:
            list[dict], list of time points.
        """
        current_line = []
        previous_start = fp_point
        for start, end, duration, field_name in reduce_events:
            current_line.extend([
                self._construct_time_point(
                    '', previous_start - start_point, start - previous_start),
                self._construct_time_point(
                    field_name, start - start_point, duration)
            ])
            previous_start = end
        current_line.append(self._construct_time_point(
            '', previous_start - start_point, end_point - previous_start))
        return current_line

    def _get_proc_details(self, proc_name, step_id=None, time_type='realtime'):
        """
        Get step trace info for selected step and save the result.

        Args:
            proc_name (str): The selected field name.
            step_id (int): The selected step_id. If not given, it means all steps is required.
                If the value is 0, it means average info for all steps except the first is
                required. Default: None.
            time_type (str): The value type. `systime` keeps the original value.
                `realtime` transforms the value in millisecond. Default: `realtime`.
        """
        if proc_name is None:
            log.error('`proc_name` is required for query.')
            raise ProfilerParamValueErrorException('`proc_name` is required for query.')
        if step_id is None:
            rows_info = self._data[:-1]
        else:
            rows_info = [self._data[step_id - 1]]

        proc_info = [get_field_value(row_info, proc_name, self.__column__, time_type)
                     for row_info in rows_info]
        self._result['info'] = {proc_name: proc_info}

    def _validate_filter_condition(self, filter_condition):
        """Validate step trace filter_condition."""
        mode = filter_condition.get('mode', 'step')
        self._validate_str_param(mode, ['step', 'proc'], 'mode')

        step_id = filter_condition.get('step_id')
        self._validate_step_id(step_id)

        proc_name = filter_condition.get('proc_name')
        self._validate_str_param(proc_name, self.__column__, 'proc_name')

        time_type = filter_condition.get('time_type', 'realtime')
        self._validate_str_param(time_type, ['realtime', 'systime'], 'time_type')

    def _validate_step_id(self, step_id):
        """Validate step_id."""
        if step_id is None or isinstance(step_id, int) and 0 <= step_id <= self._size:
            return
        log.error("Invalid step_id in request. step_id should be in [0, %d].", self._size)
        raise StepNumNotSupportedException([0, self._size])

    @staticmethod
    def _validate_str_param(proc_name, accept_param, error_name=''):
        """Validate proc_name."""
        if proc_name is None or isinstance(proc_name, str) and proc_name in accept_param:
            return
        log.error("Invalid param %s in request. Acceptable value is %s.", error_name, accept_param)
        raise ProfilerParamValueErrorException(f"Invalid {error_name}.")
