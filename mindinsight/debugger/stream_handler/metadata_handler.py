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
"""Define the metadata stream handler."""

from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import ServerStatus, DebuggerServerMode
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class MetadataHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        self._state = ServerStatus.PENDING
        self._device_name = ""
        self.step = 0
        self._client_ip = ""
        self._cur_node_name = ""
        self._cur_full_name = ""
        self.backend = ""
        self._enable_recheck = False
        self._cur_graph_name = ""
        # If recommendation_confirmed is true, it only means the user has answered yes or no to the question,
        # it does not necessarily mean that the user will use the recommended watch points.
        self._recommendation_confirmed = False
        self._debugger_version = {}
        self._data_version = {}
        # maximum step number among all devices
        self._max_step_num = 0
        self._debugger_type = DebuggerServerMode.ONLINE.value
        self.max_graph_node_size = 0

    @property
    def debugger_type(self):
        """The property of debugger_type."""
        return self._debugger_type

    @debugger_type.setter
    def debugger_type(self, debugger_type):
        """The property of debugger_type."""
        self._debugger_type = debugger_type

    @property
    def device_name(self):
        """The property of device name."""
        return self._device_name

    @property
    def node_name(self):
        """The property of current node name."""
        return self._cur_node_name

    @node_name.setter
    def node_name(self, node_name):
        """The property of current node name."""
        self._cur_node_name = node_name

    @property
    def graph_name(self):
        """The property of current node name."""
        return self._cur_graph_name

    @graph_name.setter
    def graph_name(self, graph_name):
        """The property of current node name."""
        self._cur_graph_name = graph_name if graph_name else ''

    @property
    def full_name(self):
        """The property of current node name."""
        return self._cur_full_name

    @property
    def state(self):
        """The property of state."""
        return self._state.value

    @state.setter
    def state(self, value):
        """
        Set the property of state.

        Args:
            value (str): The new state.
        """
        self._state = ServerStatus(value)

    @property
    def client_ip(self):
        """The property of client ip."""
        return self._client_ip

    @client_ip.setter
    def client_ip(self, value):
        """
        Set the property of client ip.

        Args:
            value (str): The new ip.
        """
        self._client_ip = str(value)

    @property
    def enable_recheck(self):
        """The property of enable_recheck."""
        return self._enable_recheck and self._state == ServerStatus.WAITING

    @enable_recheck.setter
    def enable_recheck(self, value):
        """
        Set the property of enable_recheck.

        Args:
            value (bool): The new ip.
        """
        self._enable_recheck = bool(value)

    @property
    def recommendation_confirmed(self):
        """The property of recommendation_confirmed."""
        return self._recommendation_confirmed

    @recommendation_confirmed.setter
    def recommendation_confirmed(self, value):
        """
        Set the property of recommendation_confirmed.

        Args:
            value (str): The new ip.
        """
        self._recommendation_confirmed = value

    @property
    def debugger_version(self):
        """The property of debugger_version."""
        return self._debugger_version

    @debugger_version.setter
    def debugger_version(self, value):
        """
        Set the property of debugger_version.

        Args:
            value (dict): The  semantic versioning of mindinsight and mindspore,
            format is {'ms': 'x.x.x', 'mi': 'x.x.x'}.
        """
        self._debugger_version = value

    @property
    def data_version(self):
        """The property of data_version."""
        return self._data_version

    @data_version.setter
    def data_version(self, value):
        """
        Set the property of data_version.

        Args:
            value (dict): The semantic versioning of mindinsight and mindspore dump data,
            format is {'state': True, 'ms': 'x.x.x', 'mi': 'x.x.x'}.
        """
        self._data_version = value

    @property
    def max_step_num(self):
        """The property of max_step_num."""
        return self._max_step_num

    @max_step_num.setter
    def max_step_num(self, max_step_num):
        """Set the property of max_step_num."""
        self._max_step_num = max_step_num

    def put(self, value):
        """
        Put value into metadata cache. Called by grpc server.

        Args:
            value (MetadataProto): The Metadata proto message.
        """
        self._device_name = value.device_name.split(':')[0]
        self.step = value.cur_step
        self._cur_full_name = value.cur_node
        self.backend = value.backend if value.backend else "Ascend"
        log.debug("Put metadata into cache at the %d-th step.", self.step)

    def get(self, filter_condition=None):
        """
        Get updated value. Called by main server.

        Args:
            filter_condition (Union[str, list[str]]): The filter property.

        Returns:
            dict, the metadata.
        """
        metadata = {}
        if filter_condition is None:
            metadata = {
                'state': self.state,
                'step': self.step,
                'device_name': self.device_name,
                'pos': '0',
                'ip': self.client_ip,
                'node_name': self.node_name,
                'backend': self.backend,
                'enable_recheck': self.enable_recheck,
                'graph_name': self.graph_name,
                'recommendation_confirmed': self._recommendation_confirmed,
                'debugger_version': self.debugger_version,
                'data_version': self.data_version,
            }
            if self.debugger_type == 'offline':
                metadata['total_step_num'] = self.max_step_num
            if self.state == ServerStatus.NODE_TOO_LARGE.value:
                metadata['max_graph_node_size'] = self.max_graph_node_size
        else:
            if not isinstance(filter_condition, list):
                filter_condition = [filter_condition]
            for field in filter_condition:
                metadata[field] = getattr(self, field) if \
                    hasattr(self, field) else None

        return {'metadata': metadata}
