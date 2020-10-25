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
"""
Scalar Writer.

This module write scalar into a  csv file.
"""
import os
import struct

from google.protobuf.message import DecodeError

from mindinsight.datavisual.utils import crc32
from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.log import parse_summary_logger
from mindinsight.datavisual.proto_files import lazy_read_pb2
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.summary_parser.image_writer import ImageWriter
from mindinsight.datavisual.data_transform.summary_parser.scalar_writer import ScalarWriter
from mindinsight.datavisual.data_transform.ms_data_loader import _SummaryParser
from mindinsight.utils.exceptions import UnknownError

HEADER_SIZE = 8
CRC_STR_SIZE = 4
MAX_EVENT_STRING = 500000000
SCALAR = 'scalar_value'
IMAGE = 'image'


class EventParser():
    """Parse summary file and save it to csv file and image."""
    def __init__(self, summary_dir, output):
        self._summary_dir = summary_dir
        self._output = output
        self._scalar_writer = ScalarWriter(self._output)
        self._image_writer = ImageWriter(FileHandler.join(self._output, IMAGE))
        self._current = 0
        self._file_size = 0
        self._process_info = 0
        self._image_check = False
        self._scalar_check = False

    def parse(self):
        """Load summary file and parse file content."""
        try:
            if not (self._check_filepath() and self._check_create_filepath(
                    self._output) and self._check_create_filepath(FileHandler.join(self._output, IMAGE))):
                return

            summary_parser = _SummaryParser(self._summary_dir)
            summary_files = summary_parser.filter_files(os.listdir(self._summary_dir))

            if not summary_files:
                parse_summary_logger.error('Path %s has no summary file.', self._summary_dir)
                return

            summary_files = summary_parser.sort_files(summary_files)

            filename = summary_files[-1]
            file_path = FileHandler.join(self._summary_dir, filename)

            if not os.access(file_path, os.R_OK):
                parse_summary_logger.error('Path %s is not accessible, please check the file-authority.', file_path)
                return

            self._summary_file_handler = FileHandler(file_path, 'rb')

            self._file_size = os.path.getsize(file_path)
            # when current parsed size bigger than self._process_info, print process
            self._process_info = self._file_size // 10

            parse_summary_logger.info("loading %s", file_path)
            result = self._load(self._summary_file_handler)

            self._scalar_writer.write()

            warning = ''

            if not self._scalar_check:
                warning = warning + " the summary file contains no scalar value"
            if not self._image_check:
                warning = warning + " the summary file contains no image"
            if result:
                if warning:
                    parse_summary_logger.warning(warning)
                parse_summary_logger.info("parsing summary file finished")

        except Exception as ex:
            parse_summary_logger.error("Parse summary file failed, detail: %r", str(ex))
            raise UnknownError(str(ex))

    def _load(self, file_handler):
        """
        Load a log file data.

        Args:
            file_handler (FileHandler): A file handler.

        Returns:
            bool, True if the summary file is finished loading.
        """
        while True:
            try:
                event_str = self._event_load(file_handler)
                if event_str is None:
                    return True
                if len(event_str) > MAX_EVENT_STRING:
                    parse_summary_logger.warning("file_path: %s, event string: %d exceeds %d and drop it.",
                                                 file_handler.file_path, len(event_str), MAX_EVENT_STRING)
                    continue
                self._event_parse(event_str)
            except exceptions.CRCFailedError:
                parse_summary_logger.error("Check crc faild, file_path=%s, offset=%s.", file_handler.file_path,
                                           file_handler.offset)
                return False
            except (OSError, DecodeError, exceptions.MindInsightException) as ex:
                parse_summary_logger.error("Parse file fail, detail: %r, file path: %s.", str(ex),
                                           file_handler.file_path)
                return False

    def _event_load(self, file_handler):
        """
        Load binary string to event string.

        Args:
            file_handler (FileHandler): A file handler.

        Returns:
            bytes, MindSpore event in bytes.
        """
        # read the header
        header_str = file_handler.read(HEADER_SIZE)

        if not header_str:
            return None

        header_crc_str = file_handler.read(CRC_STR_SIZE)
        if not header_crc_str:
            header_crc_str = ''

        if len(header_str) != HEADER_SIZE or len(header_crc_str) != CRC_STR_SIZE:
            parse_summary_logger.error("Check header size and crc, record truncated at offset %s, file_path=%s.",
                                       file_handler.offset, file_handler.file_path)
            return None
        if not crc32.CheckValueAgainstData(header_crc_str, header_str, HEADER_SIZE):
            raise exceptions.CRCFailedError()

        # read the event body if integrity of header is verified
        header = struct.unpack('Q', header_str)
        event_len = int(header[0])

        event_str = file_handler.read(event_len)
        if not event_str:
            event_str = ''
        event_crc_str = file_handler.read(CRC_STR_SIZE)
        if not event_crc_str:
            event_crc_str = ''

        if len(event_str) != event_len or len(event_crc_str) != CRC_STR_SIZE:
            parse_summary_logger.error("Check event crc, record truncated at offset %d, file_path: %s.",
                                       file_handler.offset, file_handler.file_path)
            return None
        if not crc32.CheckValueAgainstData(event_crc_str, event_str, event_len):
            raise exceptions.CRCFailedError()
        self._current += HEADER_SIZE + 2 * CRC_STR_SIZE + event_len
        if self._current > self._process_info:
            parse_summary_logger.info("current process: %d/%d, %d%%", self._current, self._file_size,
                                      100 * self._current // self._file_size)
            self._process_info += self._file_size // 10
        return event_str

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

    def _check_filepath(self):
        """Check file path existence, accessible and available"""
        if os.path.exists(self._summary_dir):
            if not os.path.isdir(self._summary_dir):
                parse_summary_logger.error('Path of summary directory is not a valid directory.')
                return False
            if not os.access(self._summary_dir, os.R_OK | os.X_OK):
                parse_summary_logger.error('Path %s is not accessible, please check the file-authority.',
                                           self._summary_dir)
            return True
        parse_summary_logger.error('Path of summary directory not exists.')
        return False

    def _check_create_filepath(self, filepath):
        """Check file path existence, accessible and available, if not exist create the file"""
        permissions = os.R_OK | os.W_OK | os.X_OK
        os.umask(permissions << 3 | permissions)
        if os.path.exists(filepath):
            parse_summary_logger.error('Path %s has already existed, please choose a new output path.', filepath)
            return False
        mode = permissions << 6
        os.makedirs(filepath, mode=mode)
        return True
