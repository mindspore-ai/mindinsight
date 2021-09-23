# Copyright 2021 Huawei Technologies Co., Ltd
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
"""The cpu base analyser."""
import csv
import os

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.validator import validate
from mindinsight.profiler.common.exceptions.exceptions import ProfilerRawFileException
from mindinsight.profiler.common.log import logger as log
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class CpuAnalyser(BaseAnalyser):
    """Cpu base analyser."""
    _csv_file_to_analyse = ""

    def _load(self):
        """Load data according to the parsed CPU operator types file."""
        op_type_file_path = os.path.join(
            self._profiling_dir,
            self._csv_file_to_analyse.format(self._device_id)
        )
        op_type_file_path = validate_and_normalize_path(
            op_type_file_path, raise_key="Invalid op_type_file_path")
        if not os.path.isfile(op_type_file_path):
            log.warning('The file <%s> does not exist.', op_type_file_path)
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

class CpuOpTypeAnalyser(CpuAnalyser):
    """Cpu operation type analyser."""
    _col_names = validate.CPU_TYPE_COL
    _csv_file_to_analyse = 'cpu_op_type_info_{}.csv'

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        try:
            return [row[0], int(row[1]), int(row[2]),
                    self._format_float_data(float(row[3])),
                    self._format_float_data(float(row[4])),
                    self._format_float_data(float(row[5])*100)]
        except IndexError as err:
            log.exception(err)
            raise ProfilerRawFileException('failed to get HOST CPU operator type data.')


class CpuOpInfoAnalyser(CpuAnalyser):
    """Cpu operation detail info analyser."""
    _col_names = validate.CPU_DETAIL_COL
    _csv_file_to_analyse = 'cpu_op_detail_info_{}.csv'

    def _convert_field_type(self, row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        try:
            return [row[0], row[1], row[2], row[3], int(row[4]),
                    self._format_float_data(float(row[5])), self._format_float_data(float(row[6])),
                    self._format_float_data(float(row[7])), row[8]]
        except IndexError as err:
            log.exception(err)
            raise ProfilerRawFileException('failed to get HOST CPU operator detail data.')
