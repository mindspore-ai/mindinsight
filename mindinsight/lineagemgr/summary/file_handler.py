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
"""File handler for lineage summary log."""
import os


class FileHandler:
    """
    Summary log file handler.

    Summary log file handler provides Python APIs to manage file IO, including
    read, seek. It is not suitable for very large files.

    Args:
        file_path (str): File path.
    """

    def __init__(self, file_path):
        self._size = os.path.getsize(file_path)
        self._cache = self._read_cache(file_path)
        self._offset = 0

    @property
    def size(self):
        """
        The size of file.

        Returns:
            int, the size of file.
        """
        return self._size

    def _read_cache(self, file_path):
        """
        Read file in cache.

        Args:
            file_path (str): File path.

        Returns:
            bytes, the file content.
        """
        with open(file_path, 'rb') as log_file:
            return log_file.read()

    def seek(self, offset):
        """
        Set the new offset of file.

        Args:
            pos (int): The new offset.
        """
        self._offset = offset

    def tell(self):
        """
        Tell the current offset.

        Returns:
            int, the offset.
        """
        return self._offset

    def read(self, size=-1, offset=None):
        """
        Read bytes from buffer by size.

        Args:
            size (int): Number of bytes to read. If set -1, read the whole file.
                Default: -1.
            offset (int): The start offset to read bytes from. Default: None.

        Returns:
            bytes, the content.
        """
        if offset is None:
            offset = self._offset

        new_offset = offset + size
        result = self._cache[offset:new_offset]
        self._offset = new_offset

        return result
