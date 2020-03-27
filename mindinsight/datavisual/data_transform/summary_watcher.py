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
"""Summary watcher module."""

import os
import re
import datetime
from pathlib import Path

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.validation import Validation
from mindinsight.utils.exceptions import FileSystemPermissionError


class SummaryWatcher:
    """SummaryWatcher class."""

    SUMMARY_FILENAME_REGEX = r'summary\.(?P<timestamp>\d+)'
    PB_FILENAME_REGEX = r'\.pb$'
    MAX_SUMMARY_DIR_COUNT = 999

    # scan at most 20000 files/directories (approximately 1 seconds)
    # if overall=False in SummaryWatcher.list_summary_directories
    # to avoid long-time blocking
    MAX_SCAN_COUNT = 20000

    def list_summary_directories(self, summary_base_dir, overall=True):
        """
        List summary directories within base directory.

        Args:
            summary_base_dir (str): Path of summary base directory.

        Returns:
            list, list of summary directory info, each of which including the following attributes.
                - relative_path (str): Relative path of summary directory, referring to settings.SUMMARY_BASE_DIR,
                                        starting with "./".
                - create_time (datetime): Creation time of summary file.
                - update_time (datetime): Modification time of summary file.

        Examples:
            >>> from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
            >>> summary_watcher = SummaryWatcher()
            >>> directories = summary_watcher.list_summary_directories('/summary/base/dir')
        """
        if self._contains_null_byte(summary_base_dir=summary_base_dir):
            return []

        if not os.path.exists(summary_base_dir):
            logger.warning('Path of summary base directory not exists.')
            return []

        if not os.path.isdir(summary_base_dir):
            logger.warning('Path of summary base directory is not a valid directory.')
            return []

        summary_dict = {}
        scan_count = 0

        try:
            entries = os.scandir(summary_base_dir)
        except PermissionError:
            logger.error('Path of summary base directory is not accessible.')
            raise FileSystemPermissionError('Path of summary base directory is not accessible.')

        for entry in entries:
            if len(summary_dict) == self.MAX_SUMMARY_DIR_COUNT:
                break
            relative_path = os.path.join('.', '')
            if entry.is_symlink():
                pass
            elif entry.is_file():
                self._update_summary_dict(summary_dict, relative_path, entry)
            elif entry.is_dir():
                full_path = os.path.realpath(os.path.join(summary_base_dir, entry.name))

                try:
                    subdir_entries = os.scandir(full_path)
                except PermissionError:
                    logger.warning('Path of %s under summary base directory is not accessible.', entry.name)
                else:
                    for subdir_entry in subdir_entries:
                        if len(summary_dict) == self.MAX_SUMMARY_DIR_COUNT:
                            break
                        subdir_relative_path = os.path.join('.', entry.name)
                        if subdir_entry.is_symlink():
                            pass
                        elif subdir_entry.is_file():
                            self._update_summary_dict(summary_dict, subdir_relative_path, subdir_entry)

                        scan_count += 1
                        if not overall and scan_count >= self.MAX_SCAN_COUNT:
                            break

            scan_count += 1
            if not overall and scan_count >= self.MAX_SCAN_COUNT:
                logger.info('Stop further scanning due to overall is False and '
                            'number of scanned files exceeds upper limit.')
                break

        directories = [{
            'relative_path': key,
            'create_time': value['ctime'],
            'update_time': value['mtime'],
        } for key, value in summary_dict.items()]

        # sort by update time in descending order and relative path in ascending order
        directories.sort(key=lambda x: (-int(x['update_time'].timestamp()), x['relative_path']))

        return directories

    def _contains_null_byte(self, **kwargs):
        """
        Check if arg contains null byte.

        Args:
            kwargs (Any): Check if arg contains null byte.

        Returns:
            bool, indicates if any arg contains null byte.
        """
        for key, value in kwargs.items():
            if not isinstance(value, str):
                continue
            if '\x00' in value:
                logger.warning('%s contains null byte \\x00.', key)
                return True

        return False

    def _is_valid_summary_directory(self, summary_base_dir, relative_path):
        """
        Check if the given summary directory is valid.

        Args:
            summary_base_dir (str): Path of summary base directory.
            relative_path (str): Relative path of summary directory, referring to summary base directory,
                                starting with "./" .

        Returns:
            bool, indicates if summary directory is valid.
        """
        summary_base_dir = os.path.realpath(summary_base_dir)
        summary_directory = os.path.realpath(os.path.join(summary_base_dir, relative_path))
        if summary_base_dir == summary_directory:
            return True

        if not os.path.exists(summary_directory):
            logger.warning('Path of summary directory not exists.')
            return False

        if not os.path.isdir(summary_directory):
            logger.warning('Path of summary directory is not a valid directory.')
            return False

        try:
            Path(summary_directory).relative_to(Path(summary_base_dir))
        except ValueError:
            logger.warning('Relative path %s is not subdirectory of summary_base_dir', relative_path)
            return False

        return True

    def _update_summary_dict(self, summary_dict, relative_path, entry):
        """
        Update summary_dict with ctime and mtime.

        Args:
            summary_dict (dict): Temporary data structure to hold summary directory info.
            relative_path (str): Relative path of summary directory, referring to summary base directory,
                                starting with "./" .
            entry (DirEntry): Directory entry instance needed to check with regular expression.
        """
        summary_pattern = re.search(self.SUMMARY_FILENAME_REGEX, entry.name)
        pb_pattern = re.search(self.PB_FILENAME_REGEX, entry.name)
        if summary_pattern is None and pb_pattern is None:
            return

        if summary_pattern is not None:
            timestamp = int(summary_pattern.groupdict().get('timestamp'))
            try:
                # extract created time from filename
                ctime = datetime.datetime.fromtimestamp(timestamp).astimezone()
            except OverflowError:
                return
        else:
            ctime = datetime.datetime.fromtimestamp(entry.stat().st_ctime).astimezone()

        # extract modified time from filesystem
        mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime).astimezone()

        if relative_path not in summary_dict or summary_dict[relative_path]['ctime'] < ctime:
            summary_dict[relative_path] = {
                'ctime': ctime,
                'mtime': mtime,
            }

    def is_summary_directory(self, summary_base_dir, relative_path):
        """
        Check if the given summary directory is valid.

        Args:
            summary_base_dir (str): Path of summary base directory.
            relative_path (str): Relative path of summary directory, referring to summary base directory,
                                starting with "./" .

        Returns:
            bool, indicates if the given summary directory is valid.

        Examples:
            >>> from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
            >>> summary_watcher = SummaryWatcher()
            >>> summaries = summary_watcher.is_summary_directory('/summary/base/dir', './job-01')
        """
        if self._contains_null_byte(summary_base_dir=summary_base_dir, relative_path=relative_path):
            return False

        if not self._is_valid_summary_directory(summary_base_dir, relative_path):
            return False

        summary_directory = os.path.realpath(os.path.join(summary_base_dir, relative_path))
        try:
            entries = os.scandir(summary_directory)
        except PermissionError:
            logger.error('Path of summary base directory is not accessible.')
            raise FileSystemPermissionError('Path of summary base directory is not accessible.')

        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                continue
            summary_pattern = re.search(self.SUMMARY_FILENAME_REGEX, entry.name)
            pb_pattern = re.search(self.PB_FILENAME_REGEX, entry.name)
            if summary_pattern or pb_pattern:
                return True

        return False

    def list_summary_directories_by_pagination(self, summary_base_dir, offset=0, limit=10):
        """
        List summary directories within base directory.

        Args:
            summary_base_dir (str): Path of summary base directory.
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1. Default value is 0.
            limit (int): The max data items for per page. Default value is 10.

        Returns:
            tuple[total, directories], total indicates the overall number of summary directories and directories
                    indicate list of summary directory info including the following attributes.
                - relative_path (str): Relative path of summary directory, referring to settings.SUMMARY_BASE_DIR,
                                        starting with "./".
                - create_time (datetime): Creation time of summary file.
                - update_time (datetime): Modification time of summary file.

        Raises:
            ParamValueError, if offset < 0 or limit is out of valid value range.
            ParamTypeError, if offset or limit is not valid integer.

        Examples:
            >>> from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
            >>> summary_watcher = SummaryWatcher()
            >>> total, directories = summary_watcher.list_summary_directories_by_pagination(
                        '/summary/base/dir', offset=0, limit=10)
        """
        offset = Validation.check_offset(offset=offset)
        limit = Validation.check_limit(limit, min_value=1, max_value=999)

        directories = self.list_summary_directories(summary_base_dir, overall=False)
        return len(directories), directories[offset * limit:(offset + 1) * limit]

    def list_summaries(self, summary_base_dir, relative_path='./'):
        """
        Get info of latest summary file within the given summary directory.

        Args:
            summary_base_dir (str): Path of summary base directory.
            relative_path (str): Relative path of summary directory, referring to summary base directory,
                                starting with "./" .

        Returns:
            list, list of summary file including the following attributes.
                - file_name (str): Summary file name.
                - create_time (datetime): Creation time of summary file.
                - update_time (datetime): Modification time of summary file.

        Examples:
            >>> from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
            >>> summary_watcher = SummaryWatcher()
            >>> summaries = summary_watcher.list_summaries('/summary/base/dir', './job-01')
        """
        if self._contains_null_byte(summary_base_dir=summary_base_dir, relative_path=relative_path):
            return []

        if not self._is_valid_summary_directory(summary_base_dir, relative_path):
            return []

        summaries = []
        summary_directory = os.path.realpath(os.path.join(summary_base_dir, relative_path))
        try:
            entries = os.scandir(summary_directory)
        except PermissionError:
            logger.error('Path of summary directory is not accessible.')
            raise FileSystemPermissionError('Path of summary directory is not accessible.')

        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                continue

            pattern = re.search(self.SUMMARY_FILENAME_REGEX, entry.name)
            if pattern is None:
                continue

            timestamp = int(pattern.groupdict().get('timestamp'))
            try:
                # extract created time from filename
                ctime = datetime.datetime.fromtimestamp(timestamp).astimezone()
            except OverflowError:
                continue

            # extract modified time from filesystem
            mtime = datetime.datetime.fromtimestamp(entry.stat().st_mtime).astimezone()

            summaries.append({
                'file_name': entry.name,
                'create_time': ctime,
                'update_time': mtime,
            })

        # sort by update time in descending order and filename in ascending order
        summaries.sort(key=lambda x: (-int(x['update_time'].timestamp()), x['file_name']))

        return summaries
