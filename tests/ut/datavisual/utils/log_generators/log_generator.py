# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Base log Generator."""

import struct
from abc import abstractmethod

from tests.ut.datavisual.utils import crc32


class LogGenerator:
    """
    Base log generator.

    This is a base class for log generators. User can use it to generate fake
    summary logs.
    """

    @abstractmethod
    def generate_event(self, values):
        """
        Abstract method for generating event.

        Args:
            values (dict): Values.

        Returns:
            summary_pb2.Event.

        """

    def _write_log_one_step(self, file_path, values):
        """
        Write log one step.

        Args:
            file_path (str): File path to write.
            values (dict): Values.

        """
        event = self.generate_event(values)
        self._write_log_from_event(file_path, event)

    @staticmethod
    def _write_log_from_event(file_path, event):
        """
        Write log by event.

        Args:
            file_path (str): File path to write.
            event (summary_pb2.Event): Event object in proto.

        """
        send_msg = event.SerializeToString()

        header = struct.pack('<Q', len(send_msg))
        header_crc = struct.pack('<I', crc32.get_mask_from_string(header))
        footer_crc = struct.pack('<I', crc32.get_mask_from_string(send_msg))

        write_event = header + header_crc + send_msg + footer_crc

        with open(file_path, "ab") as f:
            f.write(write_event)
