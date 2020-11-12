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
"""Implement the debugger data cache manager."""
import sys

from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import Streams
from mindinsight.debugger.stream_handler import EventHandler, MetadataHandler, GraphHandler, \
    TensorHandler, WatchpointHandler, WatchpointHitHandler

STREAM_HANDLER_MAP = {
    Streams.COMMAND.value: EventHandler,
    Streams.DATA.value: EventHandler,
    Streams.METADATA.value: MetadataHandler,
    Streams.GRAPH.value: GraphHandler,
    Streams.TENSOR.value: TensorHandler,
    Streams.WATCHPOINT.value: WatchpointHandler,
    Streams.WATCHPOINT_HIT.value: WatchpointHitHandler
}


class DebuggerCache:
    """The debugger data cache manager."""

    def __init__(self):
        self._stream_handler = {}

    def initialize(self):
        """Initialize the stream handlers."""
        self._stream_handler = {}
        for stream in Streams:
            mode = stream.value
            stream_handler = STREAM_HANDLER_MAP.get(mode)
            self._stream_handler[mode] = stream_handler()

    def clean(self):
        """Clean cache for all stream."""
        for _, stream_handler in self._stream_handler.items():
            stream_handler.clean()

    def get_stream_handler(self, mode):
        """
        Get the stream handler object.

        Args:
            mode (Streams): The type of stream handler.

        Returns:
            StreamHandlerBase, the stream handler object.
        """
        return self._stream_handler.get(mode.value)

    def _get(self, mode, pos):
        """
        Get updated data or command from cache.

        Args:
            mode (Streams): The type of info. `Streams.DATA` or `Streams.COMMAND`.
            pos (int): The index of info.

        Returns:
            object, the pos-th message about `mode` type of info.
        """
        stream_handler = self.get_stream_handler(mode)

        return stream_handler.get(pos)

    def _put(self, mode, value):
        """
        Set updated data or command from cache.

        Args:
            mode (Streams): The type of info. `Streams.DATA` or `Streams.COMMAND`.
            value (object): The info to be record in cache.
        """
        stream_handler = self.get_stream_handler(mode)

        return stream_handler.put(value)

    def get_command(self, pos):
        """
        Get the pos-th command in command stream.

        Args:
            pos (int): The index of command.

        Returns:
            int, the position of next message.
            EventReply, the command object.
        """
        content = self._get(Streams.COMMAND, pos)
        next_pos = content.get('metadata').get('pos')
        reply = content.get('cmd')
        return next_pos, reply

    def put_command(self, cmd):
        """
        Set command to command stream.

        Args:
            cmd (EventReply): The command EventReply.
        """
        log.debug("Set command %s", cmd)
        return self._put(Streams.COMMAND, {'cmd': cmd})

    def has_command(self, pos):
        """Judge if the number of command is no less than `pos`."""
        event = self.get_stream_handler(Streams.COMMAND).has_pos(pos)

        return event

    def clean_command(self):
        """Clean command queue."""
        self.get_stream_handler(Streams.COMMAND).clean()
        log.debug("Clean command.")

    def clean_data(self):
        """Clean command queue."""
        self.get_stream_handler(Streams.DATA).clean()
        log.debug("Clean data queue.")

    def get_data(self, pos):
        """
        Get updated data from data stream.

        Args:
            pos (int): The index of data.

        Returns:
            object, updated data_value.
        """
        return self._get(Streams.DATA, pos)

    def put_data(self, value):
        """
        Set updated data to data stream.

        Args:
            value (dict): The updated data.
        """
        log.debug("Set <%d> bytes data", sys.getsizeof(value))
        return self._put(Streams.DATA, value)
