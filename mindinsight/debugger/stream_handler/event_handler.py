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
"""Define the message handler."""
import uuid
from queue import Queue, Empty
from threading import Lock

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase


class EventHandler(StreamHandlerBase):
    """Message Handler."""

    max_limit = 1000  # the max number of items in cache

    def __init__(self):
        self._prev_flag = str(uuid.uuid4())
        self._cur_flag = str(uuid.uuid4())
        self._next_idx = 0
        self._event_cache = [None] * self.max_limit
        self._pending_requests = {}
        self._lock = Lock()

    @property
    def next_pos(self):
        """The next pos to be updated in cache."""
        return ':'.join([self._cur_flag, str(self._next_idx)])

    def has_pos(self, pos):
        """Get the event according to pos."""
        cur_flag, cur_idx = self._parse_pos(pos)
        if cur_flag not in [self._cur_flag, self._prev_flag]:
            cur_flag, cur_idx = self._cur_flag, 0
        event = self._event_cache[cur_idx]
        if event is not None:
            if not cur_flag or (cur_flag == self._cur_flag and cur_idx < self._next_idx) or \
                    (cur_flag == self._prev_flag and cur_idx >= self._next_idx):
                return event

        return None

    def clean(self):
        """Clean event cache."""
        with self._lock:
            self._prev_flag = str(uuid.uuid4())
            self._cur_flag = str(uuid.uuid4())
            self._next_idx = 0
            self._event_cache = [None] * self.max_limit
            value = {'metadata': {'pos': '0'}}
            self.clean_pending_requests(value)
            log.debug("Clean event cache. %d request is waiting.", len(self._pending_requests))

    def put(self, value):
        """
        Put value into event_cache.

        Args:
            value (dict): The event to be put into cache.
        """
        if not isinstance(value, dict):
            log.error("Dict type required when put event message.")
            raise DebuggerParamValueError("Dict type required when put event message.")

        with self._lock:
            log.debug("Put the %d-th message into queue. \n %d requests is waiting.",
                      self._next_idx, len(self._pending_requests))
            cur_pos = self._next_idx
            # update next pos
            self._next_idx += 1
            if self._next_idx >= self.max_limit:
                self._next_idx = 0
                self._prev_flag = self._cur_flag
                self._cur_flag = str(uuid.uuid4())
            # set next pos
            if not value.get('metadata'):
                value['metadata'] = {}
            value['metadata']['pos'] = self.next_pos
            self._event_cache[cur_pos] = value
            # feed the value for pending requests
            self.clean_pending_requests(value)

    def clean_pending_requests(self, value):
        """Clean pending requests."""
        for _, request in self._pending_requests.items():
            request.put(value)
        self._pending_requests = {}

    def get(self, filter_condition=None):
        """
        Get the pos-th value from event_cache according to filter_condition.

        Args:
            filter_condition (str): The index of event in cache. Default: None.

        Returns:
            object, the pos-th event.
        """
        flag, idx = self._parse_pos(filter_condition)
        cur_id = str(uuid.uuid4())
        with self._lock:
            # reset the pos after the cache is re-initialized.
            if not flag or flag not in [self._cur_flag, self._prev_flag]:
                idx = 0
            # get event from cache immediately
            if idx != self._next_idx and self._event_cache[idx]:
                return self._event_cache[idx]
            # wait for the event
            cur_queue = Queue(maxsize=1)
            self._pending_requests[cur_id] = cur_queue
        # block until event has been received
        event = self._wait_for_event(cur_id, cur_queue, filter_condition)

        return event

    def _parse_pos(self, pos):
        """Get next pos according to input position."""
        elements = pos.split(':')
        try:
            idx = int(elements[-1])
        except ValueError:
            log.error("Invalid index. The index in pos should be digit but get pos:%s", pos)
            raise DebuggerParamValueError("Invalid pos.")

        if idx < 0 or idx >= self.max_limit:
            log.error("Invalid index. The index in pos should between [0, %d)", self.max_limit)
            raise DebuggerParamValueError(f"Invalid pos. {idx}")
        flag = elements[0] if len(elements) == 2 else ''

        return flag, idx

    def _wait_for_event(self, cur_id, cur_queue, pos):
        """Wait for the pos-th event."""
        try:
            # set the timeout to 25 seconds which is less the the timeout limit from UI
            event = cur_queue.get(timeout=25)
        except Empty:
            event = None

        if event is None:
            with self._lock:
                if self._pending_requests.get(cur_id):
                    self._pending_requests.pop(cur_id)
                log.debug("Clean timeout request. Left pending requests: %d",
                          len(self._pending_requests))
            event = {'metadata': {'pos': pos}}

        return event
