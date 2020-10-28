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
"""
Scalar Writer.

This module write scalar into a csv file.
"""
import csv
import os

from mindinsight.datavisual.data_transform.summary_parser.writer import Writer


class ScalarWriter(Writer):
    """ScalarWriter write scalar into a  csv file."""
    def __init__(self, file_path):
        """
        Init ScalarWriter.

        Args:
            file_path (str): A directory path, e.g. '/output/'.
        """
        self._file_path = file_path
        self._scalar_data = [("tag", "step", "wall_time (unit: seconds)", "value")]

    def add(self, value):
        """
        Add value.

        Args:
            value (object): wall_time, tag and step and scalar value.
        """
        self._scalar_data.append(value)

    def write(self):
        """Write file."""
        with os.fdopen(os.open('{}/scalar.csv'.format(self._file_path), os.O_WRONLY | os.O_CREAT, 0o600), 'w',
                       encoding='utf-8') as fp:
            writer = csv.writer(fp, dialect='excel')
            writer.writerows(self._scalar_data)
