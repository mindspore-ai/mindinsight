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
"""Define the Device stream handler."""
from collections import defaultdict

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, DeviceIdUnregistered, \
    DebuggerParamTypeError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class DeviceHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        # contains all device infos, the format is like Dict[int(<device_id>, <device_info>)]
        self._rank_info = defaultdict(DeviceInfo)
        self._device_rank_map = {}

    @property
    def rank_ids(self):
        """The rank ids."""
        return list(self._rank_info)

    @property
    def device_amount(self):
        """The rank ids."""
        return len(self._rank_info)

    def put(self, value):
        """
        Put value into device info cache.

        Args:
            value (list): The list of server info. Each item is format like:
                {
                    "server_id": str,
                    "device": list[<Device Info>]
                },
                The format of <Device Info> is like:
                {
                    "device_id": str,
                    "device_ip": str,
                    "rank_id": str
                }.
        """
        if not isinstance(value, list):
            log.error("Invalid input type. list object is expected.")
            raise DebuggerParamTypeError("List object is expected.")
        try:
            self._extract_rank_info(value)
        except (TypeError, ValueError) as err:
            log.exception(err)
            log.error("Invalid Device info.")
            raise DebuggerParamValueError("Invalid device info.")
        log.debug("Put Device into cache")

    def _extract_rank_info(self, value):
        """Extract rank info and save."""
        for server_info in value:
            server_ip = server_info.get('server_id')
            for device_info in server_info.get('device', []):
                rank_id = int(device_info.get('rank_id'))
                if rank_id in self._rank_info:
                    log.error("Repeated rank info for rank_id: %d", rank_id)
                    raise DebuggerParamValueError("Repeated rank info.")
                device_info_obj = self._rank_info[rank_id]
                device_info_obj.rank_id = rank_id
                device_info_obj.server_ip = server_ip
                device_info_obj.device_id = int(device_info.get('device_id'))
                device_info_obj.device_ip = device_info.get('device_ip')
                self._device_rank_map[device_info_obj.device_id] = rank_id

    def add_step_num_info(self, step_info):
        """
        Add step number information for each rank.

        Args:
            step_info (dict): Step info per rank. The key is the rank id, the value
                is the relative step number.
        """
        if not step_info:
            log.warning("No step number information.")
            return
        for rank_id, step_num in step_info.items():
            self._rank_info[rank_id].step_num = step_num

    def add_graph_name_info(self, graphs):
        """
        Add graph name per device.

        Args:
            graphs (dict): Graph infos of all rank id. Each item is format like
        """
        for rank_id, graph_info in graphs.items():
            graph_names = list(graph_info)
            if len(graph_names) > 1:
                # if more than one graphs in a device, sort them
                # by the number following the last "_" in the graph_name
                graph_names = sorted(graph_names, key=lambda x: x.split("_")[-1])
            self._rank_info[rank_id].graph_names = graph_names

    def get(self, filter_condition=None):
        """
        Get device information according to filter_condition.

        Args:
            filter_condition (list): The rank id.

        Returns:
            dict, the device info.
        """
        if filter_condition is None:
            filter_condition = self.rank_ids
        if not isinstance(filter_condition, list):
            filter_condition = [filter_condition]
        device_infos = []
        for rank_id in filter_condition:
            device_info = self._rank_info.get(rank_id)
            if device_info is None:
                log.error("Invalid rank id.")
                raise DeviceIdUnregistered(rank_id)
            device_infos.append(device_info.to_dict())
        return {'devices': device_infos}

    def get_rank_id_by_device_id(self, device_id):
        """
        Get rank id by device id.

        Args:
            device_id (int): The device id.

        Returns:
            int, the rank id.
        """
        rank_id = self._device_rank_map.get(device_id)
        if rank_id is None:
            log.error("Failed to find rank_id for device_id %s", device_id)
            raise DeviceIdUnregistered(device_id)
        return rank_id

    def get_device_id_by_rank_id(self, rank_id):
        """
        Get device id by rank id.

        Args:
            rank_id (int): The rank id.

        Returns:
            int, the device id.
        """
        device_info = self._rank_info.get(rank_id)
        if device_info:
            return device_info.device_id
        log.error("Failed to find device id according to rank_id %s", rank_id)
        raise DeviceIdUnregistered(rank_id)


class DeviceInfo:
    """Device info object."""

    def __init__(self):
        self.rank_id = 0
        self.device_id = 0
        self.server_ip = ''
        self.graph_names = []
        self.device_ip = ''
        self.step_num = 0

    def to_dict(self):
        """Convert device info to dict."""
        res = {
            'rank_id': self.rank_id,
            'server_ip': self.server_ip,
            'device_id': self.device_id,
            'device_ip': self.device_ip,
            'graph_names': self.graph_names,
            'total_step_num': self.step_num
        }
        return res
