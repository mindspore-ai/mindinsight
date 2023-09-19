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
"""The gpu base analyser."""
import csv
import os
import json
from collections import defaultdict

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class GpuAnalyser(BaseAnalyser):
    """Gpu base analyser."""
    _csv_file_to_analyse = ""

    def _load(self):
        """Load data according to the parsed AICORE operator types file."""
        op_type_file_path = os.path.join(
            self._profiling_dir,
            self._csv_file_to_analyse.format(self._device_id)
        )
        op_type_file_path = validate_and_normalize_path(
            op_type_file_path, raise_key="Invalid op_type_file_path")
        if not os.path.isfile(op_type_file_path):
            logger.warning('The file <%s> does not exist.', op_type_file_path)
            return

        with open(op_type_file_path, 'r') as file:
            csv_reader = csv.reader(file)
            _ = next(csv_reader)
            for info in csv_reader:
                self._data.append(self._convert_field_type(info))

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return row

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        self._result = list(filter(_inner_filter, self._data))


class GpuOpTypeAnalyser(GpuAnalyser):
    """Gpu operation type analyser."""
    _col_names = ["op_type", "total_time", "execution_frequency", "total_percent", "avg_time"]
    _csv_file_to_analyse = 'gpu_op_type_info_{}.csv'

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], self._format_float_data(float(row[2])), int(row[1]),
                self._format_float_data(float(row[3]) * 100), self._format_float_data(float(row[4]))]


class GpuOpInfoAnalyser(GpuAnalyser):
    """Gpu operation detail info analyser."""
    _col_names = ["op_side", "op_type", "op_name", "op_full_name",
                  "op_occurrences", "op_total_time", "op_avg_time",
                  "proportion", "cuda_activity_cost_time", "cuda_activity_call_count"]
    _csv_file_to_analyse = 'gpu_op_detail_info_{}.csv'

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], row[1], row[2], row[3], int(row[4]),
                self._format_float_data(float(row[5])), self._format_float_data(float(row[6])),
                self._format_float_data(float(row[7])), self._format_float_data(float(row[8])), int(row[9])]


class GpuCudaActivityAnalyser(GpuAnalyser):
    """Gpu activity type analyser."""
    _col_names = ["name", "type", "op_full_name", "stream_id",
                  "block_dim", "grid_dim", "occurrences", "total_duration",
                  "avg_duration", "max_duration", "min_duration"]
    _csv_file_to_analyse = 'gpu_activity_data_{}.csv'

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], row[1], row[2], row[3], row[4], row[5], int(row[6]),
                self._format_float_data(float(row[7])), self._format_float_data(float(row[8])),
                self._format_float_data(float(row[9])), self._format_float_data(float(row[10]))]


class GpuDynamicAnalyser(BaseAnalyser):
    """Gpu dynamic shape data analyser."""
    _filter_type = defaultdict(list)
    _csv_file_to_analyse = 'dynamic_shape_info_{}.json'

    def query(self, condition=None):
        """
        Query data according to the condition.

        Args:
            condition (dict): The search condition, including filter condition,
                sort condition and group condition. If the condition is `None`,
                all data will be returned. Default: None.

        Returns:
            dict, the result after filtered, sorted and grouped.
        """
        if condition is None:
            condition = {}
        filter_condition = condition.get('filter_condition', {})
        sort_condition = condition.get('sort_condition')
        group_condition = condition.get('group_condition')

        self._result = []
        self._filter_type = defaultdict(list)
        self._display_col_names = self._col_names[:]
        self._filter(filter_condition)
        self._size = len(self._result)
        if sort_condition:
            self._sort(sort_condition)
        if group_condition:
            self._group(group_condition)
        return self._organize_query_result()

    def _load(self):
        """Load data according to the parsed dynamic shape file."""
        dynamic_shape_file_path = os.path.join(
            self._profiling_dir,
            self._csv_file_to_analyse.format(self._device_id)
        )
        dynamic_shape_file_path = validate_and_normalize_path(
            dynamic_shape_file_path, raise_key="Invalid dynamic shape file path.")
        if not os.path.isfile(dynamic_shape_file_path):
            logger.warning('The file <%s> does not exist.', dynamic_shape_file_path)
            return

        with open(dynamic_shape_file_path, 'r') as file:
            self._data = json.load(file)

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """
        default_type = "operator"
        limit = 3

        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        step = filter_condition.get("step_filter", ["1"])[0]
        step_info = self._data.get(self._switch_type, {}).get(step)
        if not step_info:
            return
        for item in step_info:
            self._result.append(list(item.values()))
        self._result = list(filter(_inner_filter, self._result))

        if self._switch_type == default_type:
            operator_data = self._data.get("operator_type")
        else:
            operator_data = self._data.get("kernel_type")
        self._all_type = list(operator_data[step].keys())

        if len(self._all_type) > limit:
            dispaly_op_type = filter_condition.get("dispaly_op_type", self._all_type[:limit])
        else:
            dispaly_op_type = filter_condition.get("dispaly_op_type", self._all_type)
        for step in operator_data:
            for op_type in dispaly_op_type:
                filter_data = operator_data[step].get(op_type, [0] * len(self._col_names))[2]
                self._filter_type[op_type].append(filter_data)

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        return {
            'col_name': self._display_col_names,
            'object': self._result,
            'size': self._size,
            "all_type": self._all_type,
            "filter_type": self._filter_type
        }


class GpuOpTypeInfoAnalyser(GpuDynamicAnalyser):
    """Gpu Op type info analyser."""
    _switch_type = "operator"
    _col_names = ["step", "op_side", "op_type", "op_name", "duration", "op_shape"]


class GpuCudaTypeInfoAnalyser(GpuDynamicAnalyser):
    """Gpu Cuda type info analyser."""
    _switch_type = "kernel"
    _col_names = ["step", "op_type", "op_name", "op_full_name", "duration", "block_dim", "grid_dim"]
