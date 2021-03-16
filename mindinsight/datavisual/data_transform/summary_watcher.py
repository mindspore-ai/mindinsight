# Copyright 2020-2021 Huawei Technologies Co., Ltd
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

import json
import os
import re
import datetime
from pathlib import Path

from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.utils.tools import Counter
from mindinsight.datavisual.utils.utils import contains_null_byte
from mindinsight.datavisual.common.exceptions import MaxCountExceededError
from mindinsight.utils.exceptions import FileSystemPermissionError

LINEAGE_SUMMARY_SUFFIX = '_lineage'
EXPLAIN_SUMMARY_SUFFIX = '_explain'


class SummaryWatcher:
    """SummaryWatcher class."""

    SUMMARY_FILENAME_REGEX = r'summary\.(?P<timestamp>\d+)'
    PB_FILENAME_REGEX = r'\.pb$'
    PROFILER_DIRECTORY_REGEX = r'^profiler'
    CLUSTER_PROFILER_DIRECTORY_REGEX = r'^cluster_profiler$'
    MAX_SUMMARY_DIR_COUNT = 999

    # scan at most 20000 files/directories (approximately 1 seconds)
    # if overall is False in SummaryWatcher.list_summary_directories
    # to avoid long-time blocking
    MAX_SCAN_COUNT = 20000

    def list_summary_directories(self, summary_base_dir, overall=True, list_explain=False):
        """
        List summary directories within base directory.

        Args:
            summary_base_dir (str): Path of summary base directory.
            overall (bool): Limit the total num of scanning if overall is False.
            list_explain (bool): Indicates whether to list only the mindexplain folder.
                Default is False, means not to list mindexplain folder.

        Returns:
            list, list of summary directory info, each of which including the following attributes.
                - relative_path (str): Relative path of summary directory, referring to settings.SUMMARY_BASE_DIR,
                                        starting with "./".
                - create_time (datetime): Creation time of summary file.
                - update_time (datetime): Modification time of summary file.
                - profiler (dict): profiler info, including profiler subdirectory path, profiler creation time and
                                    profiler modification time.

        Examples:
            >>> from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
            >>> summary_watcher = SummaryWatcher()
            >>> directories = summary_watcher.list_summary_directories('/summary/base/dir')
        """
        if contains_null_byte(summary_base_dir=summary_base_dir):
            return []

        relative_path = os.path.join('.', '')
        if not self._is_valid_summary_directory(summary_base_dir, relative_path):
            return []

        summary_dict = {}
        counter = Counter(max_count=None if overall else self.MAX_SCAN_COUNT)

        try:
            entries = os.scandir(summary_base_dir)
        except PermissionError:
            logger.error('Path of summary base directory is not accessible.')
            raise FileSystemPermissionError('Path of summary base directory is not accessible.')

        # sort in ascending order according to modification time.
        entries = [entry for entry in entries if not entry.is_symlink()]
        entries = sorted(entries, key=lambda x: x.stat().st_mtime)
        for entry in entries:
            if len(summary_dict) == self.MAX_SUMMARY_DIR_COUNT:
                break
            try:
                counter.add()
            except MaxCountExceededError:
                logger.info('Stop further scanning due to overall is False and '
                            'number of scanned files exceeds upper limit.')
                break
            if entry.is_symlink():
                pass
            elif entry.is_file():
                self._update_summary_dict(summary_dict, summary_base_dir, relative_path, entry, list_explain)
            elif entry.is_dir():
                self._update_summary_dict(summary_dict, summary_base_dir, relative_path, entry, list_explain)
                entry_path = os.path.realpath(os.path.join(summary_base_dir, entry.name))
                self._scan_subdir_entries(summary_dict, summary_base_dir, entry_path, entry.name, counter, list_explain)

        directories = []
        for key, value in summary_dict.items():
            directory = {
                'relative_path': key,
                **value
            }
            directories.append(directory)

        # sort by update time in descending order and relative path in ascending order
        directories.sort(key=lambda x: (-int(x['update_time'].timestamp()), x['relative_path']))

        return directories

    def _scan_subdir_entries(self, summary_dict, summary_base_dir, entry_path, entry_name, counter, list_explain):
        """
        Scan subdir entries.

        Args:
            summary_dict (dict): Temporary data structure to hold summary directory info.
            summary_base_dir (str): Path of summary base directory.
            entry_path(str): Path entry.
            entry_name (str): Name of entry.
            counter (Counter): An instance of CountLimiter.
            list_explain (bool): Indicates whether to list only the mindexplain folder.
        """
        try:
            subdir_entries = os.scandir(entry_path)
        except PermissionError:
            logger.warning('Path of %s under summary base directory is not accessible.', entry_name)
            return

        # sort in ascending order according to modification time.
        subdir_entries = [subdir_entry for subdir_entry in subdir_entries if not subdir_entry.is_symlink()]
        subdir_entries = sorted(subdir_entries, key=lambda x: x.stat().st_mtime)
        for subdir_entry in subdir_entries:
            if len(summary_dict) == self.MAX_SUMMARY_DIR_COUNT:
                break
            try:
                counter.add()
            except MaxCountExceededError:
                logger.info('Stop further scanning due to overall is False and '
                            'number of scanned files exceeds upper limit.')
                break
            subdir_relative_path = os.path.join('.', entry_name)
            if subdir_entry.is_symlink():
                pass
            self._update_summary_dict(summary_dict, summary_base_dir, subdir_relative_path, subdir_entry, list_explain)

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

        if not os.path.exists(summary_directory):
            logger.info('Path of summary directory not exists.')
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

    def _update_summary_dict(self, summary_dict, summary_base_dir, relative_path, entry, list_explain):
        """
        Update summary_dict with ctime and mtime.

        Args:
            summary_dict (dict): Temporary data structure to hold summary directory info.
            summary_base_dir (str): Path of summary base directory.
            relative_path (str): Relative path of summary directory, referring to summary base directory,
                                starting with "./" .
            entry (DirEntry): Directory entry instance needed to check with regular expression.
            list_explain (bool): Indicates whether to list only the mindexplain folder.
        """
        try:
            stat = entry.stat()
        except FileNotFoundError:
            logger.warning('File %s not found', entry.name)
            return

        ctime = datetime.datetime.fromtimestamp(stat.st_ctime).astimezone()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).astimezone()
        if entry.is_file():
            summary_pattern = re.search(self.SUMMARY_FILENAME_REGEX, entry.name)
            pb_pattern = re.search(self.PB_FILENAME_REGEX, entry.name)
            if not self._is_valid_pattern_result(summary_pattern, pb_pattern, list_explain, entry):
                return

            timestamp = None
            if summary_pattern is not None:
                timestamp = int(summary_pattern.groupdict().get('timestamp'))
                try:
                    # extract created time from filename
                    ctime = datetime.datetime.fromtimestamp(timestamp).astimezone()
                except OverflowError:
                    return

            if relative_path not in summary_dict:
                summary_dict[relative_path] = _new_entry(ctime, mtime)
                job_dict = _get_explain_job_info(summary_base_dir, relative_path, timestamp)
                summary_dict[relative_path].update(job_dict)

            if summary_dict[relative_path]['create_time'] < ctime:
                summary_dict[relative_path].update({'create_time': ctime, 'update_time': mtime})
                job_dict = _get_explain_job_info(summary_base_dir, relative_path, timestamp)
                summary_dict[relative_path].update(job_dict)

            if not summary_pattern:
                summary_dict[relative_path]['graph_files'] += 1
            elif entry.name.endswith(LINEAGE_SUMMARY_SUFFIX):
                summary_dict[relative_path]['lineage_files'] += 1
            elif entry.name.endswith(EXPLAIN_SUMMARY_SUFFIX):
                summary_dict[relative_path]['explain_files'] += 1
            else:
                summary_dict[relative_path]['summary_files'] += 1
        elif entry.is_dir():
            if list_explain:
                return

            cluster_profiler_type, is_cluster_profiler = \
                self._find_cluster_profiler_dir(entry, summary_base_dir, relative_path)
            profiler_type, is_profiler = self._find_profiler_dir(entry, summary_base_dir, relative_path)
            if is_cluster_profiler or is_profiler:
                if is_cluster_profiler:
                    profiler_type = cluster_profiler_type

                profiler = {
                    'directory': os.path.join('.', entry.name),
                    'create_time': ctime,
                    'update_time': mtime,
                    "profiler_type": profiler_type
                }

                if relative_path in summary_dict:
                    summary_dict[relative_path]['profiler'] = profiler
                else:
                    summary_dict[relative_path] = _new_entry(ctime, mtime, profiler)

    def _find_profiler_dir(self, entry, summary_base_dir, relative_path):
        """Find profiler dir by the given relative path."""
        profiler_pattern = re.search(self.PROFILER_DIRECTORY_REGEX, entry.name)
        full_dir_path = os.path.join(summary_base_dir, relative_path, entry.name)
        is_valid_profiler_dir, profiler_type = self._is_valid_profiler_directory(full_dir_path)
        if profiler_pattern is None or not is_valid_profiler_dir:
            return profiler_type, False

        return profiler_type, True

    def _find_cluster_profiler_dir(self, entry, summary_base_dir, relative_path):
        """Find profiler cluster dir by the given relative path."""
        cluster_profiler_pattern = re.search(self.CLUSTER_PROFILER_DIRECTORY_REGEX, entry.name)
        full_dir_path = os.path.join(summary_base_dir, relative_path, entry.name)
        is_valid_cluster_profiler_dir, profiler_type = self._is_valid_cluster_profiler_directory(full_dir_path)
        if cluster_profiler_pattern is None or not is_valid_cluster_profiler_dir:
            return profiler_type, False

        return profiler_type, True

    def _is_valid_pattern_result(self, summary_pattern, pb_pattern, list_explain, entry):
        """Check the pattern result is valid."""
        if summary_pattern is None and pb_pattern is None:
            return False
        if list_explain and not entry.name.endswith(EXPLAIN_SUMMARY_SUFFIX):
            return False
        if not list_explain and entry.name.endswith(EXPLAIN_SUMMARY_SUFFIX):
            return False

        return True

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
        if contains_null_byte(summary_base_dir=summary_base_dir, relative_path=relative_path):
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
            if entry.is_symlink():
                continue

            summary_pattern = re.search(self.SUMMARY_FILENAME_REGEX, entry.name)
            if summary_pattern is not None and entry.is_file():
                return True

            pb_pattern = re.search(self.PB_FILENAME_REGEX, entry.name)
            if pb_pattern is not None and entry.is_file():
                return True

            if entry.is_dir():
                profiler_pattern = re.search(self.PROFILER_DIRECTORY_REGEX, entry.name)
                cluster_profiler_pattern = re.search(self.CLUSTER_PROFILER_DIRECTORY_REGEX, entry.name)
                if profiler_pattern is not None or cluster_profiler_pattern is not None:
                    full_path = os.path.realpath(os.path.join(summary_directory, entry.name))
                    if self._is_valid_profiler_directory(full_path)[0] or \
                            self._is_valid_cluster_profiler_directory(full_path)[0]:
                        return True
        return False

    def _is_valid_profiler_directory(self, directory):
        profiler_type = ""
        try:
            from mindinsight.profiler.common.util import analyse_device_list_from_profiler_dir
            device_list, profiler_type = analyse_device_list_from_profiler_dir(directory)
        except ImportError:
            device_list = []

        return bool(device_list), profiler_type

    def _is_valid_cluster_profiler_directory(self, directory):
        """Determine whether it is a valid cluster profiler."""
        cluster_profiler_type = 'cluster'
        entries = os.scandir(directory)
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                full_path = os.path.join(directory, entry.name, 'profiler')
                is_profile, profiler_type = self._is_valid_profiler_directory(full_path)
                if is_profile:
                    return is_profile, cluster_profiler_type + '_' + profiler_type

        return False, cluster_profiler_type

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
        if contains_null_byte(summary_base_dir=summary_base_dir, relative_path=relative_path):
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

            try:
                stat = entry.stat()
            except FileNotFoundError:
                logger.warning('File %s not found.', entry.name)
                continue

            mtime = datetime.datetime.fromtimestamp(stat.st_mtime).astimezone()

            summaries.append({
                'file_name': entry.name,
                'create_time': ctime,
                'update_time': mtime,
            })

        # sort by update time in descending order and filename in ascending order
        summaries.sort(key=lambda x: (-int(x['update_time'].timestamp()), x['file_name']))

        return summaries

    def list_explain_directories(self, summary_base_dir, offset=0, limit=None):
        """
        List explain directories within base directory.

        Args:
            summary_base_dir (str): Path of summary base directory.
            offset (int): An offset for page. Ex, offset is 0, mean current page is 1. Default value is 0.
            limit (int): The max data items for per page. Default value is 10.

        Returns:
            tuple[total, directories], total indicates the overall number of explain directories and directories
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
            >>> total, directories = summary_watcher.list_explain_directories('/summary/base/dir', offset=0, limit=10)
        """
        offset = Validation.check_offset(offset=offset)
        limit = Validation.check_limit(limit, min_value=1, max_value=999, default_value=None)

        directories = self.list_summary_directories(summary_base_dir, overall=False, list_explain=True)
        if limit is None:
            return len(directories), directories

        return len(directories), directories[offset * limit:(offset + 1) * limit]


def _new_entry(ctime, mtime, profiler=None):
    """Create a new entry."""
    return {
        'create_time': ctime,
        'update_time': mtime,
        'summary_files': 0,
        'lineage_files': 0,
        'explain_files': 0,
        'graph_files': 0,
        'profiler': profiler
    }


def _get_explain_job_info(summary_base_dir, relative_path, timestamp):
    """Get explain job info."""
    if timestamp is None:
        job_dict = {"saliency_map": False, "hierarchical_occlusion": False}
        return job_dict

    json_path = os.path.join(summary_base_dir, relative_path.lstrip("./"), f"_explain_{timestamp}",
                             "manifest.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            job_dict = json.load(f)
        return job_dict

    # Set default value to make it compatible with previous version
    job_dict = {"saliency_map": True, "hierarchical_occlusion": False}
    return job_dict
