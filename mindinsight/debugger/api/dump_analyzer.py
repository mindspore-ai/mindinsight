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
# ==============================================================================
"""Debugger python API."""
import os.path
from typing import Iterable
import csv
import stat
from pathlib import Path
import numpy as np

import mindinsight
from mindinsight.debugger.api.conditions import WatchpointHit, HitDetail, WatchpointHandle, WatchpointHitImpl
from mindinsight.debugger.api.debugger_engine import DebuggerEngine
from mindinsight.debugger.api.debugger_tensor import DebuggerTensor, DebuggerTensorImpl
from mindinsight.debugger.api.node import Node, NodeImpl, NodeUniqueId
from mindinsight.debugger.api.statistic import TensorStatistic, SummaryStatistic
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.log import setup_logger
from mindinsight.debugger.common.utils import (
    validate_type, validate_slots, parse_param_to_iterable_obj
)
from mindinsight.common.util import version_match
from mindinsight.debugger.dump.parser import DebuggerParser
from mindinsight.debugger.stream_cache.data_loader import DataLoader
from mindinsight.domain.graph.base import NodeType
from mindinsight.domain.graph.query import construct_filter_func
from mindinsight.utils.exceptions import VersionNotMatchError


class DumpAnalyzer:
    """
    Analyzer to inspect the dump data.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        dump_dir (str): The path of the dump folder.
        mem_limit (int, optional): The memory limit for checking watchpoints in MB.
            Optional values: from 2048 MB to 2147483647 MB. ``None`` means no limit is set,
            only limited by computor memory. Default: ``None``.

    Supported Platforms:
        ``Ascend`` ``GPU``

    Examples:
            >>> from mindinsight.debugger import DumpAnalyzer
            >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
    """

    def __init__(self, dump_dir, mem_limit=None):
        self._dump_dir = os.path.realpath(dump_dir)
        self._mem_limit = 0 if mem_limit is None else mem_limit
        self._data_loader = None
        self._debuger_engine = None
        self._parser = None
        # the key is rank_id, the value is <tensor_feature, TensorImpl> map
        self._nodes = {}
        self._initialize()

    def _initialize(self):
        """Initialize."""
        self._validate_mem_limit(self._mem_limit)
        self._data_loader = DataLoader(self._dump_dir)
        self._debugger_engine = DebuggerEngine(self._data_loader, self._mem_limit)
        self._check_version()
        self._parse()

    @staticmethod
    def _validate_mem_limit(mem_limit):
        """Validate memory limit."""
        validate_type(mem_limit, 'mem_limit', int, 'int or None')
        # The unit is MB, from 2G to max value of int32 MB
        min_limit_value = 2 * 1024
        max_limit_value = 2147483647
        if mem_limit and mem_limit < min_limit_value or mem_limit > max_limit_value:
            msg = f"If mem_limit is not None, it should be set in [{min_limit_value}, {max_limit_value}]."
            raise DebuggerParamValueError(msg)

    def _check_version(self):
        """Check version."""
        dbg_services_module = self._debugger_engine.dbg_services_module
        console = setup_logger('debugger', 'console', console=True, logfile=False, formatter='%(message)s')
        ms_version = dbg_services_module.get_version()
        mi_version = mindinsight.__version__
        version_match_stat = version_match(ms_version, mi_version)
        if version_match_stat > 1:
            raise VersionNotMatchError(f"[WARNING] Current version of MindSpore({ms_version}) "
                                       f"is not compatible with MindInsight({mi_version}). "
                                       f"Otherwise some functions might not "
                                       f"work or even raise error. Please make MindSpore "
                                       f"version equal to MindInsight`s.")
        if version_match_stat == 1:
            console.warning("[WARNING] Current version of MindSpore(%s) "
                            "is not completely compatible with MindInsight(%s). "
                            "Otherwise some functions might not work.", ms_version, mi_version)

        config_json = self._data_loader.get_config_json_data()
        ms_data_version = config_json.get("ms_version", None)
        data_match_stat = version_match(ms_data_version, mi_version)
        if data_match_stat > 0:
            console.warning("[WARNING] The summary data under the `dump_dir` from MindSpore(%s) "
                            "which the version should be equal to MindInsight`s(%s) . "
                            "Otherwise some functions might not "
                            "work or even raise error.", ms_data_version, mi_version)

    def _parse(self):
        """Parse graph into nodes and tensors."""

        def _add_node_impl(base_nodes, node_type, nodes):
            nonlocal id_to_name_map
            for b_node in base_nodes:
                new_node = NodeImpl(b_node, node_type)
                new_node.debugger_engine = self._debugger_engine
                nodes[new_node.rank][new_node.unique_id] = new_node
                id_to_name_map[new_node.rank][(b_node.graph_name, b_node.name)] = new_node.name

        def _update_node_list(node_list, dst_id, cur_node, cur_node_map):
            nonlocal id_to_name_map
            dst_node_name = id_to_name_map[cur_node.rank].get(dst_id)
            if not dst_node_name:
                log.info("Failed to find %s in id_to_name_map", dst_id)
                return
            unique_id = NodeUniqueId(name=dst_node_name,
                                     rank=cur_node.rank, graph_name=cur_node.graph_name)
            target_node = cur_node_map.get(unique_id)
            if not target_node:
                log.error("Failed to find %s in node_map", unique_id)
                return
            node_list.append(target_node)

        self._parser = DebuggerParser(self._data_loader)
        ranks = self.get_ranks()
        # the key is rank_id, the value is <node_unique_id, NodeImpl> map
        self._nodes = {rank_id: {} for rank_id in ranks}
        id_to_name_map = {rank_id: {} for rank_id in ranks}
        _add_node_impl(self._parser.constants, NodeType.CONSTANT, self._nodes)
        _add_node_impl(self._parser.parameters, NodeType.PARAMETER, self._nodes)
        _add_node_impl(self._parser.operators, NodeType.OPERATOR, self._nodes)
        # update input and output nodes
        for node_map in self._nodes.values():
            for node in node_map.values():
                base_node = node.base_node
                if hasattr(base_node, 'inputs'):
                    # parameter or const node has no inputs
                    for node_input in base_node.inputs:
                        _update_node_list(node.input_nodes, (base_node.graph_name, node_input.name), node, node_map)

        for node_map in self._nodes.values():
            for node in node_map.values():
                for node_input in node.input_nodes:
                    node_input.downstream.append(node)

    def export_graphs(self, output_dir=None):
        """
        Export the computational graph(s) in xlsx file(s) to the `output_dir` .

        The file(s) will contain the stack info of graph nodes.

        Args:
            output_dir (str, optional): Output directory to save the file.
                ``None`` means to use the current working directory. Default: ``None``.

        Returns:
            str, The path of the generated file.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> res = my_run.export_graphs()
        """
        return self._parser.export_xlsx(output_dir)

    def select_nodes(
            self,
            query_string,
            use_regex=False,
            select_by="node_name",
            ranks=None,
            case_sensitive=True) -> Iterable[Node]:
        """
        Select nodes.

        Select the matched nodes in the computational graph according to the
        query_string. The nodes can be matched by "node_name" or "code_stack",
        see the parameters for detail.

        Args:
            query_string (str): Query string. For a node to be selected, the
                match target field must contains or matches the query string.
            use_regex (bool, optional): Indicates whether query is a regex. Default:
                ``False``.
            select_by (str, optional): The field to search when selecting
                nodes. Available values are ``"node_name"``, ``"code_stack"``.
                ``"node_name"`` means to search the name of the nodes in the
                graph. ``"code_stack"`` means the stack info of
                the node. Default: ``"node_name"``.
            ranks (Union[int, list[int], None], optional): The rank(s) to select. ``None`` means all ranks will be
                considered. The selected nodes must exist on the specified ranks. Default: ``None``.
            case_sensitive (bool, optional): Whether case-sensitive when
                selecting tensors. Default: ``True``.

        Returns:
            Iterable[Node], the matched nodes.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> nodes = my_run.select_nodes("Conv2D-op13")
        """
        validate_type(query_string, 'query_string', str, 'str')
        validate_type(use_regex, 'use_regex', bool, 'bool')
        validate_type(case_sensitive, 'case_sensitive', bool, 'bool')
        node_filter_func = self._get_filter_func(select_by)
        ranks = self._get_iterable_ranks(ranks)

        query_filter_func = construct_filter_func(query_string, case_sensitive, use_regex)
        nodes = []
        for rank_id in ranks:
            for node in self._nodes.get(rank_id, {}).values():
                if node_filter_func(node, query_filter_func):
                    nodes.append(node.copy())
        return nodes

    @staticmethod
    def _match_name(node, filter_func):
        """Check if name matched."""
        return filter_func(node.name)

    @staticmethod
    def _match_stack(node, filter_func):
        """Check if stack matched."""
        for res in map(filter_func, node.stack):
            if res:
                return True
        return False

    @staticmethod
    def _get_filter_func(select_by):
        """Get filter function."""
        if select_by == 'node_name':
            return DumpAnalyzer._match_name
        if select_by == 'code_stack':
            return DumpAnalyzer._match_stack
        raise DebuggerParamValueError(
            "The param `select_by` only support `node_name` or `code_stack`.")

    def select_tensors(
            self,
            query_string,
            use_regex=False,
            select_by="node_name",
            iterations=None,
            ranks=None,
            slots=None,
            case_sensitive=True) -> Iterable[DebuggerTensor]:
        """
        Select tensors.

        Select the matched tensors in the directory according to the
        sepicified filter condition, see the parameters for detail.

        Args:
            query_string (str): Query string. For a tensor to be selected, the
                match target field must contain or match the query string.
            use_regex (bool, optional): Indicates whether query is a regex. Default:
                ``False``.
            select_by (str, optional): The field to search when selecting
                tensors. Available values are ``"node_name"``, ``"code_stack"``.
                ``"node_name"`` means to search the node name of the tensors in the
                graph. ``"code_stack"`` means the stack info of
                the node that outputs this tensor. Default: ``"node_name"``.
            iterations (Union[int, list[int], None], optional): The iteration(s) to select. ``None`` means all dumped
                iterations will be selected. Default: ``None``.
            ranks (Union[int, list[int], None], optional): The rank(s) to select. ``None`` means all ranks
                will be selected. Default: ``None``.
            slots (list[int], optional): The slot of the selected tensor. ``None`` means all slots will be selected.
                Default: ``None``.
            case_sensitive (bool, optional): Whether case-sensitive when selecting tensors. Default: ``True``.

        Returns:
          Iterable[DebuggerTensor], the matched tensors.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = my_run.select_tensors("Conv2D-op13")
        """
        validate_type(query_string, 'query_string', str, 'str')
        validate_type(use_regex, 'use_regex', bool, 'bool')
        validate_type(case_sensitive, 'case_sensitive', bool, 'bool')
        validate_slots(slots)
        node_filter_func = self._get_filter_func(select_by)
        ranks = self._get_iterable_ranks(ranks)
        dumped_iterations = self.get_iterations(ranks)
        iterations = parse_param_to_iterable_obj(iterations, 'iterations', dumped_iterations)

        tensors = []
        query_filter_func = construct_filter_func(query_string, case_sensitive, use_regex)
        for rank_id in ranks:
            for node in self._nodes.get(rank_id, {}).values():
                if node_filter_func(node, query_filter_func):
                    tensors.extend(node.get_output_tensors(slots=slots, iterations=iterations))
        return tensors

    def select_tensor_statistics(
            self,
            iterations=None,
            ranks=None):
        """
        Select tensor statistics.

        Select the matched tensor statistics in the directory according to the
        sepicified filter condition, see the parameters for detail.

        Args:
            iterations (Union[int, list[int], None], optional): The iteration(s) to select. ``None`` means all dumped
                iterations will be selected. Default: ``None``.
            ranks (Union[int, list[int], None], optional): The rank(s) to select. ``None`` means all ranks
                will be selected. Default: ``None``.

        Returns:
            Dict[TensorStatistic], the matched TensorStatistics. The format is as below.

            .. code-block::

                {
                "rank_id":
                    {
                    "iteration_id":
                        {
                        "tensor_name":
                            [TensorStatistic],
                        ...
                        }
                    }
                ...
                }

        Examples:
            >>> from mindinsight.debugger import DumpAnalyzer
            >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
            >>> statistics = my_run.select_tensor_statistics(ranks=[0])
        """
        ranks = self._get_iterable_ranks(ranks)
        dumped_iterations = self.get_iterations(ranks)
        iterations = parse_param_to_iterable_obj(iterations, 'iterations', dumped_iterations)

        tensor_statistics = {}
        for rank_id in ranks:
            static_in_rank = {}
            for iteration_id in self.get_iterations(ranks=[rank_id]):
                if iteration_id not in iterations:
                    continue
                tensor_statistic = self._get_statistic(rank_id=rank_id, iteration_id=iteration_id)
                static_in_rank[iteration_id] = tensor_statistic
            tensor_statistics[rank_id] = static_in_rank
        return tensor_statistics

    def _get_statistic(self, rank_id, iteration_id):
        """
        Get the TensorStatic of the corresponding rank and iteration.
        """
        tensor_statistics = {}
        if not self._data_loader.has_data:
            return tensor_statistics
        net_name = self._data_loader.get_net_name()
        net_dir = Path(os.path.join(self._dump_dir, 'rank_' + str(rank_id), net_name)).absolute()
        for graph_dir in net_dir.iterdir():
            target_step_dir = graph_dir / str(iteration_id)
            if not target_step_dir.is_dir():
                continue
            statistic_file_path = os.path.join(target_step_dir, "statistic.csv")
            with open(statistic_file_path, 'r') as f:
                csv_reader = csv.DictReader(f)
                # The first line of the csv file is the title, so skip the first line.
                for statistic_line in csv_reader:
                    tensor_name = statistic_line.get('Op Name') + ':' + statistic_line.get(
                        'IO') + ':' + statistic_line.get('Slot')
                    statistics_for_specified_name = tensor_statistics.get(tensor_name, [])
                    statistics_for_specified_name.append(statistic_line)
                    tensor_statistics.update({tensor_name: statistics_for_specified_name})
        return tensor_statistics

    def _compute_statistics(self, debugger_tensors):
        """
        Compute the statistic of the given tensors.

        Args:
            debugger_tensors(Iterable[DebuggerTensor]): The given DebuggerTensors.

        Returns:
            Dict[TensorStatistic], the computed TensorStatistics. The format is as below.

            .. code-block::

                {"rank_id":{
                    "iteration_id":
                        {
                        "tensor_name":
                            [TensorStatistic],
                        ...
                        }
                    }
                ...
                }
        """
        statistics = {}
        for tensor in debugger_tensors:
            rank_id = tensor.rank
            is_new_rank = rank_id not in statistics
            static_in_rank = statistics.get(rank_id, {})
            iteration = tensor.iteration
            is_new_iteration = iteration not in static_in_rank
            static_in_iter = static_in_rank.get(iteration, {})
            single_static = self._compute_statistic(tensor)
            tensor_name = single_static.op_name + ':' + single_static.io + ':' + str(single_static.slot)
            statistics_for_specified_name = static_in_iter.get(tensor_name, [])
            statistics_for_specified_name.append(single_static)
            static_in_iter.update({tensor_name: statistics_for_specified_name})
            if is_new_iteration:
                static_in_rank[iteration] = static_in_iter
            if is_new_rank:
                statistics[rank_id] = static_in_rank
        return statistics

    def _compute_statistic(self, debugger_tensor):
        """Compute the tensor statistic for one tensor."""
        statistic = TensorStatistic()
        op_name = debugger_tensor.node.name
        tensor_value = debugger_tensor.value()
        if tensor_value is None:
            return statistic
        short_name = op_name.split('/')[-1]
        op_type = short_name.split('-')[0]
        statistic.op_name = short_name
        statistic.op_type = op_type
        statistic.io = 'output'
        statistic.slot = debugger_tensor.slot
        statistic.data_size = tensor_value.nbytes
        statistic.data_type = tensor_value.dtype
        statistic.shape = tensor_value.shape
        statistic.min_value = np.amin(tensor_value)
        statistic.max_value = np.amax(tensor_value)
        statistic.avg_value = tensor_value.mean()
        statistic.count = tensor_value.size
        statistic.negative_zero_count = np.sum(np.where(tensor_value == 0, 1, 0))
        statistic.positive_zero_count = np.sum(np.where(tensor_value == 0, 1, 0))
        statistic.negative_inf_count = len(np.nonzero(np.isneginf(tensor_value))[0])
        statistic.positive_inf_count = len(np.nonzero(np.isposinf(tensor_value))[0])
        statistic.nan_count = len(np.nonzero(np.isnan(tensor_value))[0])
        return statistic

    def summary_statistics(self, statistics, overflow_value=65500, out_path="./"):
        """
        Summary the statistics in the different ranks and iterations.

        Args:
            statistics(Dict[TensorStatistic]): The given TensorStatistic. They can be the return value of
                `compute_statistic` or `select_tensor_statistics`.
            overflow_value(int, optional): The given overflow threshold, default: ``65500``.
            out_path(str, optional): The given output directory to save the statistics. Default: ``"./"``.
        """
        summary_statistics = {}
        for rank_id, statistics_in_rank in statistics.items():
            log.warning("process statistics in rank, rank_id is: %s", rank_id)
            for iteration_id, statistics_in_iteration in statistics_in_rank.items():
                log.warning("process statistics in iteration, iteration_id is: %s", iteration_id)
                for tensor_name, statistics_for_name in statistics_in_iteration.items():
                    for statistic in statistics_for_name:
                        if isinstance(statistic, TensorStatistic):
                            self._put_tensor_statistic_to_summarystatistics(statistic, summary_statistics,
                                                                            overflow_value)
                        else:
                            self._put_dict_statistic_to_summarystatistics(statistic, summary_statistics, overflow_value)
                    summary_statistic = summary_statistics.get(tensor_name, SummaryStatistic())
                    summary_statistic.total_iterations += 1
        self._export_to_disk(summary_statistics, out_path)

    def _put_dict_statistic_to_summarystatistics(self, statistic, summary_statistics, overflow_value=65500):
        """Put dict_statistic to summarized statistics, used for Statistic of dict type from statistic file."""
        op_name = statistic.get('Op Name', 'unkown')
        op_type = statistic.get('Op Type', 'unkown')
        io = statistic.get('IO', 'output')
        slot = statistic.get('Slot', 0)
        tensor_name = op_name + ":" + io + ":" + str(slot)
        positive_inf_count = statistic.get('Positive Inf Count', 0)
        negative_inf_count = statistic.get('Negative Inf Count', 0)
        nan_count = statistic.get('NaN Count', 0)
        min_value = statistic.get('Min Value', 0)
        max_value = statistic.get('Max Value', 0)
        has_out_of_range = False
        summary_statistic = summary_statistics.get(tensor_name, SummaryStatistic())
        if not summary_statistic.op_type:
            summary_statistic.op_type = op_type
        if not summary_statistic.op_name:
            summary_statistic.op_name = op_name
        if not summary_statistic.tensor_name:
            summary_statistic.tensor_name = tensor_name
            summary_statistics[tensor_name] = summary_statistic
        summary_statistic.total_number += 1
        if int(positive_inf_count) > 0 or int(negative_inf_count) > 0:
            summary_statistic.inf_number += 1
        if int(nan_count) > 0:
            summary_statistic.nan_number += 1
        if abs(float(min_value)) > overflow_value or abs(float(max_value)) > overflow_value:
            summary_statistic.out_of_range_number += 1
            has_out_of_range = True
        if int(positive_inf_count) == 0 and int(negative_inf_count) == 0 and int(
                nan_count) == 0 and not has_out_of_range:
            summary_statistic.none_overflow_number += 1

    def _put_tensor_statistic_to_summarystatistics(self, statistic, summary_statistics, overflow_value=65500):
        """Put tensor_statistic to summarized statistics, used for TensorStatistic from tensor file."""
        op_name = statistic.op_name
        op_type = statistic.op_type
        io = statistic.io
        slot = statistic.slot
        min_value = statistic.min_value
        max_value = statistic.max_value
        has_out_of_range = False
        tensor_name = op_name + ":" + io + ":" + str(slot)
        summary_statistic = summary_statistics.get(tensor_name, SummaryStatistic())
        if not summary_statistic.op_type:
            summary_statistic.op_type = op_type
        if not summary_statistic.op_name:
            summary_statistic.op_name = op_name
        if not summary_statistic.tensor_name:
            summary_statistic.tensor_name = tensor_name
            summary_statistics[tensor_name] = summary_statistic
        summary_statistic.total_number += 1
        if statistic.positive_inf_count > 0 or statistic.negative_inf_count > 0:
            summary_statistic.inf_number += 1
        if statistic.nan_count > 0:
            summary_statistic.nan_number += 1
        if abs(min_value) > overflow_value or abs(max_value) > overflow_value:
            summary_statistic.out_of_range_number += 1
            has_out_of_range = True
        if statistic.positive_inf_count == 0 and statistic.negative_inf_count == 0 and statistic.nan_count == 0 and \
                not has_out_of_range:
            summary_statistic.none_overflow_number += 1

    def _export_to_disk(self, tensor_statistics, out_path="./"):
        """
        Export the tensor staticstics to the out_path.

        Args:
            tensor_statistics(Union[Dict[TensorStatistic], Dict[SummaryStatistic]]): The given Statistics.
                They can be the return value of `compute_statistic` or `summary_statistics`.
            out_path(str, optional): The given output directory to save the statistics. Default: ``"./"``.

        """
        ks = tensor_statistics.keys()
        if not ks:
            log.warning("The given tensor_statistics is empty.")
            return
        if not os.path.exists(out_path):
            os.makedirs(out_path, exist_ok=True)
        if isinstance(list(ks)[0], int):
            for rank_id, statistics_in_rank in tensor_statistics.items():
                for iteration_id, statistics_in_iteration in statistics_in_rank.items():
                    self._export_statistics_in_one_iteration(statistics_in_iteration, rank_id, iteration_id, out_path)
        elif isinstance(list(ks)[0], str):
            self._export_summary_statistics(tensor_statistics, out_path)
        else:
            log.warning("Invalid tensor_statistics data structure.")

    def _export_summary_statistics(self, tensor_statistics, out_path):
        """Export the summarized statistics to out_path."""
        statistic_file_path = os.path.join(out_path, "statistics_summary.csv")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(statistic_file_path, flags, modes), 'w', newline='') as f:
            csv_writer = csv.writer(f)
            statistic_header = ["op_type", "op_name", "tensor_name", "inf_number", "nan_number",
                                "out_of_range_number", "total_number", "none_overflow_number", "total_iterations"]
            csv_writer.writerow(statistic_header)
            for _, statistic in tensor_statistics.items():
                statistic_line = [statistic.op_type, statistic.op_name, statistic.tensor_name,
                                  statistic.inf_number, statistic.nan_number, statistic.out_of_range_number,
                                  statistic.total_number, statistic.none_overflow_number, statistic.total_iterations]
                csv_writer.writerow(statistic_line)
        log.info("export summarised statistics to file: %s", statistic_file_path)

    def _export_statistics_in_one_iteration(self, tensor_statistics_in_one_iteration, rank_id, iteration_id, out_path):
        """Export tensor_statistics in one iteration."""
        iteration_path = os.path.join(out_path, str(rank_id), str(iteration_id))
        if not os.path.exists(iteration_path):
            os.makedirs(iteration_path, exist_ok=True)
        statistic_file_path = os.path.join(iteration_path, "statistics.csv")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        modes = stat.S_IWUSR | stat.S_IRUSR
        with os.fdopen(os.open(statistic_file_path, flags, modes), 'w', newline='') as f:
            csv_writer = csv.writer(f)
            statistic_header = ["Op Type", "Op Name", "Task ID", "Stream ID", "Timestamp", "IO", "Slot", "Data Size",
                                "Data Type", "Shape", "Max Value", "Min Value", "Avg Value", "Count",
                                "Negative Zero Count", "Positive Zero Count", "NaN Count", "Negative Inf Count",
                                "Positive Inf Count", "Zero Count"]
            csv_writer.writerow(statistic_header)
            for statistic in tensor_statistics_in_one_iteration:
                statistic_line = [statistic.op_type, statistic.op_name, statistic.task_id,
                                  statistic.stream_id, statistic.time_stamp, statistic.io, statistic.slot,
                                  statistic.data_size, statistic.data_type, statistic.shape, statistic.max_value,
                                  statistic.min_value, statistic.avg_value, statistic.count,
                                  statistic.negative_zero_count, statistic.positive_zero_count, statistic.nan_count,
                                  statistic.negative_inf_count, statistic.positive_inf_count, statistic.zero_count]
                csv_writer.writerow(statistic_line)
        log.info("export summarised statistics to file: %s", statistic_file_path)

    def get_iterations(self, ranks=None) -> Iterable[int]:
        """
        Get available iterations which have data dumped in this run.

        Args:
            ranks (Union[int, list[int], None], optional): The rank(s) to select.
                Get available iterations which are under the specified ranks.
                The ranks refers to the number of devices to be used starting from 0
                when running distributed training. This number is called rank.
                For example, for an 8-card computer, only 4-7 cards are used for
                specified training, so 4-7 cards correspond to the ranks 0-3 respectively..
                If ``None``, return iterations of all ranks. Default: ``None``.

        Returns:
            Iterable[int], available iterations which have dumped data, sorted in increasing order.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> iterations = my_run.get_iterations()
                >>> print(list(iterations))
                [0]
        """
        total_dumped_steps = self._data_loader.load_dumped_step()
        ranks = self._get_iterable_ranks(ranks)
        iterations = set()
        for rank_id in ranks:
            for iters_per_graph in total_dumped_steps.get(rank_id, {}).values():
                iterations.update(iters_per_graph)
        res = list(iterations)
        res.sort()
        return res

    def get_ranks(self) -> Iterable[int]:
        """
        Get the available ranks in this run.

        Returns:
            Iterable[int], the list of rank id in current dump directory.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> ranks = my_run.get_ranks()
                >>> print(list(ranks))
                [0]
        """
        return [rank_dir.rank_id for rank_dir in self._data_loader.rank_dirs]

    def check_watchpoints(
            self,
            watchpoints,
            error_on_no_value=False) -> Iterable[WatchpointHit]:
        """
        Check the given watchpoints in a batch.

        Note:
            1. For speed, all watchpoints for the iteration should be given at
            the same time to avoid reading tensors len(watchpoints) times.

            2. The `check_watchpoints` function start a new process when it is called, needs to be
            called in `if __name__ == '__main__'` .

        Args:
            watchpoints (Iterable[Watchpoint]): The list of watchpoints.
            error_on_no_value (bool, optional): Whether to report error code in watchpoint
                hit when the specified tensor have no value stored in
                dump_dir. Default: ``False``.

        Returns:
            Iterable[WatchpointHit], the watchpoint hit list, sorted by tensor drop time.


        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> from mindinsight.debugger import (TensorTooLargeCondition,
                ...                                    Watchpoint)
                >>>
                >>> def test_watchpoints():
                ...     my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                ...     tensors = my_run.select_tensors(
                ...                                         query_string="Conv2D-op13",
                ...                                         use_regex=True,
                ...                                         iterations=[0],
                ...                                         ranks=[0],
                ...                                         slots=[0]
                ...                                         )
                ...     watchpoint = Watchpoint(tensors=tensors,
                ...                             condition=TensorTooLargeCondition(abs_mean_gt=0.0))
                ...     # the check_watchpoints function start a new process needs to be called through the main entry
                ...     hit = list(my_run.check_watchpoints(watchpoints=[watchpoint]))[0]
                ...     # print(str(hit))
                ...     # the print result is as follows
                ...     # Watchpoint TensorTooLarge triggered on tensor:
                ...     # rank: 0
                ...     # graph_name: kernel_graph_0
                ...     # node_name: Default/network-WithLossCell/_backbone-AlexNet/conv2-Conv2d/Conv2D-op13
                ...     # slot: 0
                ...     # iteration: 0
                ...     # Threshold: {'abs_mean_gt': 0.0}
                ...     # Hit detail: the setting for watchpoint is abs_mean_gt = 0.0.
                ...     # The actual value of the tensor is abs_mean_gt = 0.06592023578438996.
                ...
                >>> if __name__ == "__main__":
                ...     test_watchpoints()
                ...
        """
        wp_hit_list = []
        # key is watchpoint_id, value is a dict with iteration as the key and check_nodes as values
        iterations = set()
        wp_handles = {wp_id: WatchpointHandle(wp_id, wp) for wp_id, wp in enumerate(watchpoints)}
        for wp_handle in wp_handles.values():
            iterations.update(wp_handle.get_iterations())
        debugger_backend = self._debugger_engine.dbg_service
        # check all the watchpoint for the iterations
        for iteration in iterations:
            log.info("Check watchpoints for iteration %s", iteration)
            if not self._data_loader.has_data(iteration):
                log.info("No data dumped with iteration id: %s. Ignore checking watchpoint.", iteration)
                continue
            # adding the watchpoint for current iteration
            for wp_handle in wp_handles.values():
                wp_handle.add_watchpoint(iteration, self._debugger_engine)
            # check the watchpoint for current iteration
            # add the hit watchpoints to hit list
            hit_list = debugger_backend.check_watchpoints(
                iteration=iteration, error_on_no_value=error_on_no_value)
            for hit in hit_list:
                # the list of slots for the hit node to report
                # (for the current watchpoint and iteration)
                wp_handle = wp_handles.get(hit.watchpoint_id)
                graph_name, node_name = hit.name.split('/', 1)
                node = self._get_node(node_name, hit.rank_id, graph_name)
                tensor = DebuggerTensorImpl(node=node, slot=hit.slot, iteration=iteration)
                if wp_handle.need_check(tensor):
                    hit_params = hit.parameters
                    hit_detail = HitDetail(hit_params, wp_handle.condition)
                    wp_hit = WatchpointHitImpl(tensor=tensor,
                                               condition=wp_handle.condition,
                                               hit_detail=hit_detail,
                                               error_code=hit.error_code)
                    wp_hit_list.append(wp_hit)
            if error_on_no_value:
                no_value_hit_list = []
                for wp_handle in wp_handles.values():
                    no_value_hit_list += wp_handle.watchpoint_hit_on_no_value(iteration)
                wp_hit_list += no_value_hit_list
            # remove all the watchpoints for the previous iterations
            for watchpoint_id in wp_handles:
                debugger_backend.remove_watchpoint(watchpoint_id=watchpoint_id)

        return wp_hit_list

    def _get_node(self, node_name, rank_id, graph_name):
        """Get NodeImpl object."""
        unique_id = NodeUniqueId(name=node_name, rank=rank_id, graph_name=graph_name)
        node = self._nodes.get(rank_id, {}).get(unique_id)
        return node

    def list_affected_nodes(self, tensor):
        """
        List the nodes that use given tensor as input.

        Affected nodes is defined as the nodes use the given tensor as input. If
        a node is affected by the given tensor, the node's output value is
        likely to change when the given tensor changes.

        Args:
            tensor (DebuggerTensor): The tensor of which affected nodes will be
                returned.

        Returns:
            Iterable[Node], the affected nodes of the specified tensor.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensor_list = list(my_run.select_tensors(query_string="Conv2D-op13"))
                >>> affected_nodes = my_run.list_affected_nodes(tensor_list[0])
        """
        self._validate_node(tensor.node)
        affected_nodes = [affected_node.copy() for affected_node in tensor.node.downstream]
        return affected_nodes

    def get_input_nodes(self, node):
        """
        Get the input nodes of the given node.

        Args:
            node (Node): The node of which input nodes will be returned.

        Returns:
            Iterable[Node], the input nodes of the specified node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node_list = list(my_run.select_nodes(query_string="Conv2D-op13"))
                >>> input_nodes = my_run.get_input_nodes(node_list[0])
        """
        self._validate_node(node)
        input_nodes = node.input_nodes.copy()
        return input_nodes

    def get_output_nodes(self, node):
        """
        Get the nodes that use the output tensors of the given node.

        Args:
            node (Node): The specified node.

        Returns:
            Iterable[Node], output nodes of the specified node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node_list = list(my_run.select_nodes(query_string="Conv2D-op13"))
                >>> out_nodes = my_run.get_output_nodes(node_list[0])
        """
        self._validate_node(node)
        output_nodes = node.downstream.copy()
        return output_nodes

    def _validate_node(self, node):
        """Check if node is in current directory."""
        validate_type(node, 'node', NodeImpl, 'Node')
        node = self._get_node(node.name, node.rank, node.graph_name)
        if node is None:
            raise DebuggerParamValueError(f"Failed to find node {node.name} with rank {node.rank} "
                                          "in dump directory.")

    def _get_iterable_ranks(self, ranks):
        """
        Validate input ranks and return iterable rands.

        Args:
           ranks (Union[int, list[int], None], optional): The range of ranks.

        Returns:
            list[int], list of rank id.
        """
        total_ranks = self.get_ranks()
        return parse_param_to_iterable_obj(ranks, 'ranks', total_ranks)
