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
"""This file provides path resolution."""
import os

from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher


class SummaryPathParser:
    """
    Summary path parser.

    This class is a utility class, users can use it to parse summary dir,
    parse summary log path, get the latest lineage summary log, etc.
    """
    LINEAGE_SUMMARY_SUFFIX = '_lineage'
    _LINEAGE_SUMMARY_SUFFIX_LEN = len(LINEAGE_SUMMARY_SUFFIX)

    @staticmethod
    def get_summary_dirs(summary_base_dir):
        """
        Get summary dirs according to summary base dir.

        Args:
            summary_base_dir (str): Summary base dir.

        Returns:
            list[str], all summary dirs in summary base dir. The summary dir is
            absolute path.
        """
        summary_watcher = SummaryWatcher()
        relative_dirs = summary_watcher.list_summary_directories(
            summary_base_dir=summary_base_dir
        )
        summary_dirs = list(
            map(
                lambda item: os.path.realpath(
                    os.path.join(summary_base_dir, item.get('relative_path'))
                ),
                relative_dirs
            )
        )
        return summary_dirs

    @staticmethod
    def get_latest_lineage_summary(summary_dir):
        """
        Get latest lineage summary log path according to summary dir.

        Args:
            summary_dir (str): Summary dir.

        Returns:
            Union[str, None], if the lineage summary log exist, return the path,
            else return None. The lineage summary log path is absolute path.
        """
        summary_watcher = SummaryWatcher()
        summaries = summary_watcher.list_summaries(summary_base_dir=summary_dir)
        latest_file_name = SummaryPathParser._get_latest_lineage_file(summaries)
        return os.path.join(summary_dir, latest_file_name) \
            if latest_file_name is not None else None

    @staticmethod
    def get_latest_lineage_summaries(summary_base_dir):
        """
        Get all latest lineage summary logs in summary base dir.

        Args:
            summary_base_dir (str): Summary base dir.

        Returns:
            list[str], all latest lineage summary logs in summary base dir. The
            lineage summary log is absolute path.
        """
        summary_watcher = SummaryWatcher()
        relative_dirs = summary_watcher.list_summary_directories(
            summary_base_dir=summary_base_dir
        )
        latest_summaries = []
        for item in relative_dirs:
            relative_dir = item.get('relative_path')
            summaries = summary_watcher.list_summaries(
                summary_base_dir=summary_base_dir,
                relative_path=relative_dir
            )
            latest_file_name = SummaryPathParser._get_latest_lineage_file(
                summaries
            )
            if latest_file_name is None:
                continue
            latest_file = os.path.realpath(
                os.path.join(
                    summary_base_dir,
                    relative_dir,
                    latest_file_name
                )
            )
            latest_summaries.append(latest_file)
        return latest_summaries

    @staticmethod
    def _get_latest_lineage_file(summaries):
        """
        Get latest lineage summary file.

        If there is a file with the suffix `LINEAGE_SUMMARY_SUFFIX`, check
        whether there is a file with the same name that does not include the
        suffix `LINEAGE_SUMMARY_SUFFIX`. When both exist, the file is considered
        to be a lineage summary log.

        Args:
            summaries (list[dict]): All summary logs info in summary dir.

        Returns:
            str, the latest lineage summary file name.
        """
        try:
            latest_summary = max(
                summaries,
                key=lambda summary: summary.get('create_time')
            )
        except ValueError:
            return None
        max_create_time = latest_summary.get('create_time')
        summary_file_names = []
        for summary in summaries:
            if summary.get('create_time') == max_create_time:
                summary_file_names.append(summary.get('file_name'))

        latest_lineage_name = None
        for name in summary_file_names:
            if not name.endswith(SummaryPathParser.LINEAGE_SUMMARY_SUFFIX):
                continue
            ms_name = name[:-SummaryPathParser._LINEAGE_SUMMARY_SUFFIX_LEN]
            if ms_name in summary_file_names:
                latest_lineage_name = name
        return latest_lineage_name
