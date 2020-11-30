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
"""Parse summary file and save it local file."""

import os
import time

from google.protobuf.message import DecodeError

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.log import parse_summary_logger
from mindinsight.datavisual.proto_files import lazy_read_pb2
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.summary_parser.image_writer import ImageWriter
from mindinsight.datavisual.data_transform.summary_parser.scalar_writer import ScalarWriter

from ..ms_data_loader import _SummaryParser

HEADER_SIZE = 8
CRC_STR_SIZE = 4
MAX_EVENT_STRING = 500000000
SCALAR = 'scalar_value'
IMAGE = 'image'
INFO_INTERVAL = 10
RETRY_TIMES = 2


class EventParser:
    """Parse summary file and save it to local file."""
    def __init__(self, summary_file, output):
        self.summary_file = summary_file
        self._output = output
        self._scalar_writer = ScalarWriter(self._output)
        self._image_writer = ImageWriter(FileHandler.join(self._output, IMAGE))
        self._file_size = 0
        self._process_info = 0
        self._image_check = False
        self._scalar_check = False

    def parse(self):
        """Load summary file and parse file content."""

        summary_file_handler = FileHandler(self.summary_file, 'rb')

        self._file_size = os.path.getsize(self.summary_file)
        # when current parsed size bigger than self._process_info, print process
        self._process_info = self._file_size // INFO_INTERVAL

        parse_summary_logger.info("Loading %s.", self.summary_file)
        result = self._load(summary_file_handler)

        if result:
            warning = ''
            scalar_path = FileHandler.join(self._output, "scalar.csv")
            image_path = FileHandler.join(self._output, IMAGE)

            if not self._image_check:
                warning = warning + " The summary file contains no image."
            else:
                parse_summary_logger.info("Images are written in %s.", image_path)

            if not self._scalar_check:
                warning = warning + " The summary file contains no scalar value."
            else:
                parse_summary_logger.info("Writing scalar data into %s.", scalar_path)

            self._scalar_writer.write()
            if warning:
                parse_summary_logger.warning(warning)

            parse_summary_logger.info("Finished loading %s.", self.summary_file)

    def _load(self, file_handler):
        """
        Load a log file data.

        Args:
            file_handler (FileHandler): A file handler.

        Returns:
            bool, True if the summary file is finished loading.
        """
        crc_check_time = 0
        while True:
            start_offset = file_handler.offset
            try:
                event_str = _SummaryParser.event_load(file_handler)
                if start_offset != file_handler.offset:
                    self._print_process(file_handler)
                crc_check_time = 0
                if event_str is None:
                    return True
                if len(event_str) > MAX_EVENT_STRING:
                    parse_summary_logger.warning("file_path: %s, event string: %d exceeds %d and drop it.",
                                                 file_handler.file_path, len(event_str), MAX_EVENT_STRING)
                    continue
                self._event_parse(event_str)
            except exceptions.CRCLengthFailedError:
                if crc_check_time > RETRY_TIMES:
                    parse_summary_logger.error(
                        "Check crc length failed, please check the summary file integrity, "
                        "the file may be in transfer, file_path: %s, offset=%s.",
                        file_handler.file_path, start_offset)
                    return True
                parse_summary_logger.warning(
                    "Check crc failed, retrying %d/%d times.", crc_check_time + 1, RETRY_TIMES + 1)
                file_handler.reset_offset(start_offset)
                crc_check_time += 1
                time.sleep(0.5)
            except exceptions.CRCFailedError:
                parse_summary_logger.error(
                    "Check crc failed, the file may have been modified, file_path=%s, offset=%s.",
                    file_handler.file_path, start_offset)
                return True
            except (OSError, DecodeError, exceptions.MindInsightException) as ex:
                parse_summary_logger.error("Parse file fail, detail: %r, file path: %s.", str(ex),
                                           file_handler.file_path)
                return False

    def _print_process(self, file_handler):
        """Prints the current parsing progress based on the progress of the read file."""
        current_offset = file_handler.offset
        if current_offset >= self._process_info:
            parse_summary_logger.info("Current parsing process: %d/%d, %d%%.", current_offset, self._file_size,
                                      100 * current_offset // os.path.getsize(self.summary_file))
            self._process_info += self._file_size // INFO_INTERVAL
            if self._process_info > os.path.getsize(self.summary_file):
                self._process_info = os.path.getsize(self.summary_file)

    def _event_parse(self, event_str):
        """
        Transform `Event` data to event and extract the scalar and image data.

        Args:
            event_str (str): Message event string in summary proto, data read from file handler.
        """

        plugins = [SCALAR, IMAGE]

        event = lazy_read_pb2.Event.FromString(event_str)

        if event.HasField('summary'):
            for value in event.summary.value:
                for plugin in plugins:
                    if not value.HasField(plugin):
                        continue
                    self._parse_summary_value(value.tag, event.step, event.wall_time, value, plugin)

    def _parse_summary_value(self, tag, step, wall_time, value, plugin):
        """
        Parse summary value and write corresponding file according to plugin.

        Args:
            tag (str): value tag
            step (int): train step
            wall_time (float): Timestamp
            value (Summary.Value): Value message in summary file.
            plugin (str): Plugin value.
        """
        if plugin == SCALAR:
            self._scalar_writer.add((tag, step, wall_time, value.scalar_value))
            self._scalar_check = True

        elif plugin == IMAGE:
            self._image_writer.add((tag, step, value.image.encoded_image))
            self._image_writer.write()
            self._image_check = True
