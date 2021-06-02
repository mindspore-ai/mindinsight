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
import stat
import datetime

from mindinsight.debugger.stream_cache.data_loader import DataLoader
from mindinsight.debugger.dump.convert import DumpRootDirConverter, FileMapping
from mindinsight.domain.graph.pb_parser import PBParser
from mindinsight.domain.graph.query import StackQuery
from mindinsight.domain.graph.utils import Toolkit


class DumpParser:
    """
    Dump Parser.

    Args:
        dump_dir (str): Dump directory path.
    """

    def __init__(self, dump_dir):
        self._dump_dir = os.path.realpath(dump_dir)
        self._loader = DataLoader(self._dump_dir)
        self._constants = []
        self._parameters = []
        self._operators = []
        self._parse()

    def _parse(self):
        """Parse dump graph files."""
        graphs = self._loader.load_graphs()
        for graph in graphs:
            rank_id = graph['rank_id']
            graph_protos = graph['graph_protos']
            for graph_data in graph_protos:
                parser = PBParser(graph_data=graph_data)
                parser.parse()

                for constant in parser.constants:
                    constant.graph_name = graph_data.name
                    constant.rank_id = rank_id
                self._constants += parser.constants

                for parameter in parser.parameters:
                    parameter.graph_name = graph_data.name
                    parameter.rank_id = rank_id
                self._parameters += parser.parameters

                for operator in parser.operators:
                    operator.graph_name = graph_data.name
                    operator.rank_id = rank_id
                self._operators += parser.operators

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

    def export_xlsx(self, output_dir=None):
        """
        Export to excel file.

        Args:
            output_dir (str): Output directory to save the excel file. Default is None.

        Returns:
            str, excel file path.
        """
        if output_dir is None:
            output_dir = os.getcwd()
        else:
            output_dir = os.path.realpath(output_dir)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, mode=stat.S_IRUSR | stat.S_IXUSR, exist_ok=True)

        toolkit = Toolkit(
            dump_dir=self._dump_dir,
            constants=self._constants,
            parameters=self._parameters,
            operators=self._operators)

        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(output_dir, f'dump_{timestamp}.xlsx')
        toolkit.export_xlsx(file_path)
        return file_path
