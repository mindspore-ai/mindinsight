# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Debugger train job register."""

import os

from mindinsight.datavisual.common.log import logger
from mindinsight.debugger.common.utils import is_valid_rank_dir_name
from mindinsight.utils.folder_analyzer import FolderAnalyzer


class DebuggerFolderAnalyzer(FolderAnalyzer):
    """Debugger train job register."""
    def analyze(self, entry, summary_base_dir, relative_path):
        """Check dir by debugger register."""
        update_info = {}
        if entry.is_dir():
            sub_relative_path = os.path.join(relative_path, entry.name)
            entry_path = entry.path
            try:
                subdir_entries = os.scandir(entry_path)
            except PermissionError:
                logger.warning('Path of %s under summary base directory is not accessible.', entry.name)
                return update_info
            subdir_entries = [subdir_entry for subdir_entry in subdir_entries if not subdir_entry.is_symlink()]
            subdir_entries = sorted(subdir_entries, key=lambda x: x.stat().st_mtime)
            for subdir_entry in subdir_entries:
                if subdir_entry.is_dir() and is_valid_rank_dir_name(subdir_entry.name) and \
                        os.path.exists(os.path.join(subdir_entry.path, ".dump_metadata")):
                    update_info = {'dump_dir': sub_relative_path}
                    return update_info
        return update_info
