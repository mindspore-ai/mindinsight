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
import os
import json
from mindinsight.debugger.proto.ms_graph_pb2 import ModelProto
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.debugger.common.utils import DumpSettings


class DataLoader:
    """The DataLoader object provides interface to load graphs and device information from base_dir."""
    def __init__(self, base_dir):
        self._debugger_base_dir = os.path.realpath(base_dir)
        self._graph_protos = []
        self._device_info = {}
        self._step_num = {}
        # flag for whether the data is from sync dump or async dump, True for sync dump, False for async dump.
        self._is_sync = None
        self._net_dir = ""
        self._net_name = ""
        self.initialize()

    def initialize(self):
        """Initialize the data_mode and net_dir of DataLoader."""
        dump_config_file = os.path.join(self._debugger_base_dir, os.path.join(".metadata", "data_dump.json"))
        with open(dump_config_file, 'r') as load_f:
            dump_config = json.load(load_f)
            common_settings = dump_config.get(DumpSettings.COMMON_DUMP_SETTINGS.value)
            if not common_settings:
                raise ParamValueError('common_dump_settings not found in dump_config file.')
            self._net_name = common_settings['net_name']
            if dump_config.get(DumpSettings.E2E_DUMP_SETTINGS.value) and \
                    dump_config[DumpSettings.E2E_DUMP_SETTINGS.value]['enable']:
                self._is_sync = True
                self._net_dir = os.path.realpath(os.path.join(self._debugger_base_dir, self._net_name))
            elif dump_config.get(DumpSettings.ASYNC_DUMP_SETTINGS.value) and \
                    dump_config[DumpSettings.ASYNC_DUMP_SETTINGS.value]['enable']:
                self._is_sync = False
                self._net_dir = self._debugger_base_dir
            else:
                raise ParamValueError('The data must be generated from sync dump or async dump.')

    def load_graphs(self):
        """Load graphs from the debugger_base_dir."""
        files = os.listdir(self._net_dir)
        for file in files:
            if not self.is_device_dir(file):
                continue
            device_id, device_dir = self.get_device_id_and_dir(file)
            graphs_dir = os.path.join(device_dir, 'graphs')
            if not os.path.exists(graphs_dir) or not os.path.isdir(graphs_dir):
                log.debug("Directory '%s' not exist.", graphs_dir)
                self._graph_protos.append({'device_id': device_id, 'graph_protos': []})
                continue
            graph_protos = get_graph_protos_from_dir(graphs_dir)
            self._graph_protos.append({'device_id': device_id, 'graph_protos': graph_protos})

        return self._graph_protos

    def load_device_info(self):
        """Load device_info from file"""
        hccl_json_file = os.path.join(self._debugger_base_dir, '.metadata/hccl.json')
        if not os.path.isfile(hccl_json_file):
            device = []
            device_ids = self.get_all_device_id()
            device_ids.sort()
            for i, device_id in enumerate(device_ids):
                rank_id = i
                device.append({'device_id': str(device_id), 'rank_id': str(rank_id)})
            device_target = 'Ascend'
            self._device_info = {'device_target': device_target,
                                 'server_list': [{'server_id': 'localhost', 'device': device}]}
        else:
            with open(hccl_json_file, 'r') as load_f:
                load_dict = json.load(load_f)
                self._device_info = {'device_target': 'Ascend', 'server_list': load_dict['server_list']}
        return self._device_info

    def load_step_number(self):
        """Load step number in the directory"""
        files = os.listdir(self._net_dir)
        for file in files:
            if not self.is_device_dir(file):
                continue
            device_id, device_dir = self.get_device_id_and_dir(file)
            max_step = 0
            files_in_device = os.listdir(device_dir)
            if self._is_sync:
                for file_in_device in files_in_device:
                    abs_file_in_device = os.path.join(device_dir, file_in_device)
                    if os.path.isdir(abs_file_in_device) and file_in_device.startswith("iteration_"):
                        step_id_str = file_in_device.split('_')[-1]
                        max_step = update_max_step(step_id_str, max_step)
                self._step_num[str(device_id)] = max_step
            else:
                net_graph_dir = []
                for file_in_device in files_in_device:
                    abs_file_in_device = os.path.join(device_dir, file_in_device)
                    if os.path.isdir(abs_file_in_device) and file_in_device.startswith(self._net_name):
                        net_graph_dir.append(abs_file_in_device)
                if len(net_graph_dir) > 1:
                    log.warning("There are more than one graph directory in device_dir: %s. "
                                "OfflineDebugger use data in %s.", device_dir, net_graph_dir[0])
                net_graph_dir_to_use = net_graph_dir[0]
                graph_id = net_graph_dir_to_use.split('_')[-1]
                graph_id_dir = os.path.join(net_graph_dir_to_use, graph_id)
                step_ids = os.listdir(graph_id_dir)
                for step_id_str in step_ids:
                    max_step = update_max_step(step_id_str, max_step)
                self._step_num[str(device_id)] = max_step

        return self._step_num

    def is_device_dir(self, file_name):
        """Judge if the file_name is a sub directory named 'device_x'."""
        if not file_name.startswith("device_"):
            return False
        id_str = file_name.split("_")[-1]
        if not id_str.isdigit():
            return False
        device_dir = os.path.join(self._net_dir, file_name)
        if not os.path.isdir(device_dir):
            return False
        return True

    def get_device_id_and_dir(self, file_name):
        """Get device_id and absolute directory of file_name."""
        id_str = file_name.split("_")[-1]
        device_id = int(id_str)
        device_dir = os.path.join(self._net_dir, file_name)
        return device_id, device_dir

    def get_all_device_id(self):
        """Get all device_id int the debugger_base_dir"""
        device_ids = []
        files = os.listdir(self._net_dir)
        for file in files:
            if not self.is_device_dir(file):
                continue
            id_str = file.split("_")[-1]
            device_id = int(id_str)
            device_ids.append(device_id)
        return device_ids

    def get_net_dir(self):
        """Get graph_name directory of the data."""
        return self._net_dir

    def get_sync_flag(self):
        """Get the sync flag of the data."""
        return self._is_sync

    def get_net_name(self):
        """Get net_name of the data."""
        return self._net_name


def load_graph_from_file(graph_file_name):
    """Load graph from file."""
    with open(graph_file_name, 'rb') as file_handler:
        model_bytes = file_handler.read()
        model = ModelProto.FromString(model_bytes)
        graph = model.graph

    return graph


def get_graph_protos_from_dir(graphs_dir):
    """
    Get graph from graph directory.

    Args:
        graph_dir (str): The absolute directory of graph files.

    Returns:
        list, list of 'GraphProto' object.
    """
    files_in_graph_dir = os.listdir(graphs_dir)
    graph_protos = []
    pre_file_name = "ms_output_trace_code_graph_"
    for file_in_device in files_in_graph_dir:
        if file_in_device.startswith(pre_file_name) and file_in_device.endswith(".pb"):
            abs_graph_file = os.path.join(graphs_dir, file_in_device)
            graph_proto = load_graph_from_file(abs_graph_file)
            graph_protos.append(graph_proto)
    return graph_protos


def update_max_step(step_id_str, max_step):
    """Update max_step by compare step_id_str and max_step."""
    res = max_step
    if step_id_str.isdigit():
        step_id = int(step_id_str)
        if step_id > max_step:
            res = step_id
    return res
