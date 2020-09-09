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
"""The gpu base analyser."""
import csv
import os

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

    @staticmethod
    def _convert_field_type(row):
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
    _col_names = ["op_type", "type_occurrences", "total_time", "proportion", "avg_time"]
    _csv_file_to_analyse = 'gpu_op_type_info_{}.csv'

    @staticmethod
    def _convert_field_type(row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], int(row[1]), float(row[2]), float(row[3])*100, float(row[4])]


class GpuOpInfoAnalyser(GpuAnalyser):
    """Gpu operation detail info analyser."""
    _col_names = ["op_side", "op_type", "op_name", "op_full_name",
                  "op_occurrences", "op_total_time", "op_avg_time",
                  "proportion", "cuda_activity_cost_time", "cuda_activity_call_count"]
    _csv_file_to_analyse = 'gpu_op_detail_info_{}.csv'

    @staticmethod
    def _convert_field_type(row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], row[1], row[2], row[3], int(row[4]), float(row[5]),
                float(row[6]), float(row[7]), float(row[8]), int(row[9])]


class GpuCudaActivityAnalyser(GpuAnalyser):
    """Gpu activity type analyser."""
    _col_names = ["name", "type", "op_full_name", "stream_id",
                  "block_dim", "grid_dim", "occurrences", "total_duration",
                  "avg_duration", "max_duration", "min_duration"]
    _csv_file_to_analyse = 'gpu_activity_data_{}.csv'

    @staticmethod
    def _convert_field_type(row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        return [row[0], row[1], row[2], row[3], row[4], row[5], int(row[6]),
                float(row[7]), float(row[8]), float(row[9]), float(row[10])]
