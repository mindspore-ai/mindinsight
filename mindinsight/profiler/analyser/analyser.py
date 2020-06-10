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
"""The specific analyser class."""
import csv
import json
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.log import logger


class AicoreTypeAnalyser(BaseAnalyser):
    """
    The analyser for analyzing the AICORE operator types.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.
    """
    __col_names__ = ['op_type', 'execution_time', 'execution_frequency',
                     'percent']
    _file_name_aicore_type_time = 'aicore_intermediate_{}_type.csv'

    def _load(self):
        """Load data according to the parsed AICORE operator types file."""
        op_type_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_type_time.format(self._device_id)
        )
        if not os.path.isfile(op_type_file_path):
            logger.warning('The file <%s> does not exist.', op_type_file_path)
            return

        with open(op_type_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            _ = next(csv_reader)
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

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        return [row[0], float(row[1]), int(row[2]), float(row[3])]


class AicoreDetailAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the AICORE operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.
    """
    __col_names__ = ['op_name', 'op_type', 'execution_time', 'subgraph',
                     'full_op_name', 'op_info']
    _file_name_aicore_detail_time = 'aicore_intermediate_{}_detail.csv'
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
        """Load data according to the parsed AICORE operator file."""
        op_detail_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_detail_time.format(self._device_id)
        )
        framework_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_framework_info.format(self._device_id)
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
            _ = next(csv_reader)
            for info in csv_reader:
                framework_infos[info[3]] = self._convert_framework_field_type(
                    info
                )

        with open(op_detail_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            _ = next(csv_reader)
            for info in csv_reader:
                detail_info = self._get_op_detail_info(info, framework_infos)
                self._data.append(detail_info)

        del framework_infos

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
            if is_display_detail:
                inner_item.append(item[5])
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
        self._display_col_names = self.__col_names__[0:4]
        if is_display_full_op_name:
            self._display_col_names.append(self.__col_names__[4])
        if is_display_detail:
            self._display_col_names.append(self.__col_names__[5])

    def _convert_framework_field_type(self, row):
        """
        Convert the field type of framework file to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, float]], the converted data.
        """
        return [row[3], row[4], row[5], row[6],
                json.loads(row[7]) if row[7] else None]

    def _get_op_detail_info(self, row, framework_infos):
        """
        Get operator detail information.

        Args:
            row (list[str]): One row data from parsed operator file.
            framework_infos (dict): All framework information.

        Returns:
            list[Union[str, float]], the operator detail information in one row.
        """
        framework_info = framework_infos.get(row[0])
        return [framework_info[1], framework_info[2], float(row[1]),
                framework_info[3], framework_info[0], framework_info[4]]


class AicpuAnalyser(BaseAnalyser):
    """
    The analyser for analyzing all the AICPU operators.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.
    """
    __col_names__ = ['serial_number', 'op_name', 'total_time', 'dispatch_time',
                     'RunV2_start', 'compute_start', 'memcpy_start',
                     'memcpy_end', 'RunV2_end']
    _file_name_aicpu_time = 'aicpu_intermediate_{}.csv'

    def _load(self):
        """Load data according to the parsed AICPU operator file."""
        aicpu_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_aicpu_time.format(self._device_id)
        )
        if not os.path.isfile(aicpu_file_path):
            logger.warning('The file <%s> does not exist.', aicpu_file_path)
            return

        with open(aicpu_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            _ = next(csv_reader)
            for info in csv_reader:
                aicpu_info = self._convert_field_type(info)
                self._data.append(aicpu_info)

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
        return [int(row[0]), row[1], float(row[2]), float(row[3]), int(row[4]),
                int(row[5]), int(row[6]), int(row[7]), int(row[8])]
