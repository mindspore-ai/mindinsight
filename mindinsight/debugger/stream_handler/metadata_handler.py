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
"""Define the metadata stream handler."""
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.common.utils import ServerStatus
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class MetadataHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        self._state = ServerStatus.PENDING
        self._device_name = ""
        self._step = 0
        self._client_ip = ""
        self._cur_node_name = ""
        self._cur_full_name = ""
        self._backend = ""

    @property
    def device_name(self):
        """The property of device name."""
        return self._device_name

    @property
    def step(self):
        """The property of current step."""
        return self._step

    @property
    def node_name(self):
        """The property of current node name."""
        return self._cur_node_name

    @node_name.setter
    def node_name(self, node_name):
        """The property of current node name."""
        self._cur_node_name = node_name

    @property
    def full_name(self):
        """The property of current node name."""
        return self._cur_full_name

    @property
    def backend(self):
        """The property of current backend."""
        return self._backend

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

    def put(self, value):
        """
        Put value into metadata cache. Called by grpc server.

        Args:
            value (MetadataProto): The Metadata proto message.
        """
        self._device_name = value.device_name.split(':')[0]
        self._step = value.cur_step
        self._cur_full_name = value.cur_node
        self._backend = value.backend if value.backend else "Ascend"
        log.debug("Put metadata into cache at the %d-th step.", self._step)

    def get(self, filter_condition=None):
        """
        Get updated value. Called by main server.

        Args:
            filter_condition (str): The filter property.

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
                'backend': self.backend
            }
        else:
            metadata[filter_condition] = getattr(self, filter_condition) if \
                hasattr(self, filter_condition) else ''

        return {'metadata': metadata}
