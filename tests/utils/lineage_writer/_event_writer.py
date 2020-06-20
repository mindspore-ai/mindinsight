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
"""Event writer to record lineage message to summary log."""
import os
import stat
import struct

from tests.utils import crc32


class EventWriter:
    """
    Lineage summary record.
    Recording train lineage and evaluation lineage to summary log.

    Args:
        file_path (str): Summary log path.
        override (bool): If override the summary log exist.

    Raises:
        IOError: Write to summary log failed or file_path is a dir.

    Examples:
        >>> content = b'\x01\x02\x03\x04'
        >>> event_writer = EventWriter("./test.log", True)
        >>> event_writer.write_event_to_file(content)
    """
    def __init__(self, file_path, override=False):
        """
        Init EventWriter, get the type of writing.

        Args:
            file_path (str): The file path to writing.
            override (bool): The type of writing.
        """
        if os.path.exists(file_path):
            if not os.path.isfile(file_path):
                raise IOError("The file_path is not a normal file.")

        self.file_path = file_path
        if override:
            self.write_type = 'wb'
        else:
            self.write_type = 'ab'

    def write_event_to_file(self, content):
        """
        Write event to file.

        Args:
            content (bytes): Content to write.
        """
        length = struct.pack("<Q", len(content))
        header_crc = EventWriter.get_crc(length)
        crc = EventWriter.get_crc(content)
        content = length + header_crc + content + crc
        try:
            with open(self.file_path, self.write_type) as log_file:
                os.chmod(self.file_path, stat.S_IRUSR | stat.S_IWUSR)
                log_file.write(content)
        except IOError:
            raise IOError("There are some error when writing summary log.")

    @staticmethod
    def get_crc(content):
        """
        Calculate crc value of the content.

        Args:
            content (bytes): Content to be Calculated.

        Returns:
            bytes, crc of content, 4 bytes.
        """
        crc_value = crc32.get_mask_from_string(content)

        return struct.pack("<L", crc_value)
