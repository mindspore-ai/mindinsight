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
"""File handler for file operations."""
from mindinsight.utils.exceptions import PathNotExistError
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.utils.tools import to_str
from mindinsight.datavisual.data_access.local_file_system import LocalFileSystem

_DEFAULT_BUFFER_SIZE = 24 * 1024 * 1024

# _FILE_SYSTEMS, key: FileProtocolHead, value: FileSystem
_FILE_SYSTEMS = dict()
_FILE_SYSTEMS[""] = LocalFileSystem()


class FileHandler:
    """File handler."""

    def __init__(self, file_path, mode='rb'):
        """
        Init FileHandler.

        Args:
            file_path (str): File path.
            mode (Literal['r', 'rb', 'br', 'w', 'wb', 'bw']): It must be
                in ['r', 'rb', 'br', 'w', 'wb', 'bw'].
        """
        logger.debug("The __init__ method enter, param: file_path=%s"
                     "mode=%s", file_path, mode)

        if mode not in ('r', 'rb', 'br', 'w', 'wb', 'bw'):
            raise ValueError("mode %s is not supported by FileHandler." % mode)

        self._file_path = to_str(file_path)
        self._file_system = self.get_file_system(self._file_path)
        self._buff_chunk_size = _DEFAULT_BUFFER_SIZE
        self._buff = None
        self._buff_offset = 0
        self._offset = 0
        self._binary_mode = 'b' in mode

    @staticmethod
    def get_file_system(path):
        """
        Get file system object from path.

        Args:
            path (str): Directory path or file path.

        Returns:
            BaseFileSystem, a file system object.
        """
        path = to_str(path)
        prefix_index = path.find("://")
        prefix = path[:prefix_index] if prefix_index >= 0 else ""
        file_system = _FILE_SYSTEMS.get(prefix, None)

        if file_system is None:
            raise ValueError("No filesystem can be found for prefix %s" % prefix)
        return file_system

    @staticmethod
    def walk(node, forward=True, onerror=None):
        """
        Traverse path for directory and file tree.

        Read from the buffer first.If there is not enough data in the buffer,
        data will be read from the file system.

        Args:
            node (str): Current path.
            forward (bool): If True, it will return the sub-directories and files in the top-level
                directory first and then iterate the files in the sub-directories. Default: True.
            onerror (Optional[Callable]): If None, it indicates that errors during file traversal
                will be ignored. Default: None.

        Yields:
            Tuple, (node, sub_dirs, files).

        """
        logger.debug("The walk method enter, param: node=%s, "
                     "forward=%s, onerror=%s.", node, forward, type(onerror))

        file_system = FileHandler.get_file_system(node)
        node = to_str(node)
        dirs = []

        try:
            dirs = file_system.list_dir(node)
        except PathNotExistError as err:
            if onerror:
                onerror(err)
            else:
                logger.warning("Get dir list error, dir_path=%s error=%s.", node, str(err))
                return

        sub_dirs, files = [], []
        for item in dirs:
            full_path = file_system.join(node, to_str(item))
            if file_system.is_dir(full_path):
                sub_dirs.append(item)
            else:
                files.append(item)

        result = (node, sub_dirs, files)

        if forward:
            logger.debug("The walk method return, pre result=%s.", result)
            yield result

        for subdir in sub_dirs:
            joined_subdir = file_system.join(node, to_str(subdir))
            for sub_results in FileHandler.walk(joined_subdir, forward, onerror):
                yield sub_results

        if not forward:
            logger.debug("The walk method return, post result=%s.", result)
            yield result

    def read(self, size=None):
        """
        Read bytes from buffer or file by size.

        Args:
            size (Union[None, int]): Number of bytes to read, If set None, read the whole file. Default: None.

        Returns:
            str, a certain number of bytes.
        """
        if size is None:
            result = self._file_system.read(self._file_path, self._binary_mode)
            self._offset = len(result)
            return result

        result = None
        if self._buff and len(self._buff) > self._buff_offset:
            read_offset = self._buff_offset + size if size is not None else len(self._buff)
            result = self._read_buffer_by_offset(read_offset)
            if size is not None:
                if len(result) == size:
                    return result
                size -= len(result)

        read_size = max(self._buff_chunk_size, size) if size is not None else None
        self._buff = self._file_system.read(self._file_path, self._binary_mode,
                                            read_size, self._offset)
        self._buff_offset = 0

        read_offset = size if size is not None else len(self._buff)
        chunk = self._read_buffer_by_offset(read_offset)

        result = result + chunk if result else chunk

        return result

    def _read_buffer_by_offset(self, new_buff_offset):
        """
        Read buffer by offset.

        Args:
            new_buff_offset (int): Ending offset to read.

        Returns:
            str, bytes from old offset to new offset.

        """
        old_buff_offset = self._buff_offset
        read_size = min(len(self._buff), new_buff_offset) - old_buff_offset
        self._offset += read_size
        self._buff_offset += read_size
        return self._buff[old_buff_offset:old_buff_offset + read_size]

    def reset_offset(self, offset):
        """
        Reset offset and buff_offset, clean buff.

        Args:
            offset (int): Offset.

        """
        self._offset = offset
        self._buff = None
        self._buff_offset = 0

    @staticmethod
    def list_dir(path):
        """
        List directories by path.

        Args:
            path (str): Directory path or file path.

        Returns:
            list[str], directories.
        """
        file_system = FileHandler.get_file_system(path)
        return file_system.list_dir(path)

    @staticmethod
    def is_dir(path):
        """
        Determine if it is a directory.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it is a directory path, return True.
        """
        file_system = FileHandler.get_file_system(path)
        return file_system.is_dir(path)

    @staticmethod
    def is_file(path):
        """
        Determine if it is a file.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it is a file path, return True.
        """
        file_system = FileHandler.get_file_system(path)
        return file_system.is_file(path)

    @staticmethod
    def exists(path):
        """
        Determine if it exists.

        Args:
            path (str): Directory path or file path.

        Returns:
            bool, if it exists, return True.
        """
        file_system = FileHandler.get_file_system(path)
        return file_system.exists(path)

    @staticmethod
    def file_stat(file_path):
        """
        Get file stat information.

        Args:
            file_path (str): File path.

        Returns:
            Nametuple, the (size, mtime) of file.
        """
        file_system = FileHandler.get_file_system(file_path)
        return file_system.file_stat(file_path)

    @staticmethod
    def join(path, *paths):
        """
        Join paths.

        Args:
            path (str): Directory path.
            paths (str): Path or paths.

        Returns:
            str, the joined path.
        """
        file_system = FileHandler.get_file_system(path)
        return file_system.join(path, *paths)

    @property
    def offset(self):
        """Get offset."""
        return self._offset

    @property
    def file_path(self):
        """Get file path."""
        return self._file_path
