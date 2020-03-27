# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Local File System."""
import io
import os

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.utils.tools import to_str
from mindinsight.datavisual.data_access.base_file_system import BaseFileSystem
from mindinsight.datavisual.data_access.base_file_system import StatInfo
from mindinsight.utils.exceptions import PathNotExistError


class LocalFileSystem(BaseFileSystem):
    """Local file system."""

    def list_dir(self, path):
        """
        List directories by path.

        Args:
            path (str): Directory path or file path.

        Returns:
           list[str], directories.
        """
        path = to_str(path)
        if not self.is_dir(path):
            raise exceptions.PathNotDirectoryError("Path is %s." % path)
        return os.listdir(path)

    def is_dir(self, path):
        """
        Determine if it is a directory.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it is a directory path, return True.
        """
        return os.path.isdir(to_str(path))

    def is_file(self, path):
        """
        Determine if it is a file.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it is a file path, return True.
        """
        return os.path.isfile(to_str(path))

    def exists(self, path):
        """
        Determine if it exists.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it exists, return True.
        """
        return os.path.exists(to_str(path))

    def file_stat(self, file_path):
        """
        Get file stat information.

        Args:
            file_path (str): File path.

        Returns:
            Nametuple, the (size, mtime) of file.
        """
        try:
            file_info = os.stat(to_str(file_path))
        except OSError:
            raise PathNotExistError("File %s is not exist." % file_path)
        return StatInfo(size=file_info.st_size, mtime=file_info.st_mtime)

    @staticmethod
    def read_access(file_path):
        """
        Determine if it has read permission.

        Args:
            file_path (str): File path.

        Returns:
            bool, if it has read permission, return True.
        """
        return os.access(to_str(file_path), os.R_OK)

    def join(self, path, *paths):
        """
        Join paths.

        Args:
            path (str): Directory path.
            paths (str): Path or paths.

        Returns:
            str, the joined path.
        """
        return os.path.join(path, *paths)

    @staticmethod
    def read(file_path, binary_mode=False, size=None, offset=None):
        """
        Read file.

        Args:
            file_path (str): File path.
            binary_mode (bool): If true, mode will be 'rb'. Else, 'r'.
            size (int): Size of bytes to read.
            offset (int): Offset of file to read.
        Returns:
            bytes, the content read.
        """
        mode = "rb" if binary_mode else "r"
        encoding = None if binary_mode else "utf8"
        with io.open(file_path, mode, encoding=encoding) as file:
            if offset is not None:
                file.seek(offset)
            if size is not None:
                return file.read(size)

            return file.read()
