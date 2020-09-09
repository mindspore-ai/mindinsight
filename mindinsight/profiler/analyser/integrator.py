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
"""The integrator for integrating parsed profiling files."""
import csv
import os
from decimal import Decimal
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class Integrator:
    """
    The integrator for integrating parsed profiling files.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.
    """
    _file_name_aicore_detail_time = 'output_op_compute_time_{}.txt'
    _file_name_aicpu_time = 'output_data_preprocess_aicpu_{}.txt'
    _file_name_framework = 'framework_raw_{}.csv'
    _header_aicore_type = ['op_type', 'execution_time', 'execution_frequency',
                           'percent']
    _header_aicore_detail = ['full_op_name', 'execution_time']
    _header_aicpu = ['serial_number', 'op_type', 'total_time', 'dispatch_time',
                     'run_start', 'run_end']

    def __init__(self, profiling_dir, device_id):
        self._profiling_dir = profiling_dir
        self._device_id = device_id
        self._op_time_cache = {}
        self._total_time = Decimal('0.0')

    def integrate(self):
        """Integrate the parsed profiling files."""
        self._parse_aicore_detail_time()
        self._parse_aicore_type_time()
        self._parse_aicpu_time()

    def _parse_aicore_type_time(self):
        """Parse the parsed AICORE operator type file."""
        framework_file = os.path.join(
            self._profiling_dir,
            self._file_name_framework.format(self._device_id)
        )
        framework_file = validate_and_normalize_path(
            framework_file, raise_key="Invaild framework file path.")
        if not os.path.isfile(framework_file):
            return

        op_name_type_cache = {}
        with open(framework_file, 'r') as src_file:
            csv_reader = csv.reader(src_file)
            _ = next(csv_reader)

            for row in csv_reader:
                op_name_type_cache[row[3]] = row[5]

        op_type_time_cache = {}
        for full_op_name, op_time in self._op_time_cache.items():
            op_type = op_name_type_cache.get(full_op_name)
            if op_type_time_cache.get(op_type) is None:
                op_type_time_cache[op_type] = [op_time, 1]
            else:
                op_type_time_cache[op_type][0] += op_time
                op_type_time_cache[op_type][1] += 1

        op_type_file_name = 'aicore_intermediate_' + self._device_id + '_type.csv'
        op_type_file_path = os.path.join(self._profiling_dir, op_type_file_name)
        with open(op_type_file_path, 'w') as type_file:
            csv_writer = csv.writer(type_file)
            csv_writer.writerow(self._header_aicore_type)

            for op_type, op_type_time_info in op_type_time_cache.items():
                type_info = [
                    op_type, op_type_time_info[0], op_type_time_info[1],
                    round((op_type_time_info[0] / self._total_time) * 100, 2)
                ]
                csv_writer.writerow(type_info)

    def _parse_aicore_detail_time(self):
        """Parse the parsed AICORE operator time file."""
        aicore_detail_file = os.path.join(
            self._profiling_dir,
            self._file_name_aicore_detail_time.format(self._device_id)
        )
        aicore_detail_file = validate_and_normalize_path(
            aicore_detail_file, raise_key="Invaild aicore_detail file path.")
        if not os.path.isfile(aicore_detail_file):
            return

        op_detail_file_name = 'aicore_intermediate_' + self._device_id + '_detail.csv'
        op_detail_file_path = os.path.join(
            self._profiling_dir, op_detail_file_name
        )
        with open(aicore_detail_file, 'r') as src_file:
            row = src_file.readline()
            if row.startswith('op_name'):
                _ = src_file.readline()
            elif row.startswith('====='):
                _ = src_file.readline()
                _ = src_file.readline()
            else:
                return

            with open(op_detail_file_path, 'w') as detail_file:
                csv_writer = csv.writer(detail_file)
                csv_writer.writerow(self._header_aicore_detail)

                while True:
                    row = src_file.readline()
                    if not row:
                        break

                    op_infos = row.split()
                    if op_infos[0] == 'total':
                        self._total_time = Decimal(op_infos[2])
                        continue
                    self._op_time_cache[op_infos[0]] = Decimal(op_infos[1])
                    csv_writer.writerow([op_infos[0], op_infos[1]])

    def _parse_aicpu_time(self):
        """Parse the parsed AICPU operator time file."""
        aicpu_file = os.path.join(
            self._profiling_dir,
            self._file_name_aicpu_time.format(self._device_id)
        )
        aicpu_file = validate_and_normalize_path(
            aicpu_file, raise_key="Invaild aicpu file path.")
        if not os.path.isfile(aicpu_file):
            return

        save_file_name = 'aicpu_intermediate_' + self._device_id + '.csv'
        save_file_path = os.path.join(self._profiling_dir, save_file_name)
        with open(aicpu_file, 'r') as src_file:
            row = src_file.readline()
            if not row.startswith('serial_number'):
                return
            _ = src_file.readline()
            with open(save_file_path, 'w') as save_file:
                csv_writer = csv.writer(save_file)
                csv_writer.writerow(self._header_aicpu)

                while True:
                    row = src_file.readline()
                    if not row:
                        break
                    infos = row.split()
                    if infos[0] == 'AI':
                        continue
                    csv_writer.writerow(infos)
