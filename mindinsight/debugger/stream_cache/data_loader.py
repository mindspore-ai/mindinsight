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
"""This file is used to define the DataLoader."""
import csv
import os
import json
import re
from collections import namedtuple
from pathlib import Path

from google.protobuf.message import DecodeError

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, RankDirNotFound, \
    DebuggerJsonFileParseError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import DumpSettings, is_valid_rank_dir_name
from mindinsight.domain.graph.proto.ms_graph_pb2 import ModelProto

RankDir = namedtuple("rank_dir", ["rank_id", "path"])


class DataLoader:
    """The DataLoader object provides interface to load graphs and device information from base_dir."""

    DUMP_METADATA = '.dump_metadata'
    EXECUTION_ORDER = 'execution_order'
    GRAPHS = 'graphs'

    def __init__(self, base_dir):
        self._debugger_base_dir = Path(base_dir).absolute()
        # list of RankDir objects
        self._rank_dirs = []
        # flag for whether the data is from sync dump or async dump.
        self._is_sync = False
        self._device_target = "Ascend"
        self._net_name = ""
        self._initialize()

    @property
    def rank_dirs(self):
        """The property of RankDir."""
        return self._rank_dirs

    def _initialize(self):
        """Initialize the data_mode and net_dir of DataLoader."""
        self._load_rank_dirs()
        if not self._rank_dirs:
            log.error("No rank directory found under %s", str(self._debugger_base_dir))
            raise RankDirNotFound(str(self._debugger_base_dir))
        rank_dir = self._rank_dirs[0].path
        dump_config = self._load_json_file(rank_dir / self.DUMP_METADATA / 'data_dump.json')

        def _set_net_name():
            nonlocal dump_config
            common_settings = dump_config.get(DumpSettings.COMMON_DUMP_SETTINGS.value, {})
            try:
                self._net_name = common_settings['net_name']
            except KeyError:
                raise DebuggerJsonFileParseError("data_dump.json")

        def _set_dump_mode_and_device_target():
            nonlocal dump_config
            config_json = self._load_json_file(rank_dir / self.DUMP_METADATA / 'config.json')
            self._device_target = config_json.get('device_target', 'Ascend')
            if self._device_target == 'GPU' or dump_config.get(DumpSettings.E2E_DUMP_SETTINGS.value) and \
                    dump_config[DumpSettings.E2E_DUMP_SETTINGS.value]['enable']:
                self._is_sync = True
            else:
                self._is_sync = False

        _set_net_name()
        _set_dump_mode_and_device_target()

    def _load_rank_dirs(self):
        """Load rank directories."""
        self._rank_dirs = []
        rank_dirs = self._debugger_base_dir.glob('rank_*')
        for rank_dir in rank_dirs:
            if not rank_dir.is_dir() or not is_valid_rank_dir_name(rank_dir.name) \
                    or not os.path.exists(os.path.join(rank_dir, ".dump_metadata")):
                continue
            rank_id = int(rank_dir.name.split('_', 1)[-1])
            self._rank_dirs.append(RankDir(rank_id, rank_dir))
        if self._rank_dirs:
            self._rank_dirs.sort(key=lambda x: x.rank_id)

    def load_graphs(self):
        """
        Load graphs from the debugger_base_dir.

        Returns:
            list, list of graph protos from all ranks. Each item is like:
                {'rank_id': int,
                'graph_protos': [GraphProto]}
        """
        res = []
        for rank_dir in self._rank_dirs:
            rank_id, rank_path = rank_dir.rank_id, rank_dir.path
            graphs_dir = rank_path / self.GRAPHS
            if not graphs_dir.is_dir():
                log.debug("Directory '%s' doesn't exist.", graphs_dir)
                res.append({'rank_id': rank_id, 'graph_protos': []})
                continue
            graph_protos = get_graph_protos_from_dir(graphs_dir)
            res.append({'rank_id': rank_id, 'graph_protos': graph_protos})

        return res

    def load_device_info(self):
        """Load device_info from dump path."""
        device_info = {}
        if not self._rank_dirs:
            log.info("No rank directory found under dump path.")
            return device_info
        rank_dir = self._rank_dirs[0].path
        hccl_json = self._load_json_file(rank_dir / '.dump_metadata' / 'hccl.json')
        if hccl_json.get('server_list'):
            device_info = {'device_target': self._device_target, 'server_list': hccl_json['server_list']}
        else:
            log.info("Server List info is missing. Set device id same with rank id as default.")
            devices = []
            for rank_dir in self._rank_dirs:
                rank_id = rank_dir.rank_id
                devices.append({'device_id': str(rank_id), 'rank_id': str(rank_id)})
            device_info = {'device_target': self._device_target,
                           'server_list': [{'server_id': 'localhost', 'device': devices}]}
        return device_info

    @staticmethod
    def _load_json_file(file):
        """
        Load json file content.

        Args:
            file (Path): The Path object.

        Returns:
            dict, the json content.
        """
        if not file.is_file():
            log.info("File <%s> is missing.", str(file))
            return {}
        with file.open() as handler:
            try:
                return json.load(handler)
            except json.decoder.JSONDecodeError as err:
                log.warning("Failed to load json file %s. %s", str(file), str(err))
                return {}

    def load_dumped_step(self):
        """
        Load dumped step number in the directory.

        Returns:
            dict, the dumped step info among all devices. The key is rank_id,
            the value is like Dict[int, list[int]].
        """
        def _load_iters_per_rank(net_dir):
            res = {}
            for graph_dir in net_dir.iterdir():
                graph_id_str = graph_dir.name
                if not graph_id_str.isdigit():
                    log.warning("Invalid graph dir under net dir:%s", str(net_dir))
                    continue
                res[int(graph_id_str)] = _load_iters_per_graph(graph_dir)
            return res

        def _load_iters_per_graph(graph_dir):
            iters = []
            for iteration_dir in graph_dir.iterdir():
                iter_id_str = iteration_dir.name
                if not iter_id_str.isdigit():
                    log.debug("Ignore iteration dir: %s", str(iteration_dir))
                    continue
                iters.append(int(iter_id_str))
            return iters

        step_num = {}
        for rank_dir in self._rank_dirs:
            rank_id, rank_path = rank_dir.rank_id, rank_dir.path
            net_path = rank_path / self._net_name
            if not net_path.is_dir():
                log.info("No net directory under rank dir: %s", str(rank_dir))
                continue
            step_num[rank_id] = _load_iters_per_rank(net_path)

        return step_num

    def get_rank_dir(self, rank_id):
        """
        Get the rank directory according to rank_id.

        Args:
            rank_id (int): The rank id.

        Returns:
            RankDir, the rank dir info.
        """
        rank_path = self._debugger_base_dir / f'rank_{rank_id}'
        if rank_path.is_dir():
            return RankDir(rank_id, rank_path)
        log.error("No rank directory found.")
        raise DebuggerParamValueError("Invalid rank_id.")

    def get_step_iter(self, rank_id=None, step=None):
        """Get the generator of step path."""
        step_pattern = '[0-9]*' if step is None else step
        if rank_id is None:
            rank_dirs = self._rank_dirs
        else:
            rank_dirs = list(self.get_rank_dir(rank_id))
        for rank_dir in rank_dirs:
            step_dirs = rank_dir.path.glob(f'{self._net_name}/[0-9]*/{step_pattern}')
            for step_dir in step_dirs:
                yield step_dir

    def get_dump_dir(self):
        """Get graph_name directory of the data."""
        return str(self._debugger_base_dir)

    def get_sync_flag(self):
        """Get the sync flag of the data."""
        return self._is_sync

    def get_net_name(self):
        """Get net_name of the data."""
        return self._net_name

    def load_graph_history(self):
        """
        Load graph history of all devices.

        Returns:
            dict, graph history. The key is rank id, the value is Dict[int, list[int]].
        """
        all_graph_history = {}
        for rank_dir in self._rank_dirs:
            execution_order_dir = rank_dir.path / self.EXECUTION_ORDER
            if not execution_order_dir.is_dir():
                log.warning("Execution order directory %s doesn't exist.", str(execution_order_dir))
                all_graph_history[rank_dir.rank_id] = {}
                continue
            graph_history = {}
            history_pattern = re.compile(r"ms_global_execution_order_graph_(?P<graph_id>\d+).csv")
            for item in execution_order_dir.iterdir():
                re_match = re.match(history_pattern, item.name)
                if re_match:
                    history = read_graph_history(item)
                    graph_history[int(re_match.group('graph_id'))] = history
            all_graph_history[rank_dir.rank_id] = graph_history
        return all_graph_history


def read_graph_history(file_path):
    """
    Load graph history from file.

    Args:
        file_path (str): File path contains the graph execution order info.

    Returns:
        list[int], the executed iteration ids of each graph.
    """
    with open(file_path, 'r') as handler:
        csv_reader = csv.reader(handler)
        history = [int(row[0]) for row in csv_reader]
        return history


def load_graph_from_file(graph_file_path):
    """
    Load graph from file.

    Args:
        graph_file_path (Path): Graph file path.

    Returns:
        GraphProto, the parsed GraphProto object.
    """
    with graph_file_path.open('rb') as file_handler:
        model_bytes = file_handler.read()
        model = ModelProto.FromString(model_bytes)
        graph = model.graph

    return graph


def get_graph_protos_from_dir(graphs_dir):
    """
    Get graph from graph directory.

    Args:
        graphs_dir (Path): The Path object of graph directory.

    Returns:
        list, list of 'GraphProto' object.
    """
    graph_protos = []
    pre_file_name = "ms_output_trace_code_graph_"
    for file_in_device in graphs_dir.iterdir():
        file_name = file_in_device.name
        if file_name.startswith(pre_file_name) and file_name.endswith(".pb"):
            try:
                graph_proto = load_graph_from_file(file_in_device)
            except DecodeError:
                log.warning("Load graph failed. The graph file is invalid.")
                return []
            graph_protos.append(graph_proto)
    return graph_protos
