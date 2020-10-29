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
Image Writer.

This module write scalar into a  csv file.
"""
import os
from urllib.parse import quote

from mindinsight.datavisual.data_transform.summary_parser.writer import Writer


class ImageWriter(Writer):
    """ImageWriter write image into a png file."""
    def __init__(self, file_path):
        """
        Init ImageWriter.

        Args:
            file_path (str): A directory path, e.g. '/output/image/'.
        """
        self._file_path = file_path
        self._image_data = []

    def add(self, value):
        """
        Add value.

        Args:
            value (object): tag and step and image value.
        """
        self._image_data.append(value)

    def write(self):
        """Write file."""
        for i in range(len(self._image_data)):
            tag = quote(self._image_data[i][0], safe="")
            with os.fdopen(os.open("{}/{}_{}.png".format(self._file_path, tag, self._image_data[i][1]),
                                   os.O_WRONLY | os.O_CREAT, 0o600), 'wb') as fp:
                fp.write(self._image_data[i][2])
        self._image_data = []
