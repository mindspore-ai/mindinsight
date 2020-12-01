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
"""This module provides python APIs to get lineage summary from summary log."""
import struct
from collections import namedtuple
from enum import Enum

from google.protobuf.json_format import MessageToDict
from google.protobuf.message import DecodeError

from mindinsight.datavisual.proto_files.mindinsight_lineage_pb2 import LineageEvent
from mindinsight.datavisual.utils import crc32
from mindinsight.lineagemgr.common.exceptions.exceptions import MindInsightException, \
    LineageVerificationException, LineageSummaryAnalyzeException
from mindinsight.lineagemgr.common.log import logger as log
from mindinsight.lineagemgr.common.validator.validate_path import safe_normalize_path
from mindinsight.lineagemgr.summary.file_handler import FileHandler

LineageInfo = namedtuple('LineageInfo', ['train_lineage', 'eval_lineage', 'dataset_graph'])


class SummaryTag(Enum):
    """The tag value of lineage fields."""

    # the value is `field_number << 3 | wire_type`
    WALL_TIME = 'wall_time'
    STEP = 'step'
    VERSION = 'version'
    GRAPH = 'graph'
    SUMMARY = 'summary'
    TRAIN_LINEAGE = 'train_lineage'
    EVAL_LINEAGE = 'evaluation_lineage'
    DATASET_GRAPH = 'dataset_graph'


class SummaryAnalyzer:
    """
    Summary log Analyzer.

    Args:
        file_path (str): The path of summary log.

    Raises:
        LineageVerificationException: Raise when verification failed.
    """
    HEADER_SIZE = 8
    HEADER_CRC_SIZE = 4
    BODY_CRC_SIZE = 4

    def __init__(self, file_path):
        self.file_handler = FileHandler(file_path)

    def load_events(self):
        """
        Load events in summary log.

        Returns:
            generator, the event generator.
        """
        while self._has_next():
            yield self._read_event()

    def _has_next(self):
        """
        Check if the file has reached the end.

        Returns:
            bool, whether the file has reached the end.
        """
        current_offset = self.file_handler.tell()
        if current_offset < self.file_handler.size:
            return True

        return False

    def _read_event(self):
        """
        Read event.

        Returns:
            LineageEvent, the event body.
        """
        body_size = self._read_header()
        body_str = self._read_body(body_size)
        event = LineageEvent().FromString(body_str)
        return event

    def _read_header(self):
        """
        Read header information.

        Returns:
            int, the length of event body.
        """
        header_str = self.file_handler.read(self.HEADER_SIZE)
        header_crc_str = self.file_handler.read(self.HEADER_CRC_SIZE)
        SummaryAnalyzer._check_crc(header_str, header_crc_str)

        body_len = struct.unpack("<Q", header_str)[0]

        return body_len

    def _read_body(self, body_size):
        """
        Read event body information.

        Args:
            body_size (int): The size of event body.

        Returns:
            bytes, the event body in bytes.
        """
        body_str = self.file_handler.read(body_size)
        body_crc_str = self.file_handler.read(self.BODY_CRC_SIZE)
        SummaryAnalyzer._check_crc(body_str, body_crc_str)

        return body_str

    @staticmethod
    def _check_crc(source_str, crc_str):
        """
        Check the integrity of source string.

        Args:
            source_str (bytes): Source string in bytes.
            crc_str (bytes): CRC string of source string in bytes.

        Raises:
            LineageVerificationException: Raise when verification failed.
        """
        if not crc32.CheckValueAgainstData(crc_str, source_str, len(source_str)):
            log.debug("The CRC verification not pass. source_str: %s. crc_str: %s.", source_str, crc_str)
            raise LineageVerificationException("The CRC verification failed.")


class LineageSummaryAnalyzer(SummaryAnalyzer):
    """
    Summary log analyzer for lineage information.

    Args:
        file_path (str): The path of summary log.

    Raises:
        LineageSummaryAnalyzeException: If failed to get lineage information.
    """

    def __init__(self, file_path):
        file_path = safe_normalize_path(file_path, 'lineage_summary_path', None)
        super(LineageSummaryAnalyzer, self).__init__(file_path)

    def get_latest_info(self):
        """
        Get latest lineage info in summary log file.

        Returns:
            LineageInfo, the lineage summary information.
        """
        lineage_events = {
            SummaryTag.TRAIN_LINEAGE: None,
            SummaryTag.EVAL_LINEAGE: None,
            SummaryTag.DATASET_GRAPH: None
        }
        for event in self.load_events():
            for tag, _ in lineage_events.items():
                if event.HasField(tag.value):
                    lineage_events[tag] = event
                    break

        lineage_info = LineageInfo(
            train_lineage=lineage_events.get(SummaryTag.TRAIN_LINEAGE),
            eval_lineage=lineage_events.get(SummaryTag.EVAL_LINEAGE),
            dataset_graph=lineage_events.get(SummaryTag.DATASET_GRAPH)
        )

        return lineage_info

    @classmethod
    def get_summary_infos(cls, file_path):
        """
        Get lineage summary information from summary log file.

        Args:
            file_path (str): The file path of summary log.

        Returns:
            LineageInfo, the lineage summary information.

        Raises:
            LineageSummaryAnalyzeException: If failed to get lineage information.
        """
        analyzer = cls(file_path)
        err_msg = "Can not analyze lineage info, file path is %s. Detail: %s"
        try:
            lineage_info = analyzer.get_latest_info()
        except (MindInsightException, IOError, DecodeError) as err:
            log.debug(err_msg, file_path, str(err))
            raise LineageSummaryAnalyzeException(str(err))
        except Exception as err:
            log.debug(err_msg, file_path, str(err))
            raise LineageSummaryAnalyzeException(str(err))

        return lineage_info

    @staticmethod
    def get_user_defined_info(file_path):
        """
        Get user defined info.
        Args:
            file_path (str): The file path of summary log.

        Returns:
            list, the list of dict format user defined information
                which converted from proto message.
        """
        all_user_message = []
        summary_analyzer = SummaryAnalyzer(file_path)

        for event in summary_analyzer.load_events():
            if event.HasField("user_defined_info"):
                user_defined_info = MessageToDict(
                    event,
                    preserving_proto_field_name=True
                ).get("user_defined_info")
                user_dict = LineageSummaryAnalyzer._get_dict_from_proto(user_defined_info)
                all_user_message.append(user_dict)

        return all_user_message

    @staticmethod
    def _get_dict_from_proto(user_defined_info):
        """
        Convert the proto message UserDefinedInfo to its dict format.

        Args:
            user_defined_info (UserDefinedInfo): The proto message of user defined info.

        Returns:
            dict, the converted dict.
        """
        user_dict = dict()
        proto_dict = user_defined_info.get("user_info")
        for proto_item in proto_dict:
            if proto_item and isinstance(proto_item, dict):
                key, value = list(list(proto_item.values())[0].items())[0]
                if isinstance(value, dict):
                    user_dict[key] = LineageSummaryAnalyzer._get_dict_from_proto(value)
                else:
                    user_dict[key] = value

        return user_dict
