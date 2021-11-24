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
"""Graph API module."""

import os

from mindinsight.debugger.dump.convert import DumpRootDirConverter, FileMapping
from mindinsight.debugger.dump.parser import Parser
from mindinsight.debugger.stream_cache.data_loader import DataLoader
from mindinsight.domain.graph.query import StackQuery


class DumpParser(Parser):
    """
    Dump Parser.

    Args:
        dump_dir (str): Dump directory path.
    """

    def __init__(self, dump_dir):
        loader = DataLoader(dump_dir)
        super(DumpParser, self).__init__(loader)

    def get_tensor_files(self, qs, use_regex=False, rank_ids=None, iterations=None):
        """
        Get tensor files.

        Args:
            qs (str): Query string.
            use_regex (bool): Indicates if query is regex.
            rank_ids (list): Selected rank IDs.
            iterations (list): Selected iterations.

        Returns:
            dict, paths of tensor files. The format is like: {[op_full_name]: OpPathManager}.
                Call OpPathManager.to_dict(), the result is format like:
                    {'rank_[rank_id]':
                        {[iteration_id]:
                            {
                                'input': list[file_path],
                                'output': list[file_path]
                            }
                        }
                    }
        """
        operators = []
        if rank_ids is None:
            operators = self._operators
        else:
            for operator in self._operators:
                if operator.rank_id in rank_ids:
                    operators.append(operator)

        query = StackQuery(operators)
        operators = query.filter(qs, use_regex=use_regex).all()
        file_paths = {}
        file_mapping = FileMapping(self._loader)
        for operator in operators:
            op_pattern = os.path.basename(operator.full_name)
            res = file_mapping.find_tensor_file(op_pattern, rank_ids=rank_ids, iterations=iterations)
            file_paths[operator.full_name] = res
        return file_paths

    def convert_all_data_to_host(self):
        """
        Convert all data to host format.

        Returns:
            list, failed tensors.
        """
        conversion = DumpRootDirConverter(self._loader)
        failed_lines = conversion.convert()
        return failed_lines
