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
from mindinsight.profiler.analyser.gpu_analyser import GpuAnalyser
from mindinsight.profiler.common.validator import validate
from mindinsight.profiler.common.exceptions.exceptions import ProfilerRawFileException
from mindinsight.profiler.common.log import logger as log


class CpuOpTypeAnalyser(GpuAnalyser):
    """Cpu operation type analyser."""
    _col_names = validate.CPU_TYPE_COL
    _csv_file_to_analyse = 'cpu_op_type_info_{}.csv'

    @staticmethod
    def _convert_field_type(row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        try:
            return [row[0], int(row[1]), int(row[2]), float(row[3]), float(row[4]), float(row[5])*100]
        except IndexError as err:
            log.exception(err)
            raise ProfilerRawFileException('failed to get HOST CPU operator type data.')


class CpuOpInfoAnalyser(GpuAnalyser):
    """Cpu operation detail info analyser."""
    _col_names = validate.CPU_DETAIL_COL
    _csv_file_to_analyse = 'cpu_op_detail_info_{}.csv'

    @staticmethod
    def _convert_field_type(row):
        """
        Convert the field type to the specific type.

        Args:
            row (list): One row data from parsed data.

        Returns:
            list, the converted data.
        """
        try:
            return [row[0], row[1], row[2], row[3], int(row[4]), float(row[5]), float(row[6]), float(row[7]), row[8]]
        except IndexError as err:
            log.exception(err)
            raise ProfilerRawFileException('failed to get HOST CPU operator detail data.')
