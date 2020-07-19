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
"""
DataLoader for MindSpore data.

This module is used to load the MindSpore training log file.
Each instance will read an entire run, a run can contain one or
more log file.
"""
import re
import struct

from google.protobuf.message import DecodeError
from google.protobuf.text_format import ParseError

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.events_data import EventsData
from mindinsight.datavisual.data_transform.events_data import TensorEvent
from mindinsight.datavisual.data_transform.graph import MSGraph
from mindinsight.datavisual.data_transform.histogram import Histogram
from mindinsight.datavisual.data_transform.histogram_container import HistogramContainer
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer
from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2
from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2
from mindinsight.datavisual.utils import crc32
from mindinsight.utils.exceptions import UnknownError

HEADER_SIZE = 8
CRC_STR_SIZE = 4


class MSDataLoader:
    """
    MSDataLoader class, load MindSpore event data.

    Args:
        summary_dir (str): Log directory.
    """

    def __init__(self, summary_dir):
        self._summary_dir = summary_dir
        self._valid_filenames = []
        self._events_data = EventsData()

        self._parser_list = []
        self._parser_list.append(_SummaryParser(summary_dir))
        self._parser_list.append(_PbParser(summary_dir))

    def get_events_data(self):
        """Return events data read from log file."""
        return self._events_data

    def _check_files_deleted(self, filenames, old_filenames):
        """
        Check the file list for updates.

        Args:
            filenames (list[str]): The latest files list.
            old_filenames (list[str]): List of old files.
        """
        deleted_files = set(old_filenames) - set(filenames)
        if deleted_files:
            logger.warning("There are some files has been deleted, "
                           "we will reload all files in path %s.", self._summary_dir)
            self.__init__(self._summary_dir)

    def load(self, computing_resource_mgr):
        """
        Load all log valid files.

        When the file is reloaded, it will continue to load from where it left off.

        Args:
            computing_resource_mgr (ComputingResourceManager): The ComputingResourceManager instance.
        """
        logger.debug("Start to load data in ms data loader.")
        filenames = self.filter_valid_files()
        if not filenames:
            logger.warning("No valid files can be loaded, summary_dir: %s.", self._summary_dir)
            raise exceptions.SummaryLogPathInvalid()
        old_filenames = list(self._valid_filenames)
        self._valid_filenames = filenames
        self._check_files_deleted(filenames, old_filenames)

        with computing_resource_mgr.get_executor() as executor:
            for parser in self._parser_list:
                parser.parse_files(executor, filenames, events_data=self._events_data)

    def filter_valid_files(self):
        """
        Gets a list of valid files from the given file path.

        Returns:
            list[str], file name list.

        """
        filenames = []
        for filename in FileHandler.list_dir(self._summary_dir):
            if FileHandler.is_file(FileHandler.join(self._summary_dir, filename)):
                filenames.append(filename)

        valid_filenames = []
        for parser in self._parser_list:
            valid_filenames.extend(parser.filter_files(filenames))

        return list(set(valid_filenames))


class _Parser:
    """Parsed base class."""

    def __init__(self, summary_dir):
        self._latest_filename = ''
        self._latest_mtime = 0
        self._summary_dir = summary_dir

    def parse_files(self, executor, filenames, events_data):
        """
        Load files and parse files content.

        Args:
            executor (Executor): The executor instance.
            filenames (list[str]): File name list.
            events_data (EventsData): The container of event data.
        """
        raise NotImplementedError

    def sort_files(self, filenames):
        """Sort by modify time increments and filenames increments."""
        filenames = sorted(filenames, key=lambda file: (
            FileHandler.file_stat(FileHandler.join(self._summary_dir, file)).mtime, file))
        return filenames

    def filter_files(self, filenames):
        """
        Gets a list of files that this parsing class can parse.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.
        """
        raise NotImplementedError

    def _set_latest_file(self, filename):
        """
        Check if the file's modification time is newer than the last time it was loaded, and if so, set the time.

        Args:
            filename (str): The file name that needs to be checked and set.

        Returns:
            bool, Returns True if the file was modified earlier than the last time it was loaded, or False.
        """
        mtime = FileHandler.file_stat(FileHandler.join(self._summary_dir, filename)).mtime
        if mtime < self._latest_mtime or \
                (mtime == self._latest_mtime and filename <= self._latest_filename):
            return False

        self._latest_mtime = mtime
        self._latest_filename = filename

        return True


class _PbParser(_Parser):
    """This class is used to parse pb file."""

    def parse_files(self, executor, filenames, events_data):
        pb_filenames = self.filter_files(filenames)
        pb_filenames = self.sort_files(pb_filenames)
        for filename in pb_filenames:
            if not self._set_latest_file(filename):
                continue

            try:
                tensor_event = self._parse_pb_file(filename)
            except UnknownError:
                # Parse pb file failed, so return None.
                continue

            events_data.add_tensor_event(tensor_event)

    def filter_files(self, filenames):
        """
        Get a list of pb files.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.
        """
        return list(filter(lambda filename: re.search(r'\.pb$', filename), filenames))

    def _parse_pb_file(self, filename):
        """
        Parse pb file and write content to `EventsData`.

        Args:
            filename (str): The file path of pb file.

        Returns:
            TensorEvent, if load pb file and build graph success, will return tensor event, else return None.
        """
        file_path = FileHandler.join(self._summary_dir, filename)
        logger.info("Start to load graph from pb file, file path: %s.", file_path)
        filehandler = FileHandler(file_path)
        model_proto = anf_ir_pb2.ModelProto()
        try:
            model_proto.ParseFromString(filehandler.read())
        except ParseError:
            logger.warning("The given file is not a valid pb file, file path: %s.", file_path)
            return None

        graph = MSGraph()

        try:
            graph.build_graph(model_proto.graph)
        except Exception as ex:
            # Normally, there are no exceptions, and it is only possible for users on the MindSpore side
            # to dump other non-default graphs.
            logger.error("Build graph failed, file path: %s.", file_path)
            logger.exception(ex)
            raise UnknownError(str(ex))

        tensor_event = TensorEvent(wall_time=FileHandler.file_stat(file_path),
                                   step=0,
                                   tag=filename,
                                   plugin_name=PluginNameEnum.GRAPH.value,
                                   value=graph,
                                   filename=filename)

        logger.info("Build graph success, file path: %s.", file_path)
        return tensor_event


class _SummaryParser(_Parser):
    """The summary file parser."""

    def __init__(self, summary_dir):
        super(_SummaryParser, self).__init__(summary_dir)
        self._latest_file_size = 0
        self._summary_file_handler = None
        self._events_data = None

    def parse_files(self, executor, filenames, events_data):
        """
        Load summary file and parse file content.

        Args:
            executor (Executor): The executor instance.
            filenames (list[str]): File name list.
            events_data (EventsData): The container of event data.
        """
        self._events_data = events_data
        summary_files = self.filter_files(filenames)
        summary_files = self.sort_files(summary_files)

        for filename in summary_files:
            if self._latest_filename and \
                    (self._compare_summary_file(self._latest_filename, filename)):
                continue

            file_path = FileHandler.join(self._summary_dir, filename)

            if filename != self._latest_filename:
                self._summary_file_handler = FileHandler(file_path, 'rb')
                self._latest_filename = filename
                self._latest_file_size = 0

            new_size = FileHandler.file_stat(file_path).size
            if new_size == self._latest_file_size:
                continue

            self._latest_file_size = new_size
            try:
                self._load_single_file(self._summary_file_handler, executor)
                # Wait for data in this file to be processed to avoid loading multiple files at the same time.
                executor.wait_all_tasks_finish()
            except UnknownError as ex:
                logger.warning("Parse summary file failed, detail: %r,"
                               "file path: %s.", str(ex), file_path)

    def filter_files(self, filenames):
        """
        Gets a list of summary files.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.
        """
        return list(filter(
            lambda filename: (re.search(r'summary\.\d+', filename)
                              and not filename.endswith("_lineage")), filenames))

    def _load_single_file(self, file_handler, executor):
        """
        Load a log file data.

        Args:
            file_handler (FileHandler): A file handler.
            executor (Executor): The executor instance.
        """
        while True:
            start_offset = file_handler.offset
            try:
                event_str = self._event_load(file_handler)
                if event_str is None:
                    file_handler.reset_offset(start_offset)
                    break

                future = executor.submit(self._event_parse, event_str, self._latest_filename)

                def _add_tensor_event_callback(future_value):
                    try:
                        tensor_values = future_value.result()
                        for tensor_value in tensor_values:
                            if tensor_value.plugin_name == PluginNameEnum.GRAPH.value:
                                try:
                                    graph_tags = self._events_data.list_tags_by_plugin(PluginNameEnum.GRAPH.value)
                                except KeyError:
                                    graph_tags = []

                                summary_tags = self.filter_files(graph_tags)
                                for tag in summary_tags:
                                    self._events_data.delete_tensor_event(tag)

                            self._events_data.add_tensor_event(tensor_value)
                    except Exception as exc:
                        # Log exception for debugging.
                        logger.exception(exc)
                        raise

                future.add_done_callback(_add_tensor_event_callback)
            except exceptions.CRCFailedError:
                file_handler.reset_offset(start_offset)
                logger.warning("Check crc faild and ignore this file, file_path=%s, "
                               "offset=%s.", file_handler.file_path, file_handler.offset)
                break
            except (OSError, DecodeError, exceptions.MindInsightException) as ex:
                logger.warning("Parse log file fail, and ignore this file, detail: %r,"
                               "file path: %s.", str(ex), file_handler.file_path)
                break
            except Exception as ex:
                logger.exception(ex)
                raise UnknownError(str(ex))

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
            logger.info("End of file, file_path=%s.", file_handler.file_path)
            return None
        header_crc_str = file_handler.read(CRC_STR_SIZE)
        if not header_crc_str:
            header_crc_str = ''

        if len(header_str) != HEADER_SIZE or len(header_crc_str) != CRC_STR_SIZE:
            logger.warning("Check header size and crc, record truncated at offset %s, "
                           "file_path=%s.", file_handler.offset, file_handler.file_path)
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
            logger.warning("Check event crc, record truncated at offset %d, file_path: %s.",
                           file_handler.offset, file_handler.file_path)
            return None
        if not crc32.CheckValueAgainstData(event_crc_str, event_str, event_len):
            raise exceptions.CRCFailedError()

        return event_str

    @staticmethod
    def _event_parse(event_str, latest_file_name):
        """
        Transform `Event` data to tensor_event and update it to EventsData.

        This method is static to avoid sending unnecessary objects to other processes.

        Args:
            event (str): Message event string in summary proto, data read from file handler.
            latest_file_name (str): Latest file name.
        """

        plugins = {
            'scalar_value': PluginNameEnum.SCALAR,
            'image': PluginNameEnum.IMAGE,
            'histogram': PluginNameEnum.HISTOGRAM,
            'tensor': PluginNameEnum.TENSOR
        }
        logger.debug("Start to parse event string. Event string len: %s.", len(event_str))
        event = summary_pb2.Event.FromString(event_str)
        logger.debug("Deserialize event string completed.")

        ret_tensor_events = []
        if event.HasField('summary'):
            for value in event.summary.value:
                for plugin in plugins:
                    if not value.HasField(plugin):
                        continue
                    plugin_name_enum = plugins[plugin]
                    tensor_event_value = getattr(value, plugin)
                    logger.debug("Processing plugin value: %s.", plugin_name_enum)

                    if plugin == 'histogram':
                        tensor_event_value = HistogramContainer(tensor_event_value)
                        # Drop steps if original_buckets_count exceeds HistogramContainer.MAX_ORIGINAL_BUCKETS_COUNT
                        # to avoid time-consuming re-sample process.
                        if tensor_event_value.histogram.original_buckets_count > Histogram.MAX_ORIGINAL_BUCKETS_COUNT:
                            logger.info('original_buckets_count exceeds '
                                        'HistogramContainer.MAX_ORIGINAL_BUCKETS_COUNT')
                            continue
                    elif plugin == 'tensor':
                        tensor_event_value = TensorContainer(tensor_event_value)

                    tensor_event = TensorEvent(wall_time=event.wall_time,
                                               step=event.step,
                                               tag='{}/{}'.format(value.tag, plugin_name_enum.value),
                                               plugin_name=plugin_name_enum.value,
                                               value=tensor_event_value,
                                               filename=latest_file_name)
                    logger.debug("Tensor event generated, plugin is %s, tag is %s, step is %s.",
                                 plugin_name_enum, value.tag, event.step)
                    ret_tensor_events.append(tensor_event)

        elif event.HasField('graph_def'):
            graph = MSGraph()
            graph.build_graph(event.graph_def)
            tensor_event = TensorEvent(wall_time=event.wall_time,
                                       step=event.step,
                                       tag=latest_file_name,
                                       plugin_name=PluginNameEnum.GRAPH.value,
                                       value=graph,
                                       filename=latest_file_name)
            ret_tensor_events.append(tensor_event)

        return ret_tensor_events

    @staticmethod
    def _compare_summary_file(current_file, dst_file):
        """
        Compare the creation times of the two summary log files.

        Args:
            current_file (str): Must be the summary log file path.
            dst_file (str): Must be the summary log file path.

        Returns:
            bool, returns True if the current file is new, or False if not.
        """
        current_time = int(re.search(r'summary\.(\d+)', current_file)[1])
        dst_time = int(re.search(r'summary\.(\d+)', dst_file)[1])
        if current_time > dst_time or (current_time == dst_time and current_file > dst_file):
            return True
        return False

    def sort_files(self, filenames):
        """Sort by creating time increments and filenames decrement."""
        filenames = sorted(filenames,
                           key=lambda filename: (-int(re.search(r'summary\.(\d+)', filename)[1]), filename),
                           reverse=True)
        return filenames
