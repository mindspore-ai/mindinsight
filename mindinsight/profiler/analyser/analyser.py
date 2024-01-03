# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""The specific analyser class."""
import csv
import json
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path
from mindinsight.profiler.common.exceptions.exceptions import ProfilerIOException


class AicoreTypeAnalyser(BaseAnalyser):
    """
    The analyser for analyzing the AICORE operator types.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['kernel_type', 'total_time', 'execution_frequency', 'total_percent', 'avg_time']
    _file_name_aicore_type_time = 'aicore_intermediate_{}_type.csv'

    def _load(self):
        """Load data according to the parsed AICORE operator types file."""
        op_type_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_type_time.format(self._device_id)
        )

        op_type_file_path = validate_and_normalize_path(
            op_type_file_path, raise_key='Invalid aicore_type file path.'
        )

        if not os.path.isfile(op_type_file_path):
            logger.warning('The file <%s> does not exist.', op_type_file_path)
            return

        with open(op_type_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                self._data.append(self._convert_field_type(info))

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        self._result = list(filter(_inner_filter, self._data))

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        for item in self._result:
            item[1] = float(format(item[1], '.6f'))
        return super()._organize_query_result()

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        total_time = self._format_float_data(float(row[1]) * self._ms_to_us)
        return [row[0], total_time,
                int(row[2]), self._format_float_data(float(row[3]) * 100),
                self._format_float_data(total_time / int(row[2]))]


class AicoreDetailAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the AICORE operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['op_name', 'kernel_name', 'kernel_type', 'avg_execution_time', 'execution_frequency',
                  'MFLOPs(10^6 cube)', 'GFLOPS(10^9 cube)', 'MFLOPs(10^6 vector)', 'GFLOPS(10^9 vector)', 'op_info']
    _file_name_aicore_detail_time = 'aicore_intermediate_{}_detail.csv'
    _file_name_flops = 'flops_{}.txt'
    _file_name_framework_info = 'framework_raw_{}.csv'

    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self._none_filter_condition_key = [
            'is_display_detail', 'is_display_full_op_name'
        ]
        self._none_sort_col_names = ['op_info']

    def query_and_sort_by_op_type(self, filter_condition, op_type_order: list):
        """
        Query the AICORE operator detail information by `filter_condition`,
        and sort by `op_type_order` and execution time.

        Args:
            filter_condition (dict): The filter condition.
            op_type_order (list[str]): The name of the operator type in order.

        Returns:
            dict, The results are filtered and sorted.
        """
        if filter_condition is None:
            filter_condition = {}
        self._filter(filter_condition)

        type_detail_cache = {}
        is_display_full_op_name = filter_condition.get(
            'is_display_full_op_name', True
        )
        kernel_type_idx = 2 if is_display_full_op_name else 1
        avg_exec_time_idx = 3 if is_display_full_op_name else 2
        for detail_info in self._result:
            op_type = detail_info[kernel_type_idx]
            if op_type not in op_type_order:
                continue
            infos = type_detail_cache.get(op_type)
            if infos:
                infos.append(detail_info)
            else:
                type_detail_cache[op_type] = [detail_info]

        result = []
        for op_type in op_type_order:
            detail_infos = type_detail_cache.get(op_type)
            if detail_infos is None:
                continue
            detail_infos.sort(key=lambda item: item[avg_exec_time_idx], reverse=True)
            result.extend(detail_infos)

        return {
            'col_name': self._display_col_names,
            'object': result
        }

    def _load(self):
        """Load data according to the parsed AICORE operator file."""
        op_detail_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_detail_time.format(self._device_id)
        )
        framework_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_framework_info.format(self._device_id)
        )
        flops_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_flops.format(self._device_id)
        )
        op_detail_file_path = validate_and_normalize_path(
            op_detail_file_path, raise_key='Invalid aicore_detail file path.'
        )
        framework_file_path = validate_and_normalize_path(
            framework_file_path, raise_key='Invalid framework file path.'
        )
        flops_file_path = validate_and_normalize_path(
            flops_file_path, raise_key='Invalid flops file path.'
        )
        if not os.path.isfile(op_detail_file_path):
            logger.warning('The file <%s> does not exist.', op_detail_file_path)
            return
        if not os.path.isfile(framework_file_path):
            logger.warning('The file <%s> does not exist.', framework_file_path)
            return

        framework_infos = dict()
        with open(framework_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                framework_infos[info[3]] = self._convert_framework_field_type(
                    info
                )

        flops_infos = dict()
        if os.path.isfile(flops_file_path):
            with open(flops_file_path, 'r') as f_obj:
                # skip the first line which is header info.
                next(f_obj)
                for line in f_obj:
                    flops_line = line.strip().split(',')
                    if not flops_line[1]:
                        continue
                    # flops_line[0] is full_op_name.
                    flops_infos[flops_line[0]] = flops_line[1:]
        else:
            logger.warning('The file <%s> does not exist.', flops_file_path)

        with open(op_detail_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                detail_info = self._get_op_detail_info(info, framework_infos, flops_infos)
                self._data.append(detail_info)

        del framework_infos
        del flops_infos

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        def _inner_map(item: list):
            inner_item = item[1:9]
            if is_display_full_op_name:
                inner_item.insert(0, item[0])
            if is_display_detail:
                inner_item.append(item[9])
            return inner_item

        is_display_detail = filter_condition.get('is_display_detail', True)
        is_display_full_op_name = filter_condition.get(
            'is_display_full_op_name', True
        )
        self._set_display_col_name(is_display_detail, is_display_full_op_name)
        if is_display_detail and is_display_full_op_name:
            self._result = list(filter(_inner_filter, self._data))
        else:
            self._result = list(
                map(_inner_map, filter(_inner_filter, self._data))
            )

    def _set_display_col_name(self, is_display_detail, is_display_full_op_name):
        """
        Set the display column name according to the filter condition.

        Args:
            is_display_detail (bool): Whether to display the detailed operator
                information.
            is_display_full_op_name (bool): Whether to display the operator full
                name.
        """
        self._display_col_names = self._col_names[1:9]
        if is_display_full_op_name:
            self._display_col_names.insert(0, self._col_names[0])
        if is_display_detail:
            self._display_col_names.append(self._col_names[9])

    @staticmethod
    def _convert_framework_field_type(row):
        """
        Convert the field type of framework file to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        return [row[4], row[5], row[6], row[7],
                json.loads(row[8]) if row[8] else None]

    def _get_op_detail_info(self, row, framework_infos, flops_infos):
        """
        Get operator detail information.

        Args:
            row (list[str]): One row data from parsed operator file.
            framework_infos (dict): All framework information.
            flops_infos (dict): All flops information.

        Returns:
            list[Union[str, float]], the operator detail information in one row.
        """
        framework_info = framework_infos.get(row[0])
        flops_info = flops_infos.get(row[0], ['-', '-', '-', '-'])
        if len(flops_info) > 3:
            return [framework_info[0], framework_info[1], framework_info[2],
                    self._format_float_data(float(row[1]) * self._ms_to_us),
                    self._format_float_data(int(row[2])),
                    self._format_float_data(flops_info[0]),
                    self._format_float_data(flops_info[1]),
                    self._format_float_data(flops_info[2]),
                    self._format_float_data(flops_info[3]),
                    framework_info[4]]
        return [framework_info[0], framework_info[1], framework_info[2],
                self._format_float_data(float(row[1]) * self._ms_to_us),
                self._format_float_data(int(row[2])),
                self._format_float_data(flops_info[0]),
                self._format_float_data(flops_info[1]),
                self._format_float_data(flops_info[2]),
                framework_info[3], framework_info[4]]


class AicpuTypeAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the AICPU operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['kernel_type', 'total_time', 'execution_frequency', 'percent']
    _file_name_aicpu_time = 'aicpu_intermediate_{}.csv'

    def _load(self):
        """Load data according to the parsed AICPU operator file."""
        aicpu_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicpu_time.format(self._device_id)
        )
        aicpu_file_path = validate_and_normalize_path(
            aicpu_file_path, raise_key='Invalid aicpu file path.'
        )

        if not os.path.isfile(aicpu_file_path):
            logger.warning('The file <%s> does not exist.', aicpu_file_path)
            return

        type_detail_cache = dict()
        with open(aicpu_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for item in csv_reader:
                op_type = item[1].split('-')[0]
                info = type_detail_cache.get(op_type)
                if info:
                    info.append(item)
                else:
                    type_detail_cache[op_type] = [item]
        type_temp_detail_cache = dict()
        total_time = 0
        result = []
        for key, value in type_detail_cache.items():
            exec_frequency = len(value)
            total_time_index = 2
            exec_total_time = sum([float(i[total_time_index]) for i in value]) * self._ms_to_us
            total_time += exec_total_time
            type_temp_detail_cache[key] = [key, round(exec_total_time, self._ms_round_digits), exec_frequency]

        for key, value in type_temp_detail_cache.items():
            execution_time_index = 1
            percent = round((value[execution_time_index] / total_time) * 100, 2)
            value.append(percent)
            result.append(value)

        self._data = result

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        self._result = list(filter(_inner_filter, self._data))


class AicpuDetailAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the AICPU operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['kernel_name', 'kernel_type', 'avg_execution_time', 'dispatch_time',
                  'execution_frequency']
    _file_name_aicpu_time = 'aicpu_intermediate_{}.csv'

    def _load(self):
        """Load data according to the parsed AICPU operator file."""
        aicpu_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicpu_time.format(self._device_id)
        )
        aicpu_file_path = validate_and_normalize_path(
            aicpu_file_path, raise_key='Invalid aicpu file path.'
        )
        if not os.path.isfile(aicpu_file_path):
            logger.warning('The file <%s> does not exist.', aicpu_file_path)
            return

        temp_dict = dict()
        with open(aicpu_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                aicpu_info = self._convert_field_type(info)
                key = aicpu_info[0]
                if key not in temp_dict:
                    temp_dict[key] = [0, 0, 0]
                temp_dict.get(key)[0] += aicpu_info[2]
                temp_dict.get(key)[1] += aicpu_info[3]
                temp_dict.get(key)[2] += 1
        for k, v in temp_dict.items():
            self._data.append([k, k.split('-')[0], round(v[0] / v[2] * self._ms_to_us, self._ms_round_digits),
                               round((v[1] / v[2]) * self._ms_to_us, self._ms_round_digits), v[2]])

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        self._result = list(filter(_inner_filter, self._data))

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        # Make the previous data (mindspore version before 2021.06.02) compatible.
        if len(row) == 6:
            row.insert(4, '0')
        return [row[1], row[1].split('-')[0], self._format_float_data(float(row[2])),
                self._format_float_data(float(row[3]))]


class PynativeTypeAnalyser(BaseAnalyser):
    """
    The analyser for analyzing the Pynative operator types.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['op_type', 'execution_time', 'execution_frequency', 'percent']
    _file_name_aicore_type_time = 'pynative_op_intermediate_{}_type.csv'

    def _load(self):
        """Load data according to the parsed Pynative operator types file."""
        op_type_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_type_time.format(self._device_id)
        )

        op_type_file_path = validate_and_normalize_path(
            op_type_file_path, raise_key='Invalid pynative_type file path.'
        )

        if not os.path.isfile(op_type_file_path):
            logger.warning('The file <%s> does not exist.', op_type_file_path)
            return

        with open(op_type_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                self._data.append(self._convert_field_type(info))

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        self._result = list(filter(_inner_filter, self._data))

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        for item in self._result:
            item[1] = float(format(item[1], '.6f'))
        return super()._organize_query_result()

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        return [row[0], self._format_float_data(float(row[1])) * self._ms_to_us,
                int(row[2]), self._format_float_data(float(row[3]))]


class PynativeDetailAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the Pynative operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['op_name', 'op_type', 'avg_execution_time', 'subgraph', 'full_op_name']
    _file_name_aicore_detail_time = 'pynative_op_intermediate_{}_detail.csv'

    def query_and_sort_by_op_type(self, filter_condition, op_type_order: list):
        """
        Query the Pynative operator detail information by `filter_condition`,
        and sort by `op_type_order` and execution time.

        Args:
            filter_condition (dict): The filter condition.
            op_type_order (list[str]): The name of the operator type in order.

        Returns:
            dict, The results are filtered and sorted.
        """
        if filter_condition is None:
            filter_condition = {}
        self._filter(filter_condition)

        type_detail_cache = {}
        for detail_info in self._result:
            op_type = detail_info[1]
            if op_type not in op_type_order:
                continue
            infos = type_detail_cache.get(op_type)
            if infos:
                infos.append(detail_info)
            else:
                type_detail_cache[op_type] = [detail_info]

        result = []
        for op_type in op_type_order:
            detail_infos = type_detail_cache.get(op_type)
            if detail_infos is None:
                continue
            detail_infos.sort(key=lambda item: item[2], reverse=True)
            result.extend(detail_infos)

        return {
            'col_name': self._display_col_names,
            'object': result
        }

    def _load(self):
        """Load data according to the parsed Pynative operator file."""
        op_detail_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_detail_time.format(self._device_id)
        )

        op_detail_file_path = validate_and_normalize_path(
            op_detail_file_path, raise_key='Invalid Pynative_detail file path.'
        )

        if not os.path.isfile(op_detail_file_path):
            logger.warning('The file <%s> does not exist.', op_detail_file_path)
            return

        with open(op_detail_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)
            for info in csv_reader:
                detail_info = self._get_op_detail_info(info)
                self._data.append(detail_info)

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        def _inner_map(item: list):
            inner_item = item[0:4]
            if is_display_full_op_name:
                inner_item.append(item[4])
            return inner_item

        is_display_full_op_name = filter_condition.get(
            'is_display_full_op_name', True
        )
        self._set_display_col_name(is_display_full_op_name)
        if is_display_full_op_name:
            self._result = list(filter(_inner_filter, self._data))
        else:
            self._result = list(
                map(_inner_map, filter(_inner_filter, self._data))
            )

    def _set_display_col_name(self, is_display_full_op_name):
        """
        Set the display column name according to the filter condition.

        Args:
            is_display_detail (bool): Whether to display the detailed operator
                information.
            is_display_full_op_name (bool): Whether to display the operator full
                name.
        """
        self._display_col_names = self._col_names[0:4]
        if is_display_full_op_name:
            self._display_col_names.append(self._col_names[4])

    def _get_op_detail_info(self, row):
        """
        Get operator detail information.

        Args:
            row (list[str]): One row data from parsed operator file.
        Returns:
            list[Union[str, float]], the operator detail information in one row.
        """
        return [row[0], row[0].split('-')[0],
                self._format_float_data(float(row[1])) * self._ms_to_us,
                'Default', 'Default/' + row[0]]


class DynamicShapeAnalyser(BaseAnalyser):
    """Analyse dynamic shape info data from file."""
    _dynamic_file_name = 'dynamic_shape_info_{}.json'

    def get_dynamic_shape_detail(self):
        """
        Get dynamic shape information for UI display.

        Returns:
            json, the content of dynamic shape information.
        """
        detail_filename = self._dynamic_file_name.format(self._device_id)
        file_path = os.path.join(self._profiling_dir, detail_filename)
        file_path = validate_and_normalize_path(
            file_path, raise_key='Invalid dynamic shape file path.'
        )
        dynamic_shape_info = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as fp:
                    dynamic_shape_info = json.load(fp)
            except (IOError, OSError, json.JSONDecodeError) as err:
                logger.error('Error occurred when read dynamic shape file: %s', err)
                raise ProfilerIOException()
        else:
            logger.warning('No dynamic shape file. Please check the output path.')
        return dynamic_shape_info

    def _load(self):
        """Load data according to the parsed profiling files."""

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """
