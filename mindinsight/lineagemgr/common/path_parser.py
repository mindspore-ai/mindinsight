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
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.lineagemgr.common.log import logger
from mindinsight.lineagemgr.common.utils import get_timestamp
from mindinsight.utils.exceptions import MindInsightException


class SummaryPathParser:
    """
    Summary path parser.

    This class is a utility class, users can use it to parse summary dir,
    parse summary log path, get the latest lineage summary log, etc.
    """
    LINEAGE_SUMMARY_SUFFIX = '_lineage'
    _LINEAGE_SUMMARY_SUFFIX_LEN = len(LINEAGE_SUMMARY_SUFFIX)

    @staticmethod
    def get_lineage_summaries(summary_dir, is_sorted=False, reverse=True):
        """
        Get lineage summaries according to summary dir.

        Args:
            summary_dir (str): Summary dir.
            is_sorted (bool): If it is True, files will be sorted.
            reverse (bool): If it is True, sort by timestamp increments and filename decrement.

        Returns:
            list, if the lineage summary log exist, return the file names, else return [].
        """
        try:
            summary_watcher = SummaryWatcher()
            summaries = summary_watcher.list_summaries(summary_base_dir=summary_dir)
        except MindInsightException as err:
            logger.warning(str(err))
            return []
        summary_files = [summary.get('file_name') for summary in summaries]
        lineage_files_name = list(filter(
            lambda filename: (filename.endswith(SummaryPathParser.LINEAGE_SUMMARY_SUFFIX)), summary_files))
        if is_sorted:
            lineage_files_name = SummaryPathParser._sorted_summary_files(lineage_files_name, reverse)

        return lineage_files_name

    @staticmethod
    def _sorted_summary_files(summary_files, reverse):
        """Sort by timestamp increments and filename decrement."""
        sorted_files = sorted(summary_files,
                              key=lambda filename: (-get_timestamp(filename), filename),
                              reverse=reverse)
        return sorted_files
