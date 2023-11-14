# Copyright 2019-2023 Huawei Technologies Co., Ltd
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
import time
from os import path

from google.protobuf.message import DecodeError
from google.protobuf.text_format import ParseError

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.common.enums import PluginNameEnum
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.events_data import EventsData
from mindinsight.datavisual.data_transform.events_data import TensorEvent
from mindinsight.datavisual.data_transform.graph import MSGraph
from mindinsight.datavisual.data_transform.graph import OptimizedGraph
from mindinsight.datavisual.data_transform.histogram import Histogram
from mindinsight.datavisual.data_transform.histogram_container import HistogramContainer
from mindinsight.datavisual.data_transform.image_container import ImageContainer
from mindinsight.datavisual.data_transform.tensor_container import TensorContainer, MAX_TENSOR_COUNT
from mindinsight.datavisual.data_transform.loss_landscape_container import LossLandscapeContainer
from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2
from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2
from mindinsight.datavisual.proto_files import mindinsight_mind_ir_pb2 as mind_ir_pb2
from mindinsight.datavisual.utils.tools import exception_no_raise_wrapper
from mindinsight.utils.computing_resource_mgr import ComputingResourceManager, Executor
from mindinsight.utils.exceptions import UnknownError

HEADER_SIZE = 8
CRC_STR_SIZE = 4
MAX_EVENT_STRING = 500000000


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
        self._parser_list.append(_MindirParser(summary_dir))
        self._is_integrity = True

    @property
    def is_integrity(self):
        return self._is_integrity

    @is_integrity.setter
    def is_integrity(self, integrity):
        self._is_integrity = integrity

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
            logger.info("There are some files has been deleted, "
                        "we will reload all files in path %s.", self._summary_dir)
            self.__init__(self._summary_dir)

    def load(self, executor=None):
        """
        Load all log valid files.

        When the file is reloaded, it will continue to load from where it left off.

        Args:
            executor (Optional[executor]): The Executor instance.

        Returns:
            bool, True if the train job is finished loading.
        """
        logger.debug("Start to load data in ms data loader.")
        if isinstance(executor, Executor):
            return self._load(executor)

        if executor is not None:
            raise TypeError("'executor' should be an Executor instance or None.")

        with ComputingResourceManager.get_instance().get_executor() as new_executor:
            while not self._load(new_executor):
                pass
            return True

    def _load(self, executor):
        """
        Load all log valid files.

        When the file is reloaded, it will continue to load from where it left off.

        Args:
            executor (executor): The Executor instance.

        Returns:
            bool, True if the train job is finished loading.
        """
        filenames = self.filter_valid_files()
        if not filenames:
            logger.warning("No valid files can be loaded, summary_dir: %s.", self._summary_dir)
            raise exceptions.SummaryLogPathInvalid()
        old_filenames = list(self._valid_filenames)
        self._valid_filenames = filenames
        self._check_files_deleted(filenames, old_filenames)

        finished = True
        is_integrity = True
        for parser in self._parser_list:
            finished = parser.parse_files(executor, filenames, events_data=self._events_data) and finished
            is_integrity = parser.is_integrity and is_integrity
        self.is_integrity = is_integrity
        return finished

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
        self._summary_dir = summary_dir
        self._latest_filename = ''
        self._is_integrity = True

    @property
    def is_integrity(self):
        return self._is_integrity

    @is_integrity.setter
    def is_integrity(self, integrity):
        self._is_integrity = integrity

    def parse_files(self, executor, filenames, events_data):
        """
        Load files and parse files content.

        Args:
            executor (Executor): The executor instance.
            filenames (list[str]): File name list.
            events_data (EventsData): The container of event data.
        """
        raise NotImplementedError

    def filter_files(self, filenames):
        """
        Gets a list of files that this parsing class can parse.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.
        """
        raise NotImplementedError


class _PbParser(_Parser):
    """This class is used to parse pb file."""

    def __init__(self, summary_dir):
        super(_PbParser, self).__init__(summary_dir)
        self._latest_mtime = 0

    def parse_files(self, executor, filenames, events_data):
        pb_filenames = self.filter_files(filenames)
        pb_filenames = self.sort_files(pb_filenames)
        for filename in pb_filenames:
            if not self._set_latest_file(filename):
                continue
            future = executor.submit(self._parse_pb_file, self._summary_dir, filename)
            def add_tensor_event(future_value):
                tensor_events = future_value.result()
                for tensor_event in tensor_events:
                    if tensor_event is not None:
                        events_data.add_tensor_event(tensor_event)
            if future is not None:
                future.add_done_callback(exception_no_raise_wrapper(add_tensor_event))
            return False
        return True

    def filter_files(self, filenames):
        """
        Get a list of pb files.

        Args:
            filenames (list[str]): File name list, like [filename1, filename2].

        Returns:
            list[str], filename list.

        Returns:
            bool, True if all the pb files are finished loading.
        """
        return list(filter(lambda filename: re.search(r'\.pb$', filename), filenames))

    def sort_files(self, filenames):
        """Sort by modify time increments and filenames increments."""
        filenames = sorted(filenames, key=lambda file: (
            FileHandler.file_stat(FileHandler.join(self._summary_dir, file)).mtime, file))
        return filenames

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

    @staticmethod
    def _parse_pb_file(summary_dir, filename):
        """
        Parse pb file and write content to `EventsData`.

        Args:
            filename (str): The file path of pb file.

        Returns:
            TensorEvent, if load pb file and build graph success, will return tensor event, else return None.
        """
        file_path = FileHandler.join(summary_dir, filename)
        logger.info("Start to load graph from pb file, file path: %s.", file_path)
        filehandler = FileHandler(file_path)
        model_proto = anf_ir_pb2.ModelProto()
        try:
            model_proto.ParseFromString(filehandler.read())
        except ParseError:
            logger.warning("The given file is not a valid pb file, file path: %s.", file_path)
            return None

        ret_tensor_events = build_graph_events(model_proto.graph, filename, 0, FileHandler.file_stat(file_path).mtime)
        logger.info("Build graph success, file path: %s.", file_path)
        return ret_tensor_events


class _SummaryParser(_Parser):
    """The summary file parser."""

    def __init__(self, summary_dir):
        super(_SummaryParser, self).__init__(summary_dir)
        self._latest_file_size = 0
        self._summary_file_handler = None

    def parse_files(self, executor, filenames, events_data):
        """
        Load summary file and parse file content.

        Args:
            executor (Executor): The executor instance.
            filenames (list[str]): File name list.
            events_data (EventsData): The container of event data.

        Returns:
            bool, True if all the summary files are finished loading.
        """
        summary_files = self.filter_files(filenames)
        summary_files = self.sort_files(summary_files)
        if self._latest_filename in summary_files:
            index = summary_files.index(self._latest_filename)
            summary_files = summary_files[index:]

        for filename in summary_files:
            file_path = FileHandler.join(self._summary_dir, filename)

            if filename != self._latest_filename:
                self._summary_file_handler = FileHandler(file_path, 'rb')
                self._latest_filename = filename
                self._latest_file_size = 0

            new_size = FileHandler.file_stat(file_path).size
            if new_size == self._latest_file_size:
                continue

            try:
                if not self._load_single_file(self._summary_file_handler, executor, events_data):
                    self._latest_file_size = self._summary_file_handler.offset
                else:
                    self._latest_file_size = new_size
                # Wait for data in this file to be processed to avoid loading multiple files at the same time.
                logger.debug("Parse summary file offset %d, file path: %s.", self._latest_file_size, file_path)
                return False
            except UnknownError as ex:
                logger.warning("Parse summary file failed, detail: %r,"
                               "file path: %s.", str(ex), file_path)
        return True

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

    def _load_single_file(self, file_handler, executor, events_data):
        """
        Load a log file data.

        Args:
            file_handler (FileHandler): A file handler.
            executor (Executor): The executor instance.
            events_data (EventsData): The container of event data.

        Returns:
            bool, True if the summary file is finished loading.
        """
        while True:
            start_offset = file_handler.offset
            try:
                self.is_integrity = True
                event_str = self.event_load(file_handler)
                if event_str is None:
                    file_handler.reset_offset(start_offset)
                    return True
                if len(event_str) > MAX_EVENT_STRING:
                    logger.warning("file_path: %s, event string: %d exceeds %d and drop it.",
                                   file_handler.file_path, len(event_str), MAX_EVENT_STRING)
                    continue

                future = executor.submit(self._event_parse, event_str, self._latest_filename)

                def _add_tensor_event_callback(future_value):
                    tensor_values = future_value.result()
                    for tensor_value in tensor_values:
                        if tensor_value.plugin_name == PluginNameEnum.GRAPH.value:
                            try:
                                graph_tags = events_data.list_tags_by_plugin(PluginNameEnum.GRAPH.value)
                            except KeyError:
                                graph_tags = []

                            summary_tags = self.filter_files(graph_tags)
                            for tag in summary_tags:
                                events_data.delete_tensor_event(tag)

                        events_data.add_tensor_event(tensor_value)

                if future is not None:
                    future.add_done_callback(exception_no_raise_wrapper(_add_tensor_event_callback))
                return False
            except exceptions.CRCLengthFailedError as exc:
                file_handler.reset_offset(start_offset)
                file_size = file_handler.file_stat(file_handler.file_path).size
                logger.error("Check crc failed and ignore this file, please check the integrity of the file, "
                             "file_path: %s, offset: %s, file size: %s. Detail: %s.",
                             file_handler.file_path, file_handler.offset, file_size, str(exc))
                self.is_integrity = False
                modify_time = path.getmtime(file_handler.file_path)
                current_time = time.time()
                if current_time - modify_time > 600:
                    logger.error("The file: %s is damaged.", file_handler.file_path)
                    return True
                return False
            except (OSError, DecodeError, exceptions.MindInsightException) as ex:
                logger.error("Parse log file fail, and ignore this file, detail: %r, "
                             "file path: %s.", str(ex), file_handler.file_path)
                return True
            except Exception as ex:
                logger.exception(ex)
                raise UnknownError(str(ex))

    @staticmethod
    def event_load(file_handler):
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
            logger.info("Load summary file finished, file_path=%s.", file_handler.file_path)
            return None
        header_crc_str = file_handler.read(CRC_STR_SIZE)
        if not header_crc_str:
            header_crc_str = ''

        if len(header_str) != HEADER_SIZE or len(header_crc_str) != CRC_STR_SIZE:
            raise exceptions.CRCLengthFailedError("CRC header length or event header length is incorrect.")

        # read the event body if integrity of header is verified
        header = struct.unpack('Q', header_str)
        event_len = int(header[0])
        if event_len <= 0:
            raise exceptions.CRCLengthFailedError("The event length from header is no more than zero.")

        event_str = file_handler.read(event_len)
        if not event_str:
            event_str = b''
        event_crc_str = file_handler.read(CRC_STR_SIZE)
        if not event_crc_str:
            event_crc_str = ''

        if len(event_str) != event_len or len(event_crc_str) != CRC_STR_SIZE:
            raise exceptions.CRCLengthFailedError("The event string length or crc length is incorrect.")

        return event_str

    @staticmethod
    def _parse_summary_value(value, plugin):
        """
        Parse summary value and create corresponding container according to plugin.

        Args:
            value (Summary.Value): Value message in summary file.
            plugin (str): Plugin value.

        Returns:
            Union[Summary.Value, HistogramContainer, TensorContainer, ImageContainer], original summary value
            or an instance of  HistogramContainer or TensorContainer or ImageContainer.
        """
        tensor_event_value = getattr(value, plugin)
        if plugin == PluginNameEnum.HISTOGRAM.value:
            tensor_event_value = HistogramContainer(tensor_event_value)
            # Drop steps if original_buckets_count exceeds HistogramContainer.MAX_ORIGINAL_BUCKETS_COUNT
            # to avoid time-consuming re-sample process.
            if tensor_event_value.histogram.original_buckets_count > Histogram.MAX_ORIGINAL_BUCKETS_COUNT:
                logger.info('original_buckets_count exceeds '
                            'HistogramContainer.MAX_ORIGINAL_BUCKETS_COUNT')
                return None

        elif plugin == PluginNameEnum.TENSOR.value:
            tensor_event_value = TensorContainer(tensor_event_value)
            if tensor_event_value.error_code is not None:
                logger.warning('tag: %s/tensor, dims: %s, tensor count: %d exceeds %d and drop it.',
                               value.tag, tensor_event_value.dims, tensor_event_value.size, MAX_TENSOR_COUNT)

        elif plugin == PluginNameEnum.IMAGE.value:
            tensor_event_value = ImageContainer(tensor_event_value)

        elif plugin == PluginNameEnum.LANDSCAPE.value:
            tensor_event_value = LossLandscapeContainer(tensor_event_value)

        return tensor_event_value

    @staticmethod
    def _event_parse(event_str, latest_file_name):
        """
        Transform `Event` data to tensor_event and update it to EventsData.

        This method is static to avoid sending unnecessary objects to other processes.

        Args:
            event_str (str): Message event string in summary proto, data read from file handler.
            latest_file_name (str): Latest file name.
        """

        plugins = {
            'scalar_value': PluginNameEnum.SCALAR,
            'image': PluginNameEnum.IMAGE,
            'histogram': PluginNameEnum.HISTOGRAM,
            'tensor': PluginNameEnum.TENSOR,
            'loss_landscape': PluginNameEnum.LANDSCAPE
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
                    logger.debug("Processing plugin value: %s.", plugin_name_enum)
                    tensor_event_value = _SummaryParser._parse_summary_value(value, plugin)
                    if tensor_event_value is None:
                        continue

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
            ret_tensor_events.extend(build_graph_events(event.graph_def, latest_file_name, event.step, event.wall_time))

        return ret_tensor_events

    def sort_files(self, filenames):
        """Sort by creating time increments and filenames decrement."""
        filenames = sorted(filenames,
                           key=lambda filename: (-int(re.search(r'summary\.(\d+)', filename)[1]), filename),
                           reverse=True)
        return filenames


class _MindirParser(_Parser):
    def __init__(self, summary_dir):
        super(_MindirParser, self).__init__(summary_dir)
        self._latest_mtime = 0

    def parse_files(self, executor, filenames, events_data):
        mindir_filenames=self.filter_files(filenames)
        mindir_filenames=self.sort_files(mindir_filenames)
        for filename in mindir_filenames:
            if not self._set_latest_file(filename):
                continue
            future = executor.submit(self._parse_mindir_file, self._summary_dir, filename)

            def add_tensor_event(future_value):
                tensor_events = future_value.result()
                for tensor_event in tensor_events:
                    if tensor_event is not None:
                        events_data.add_tensor_event(tensor_event)

            if future is not None:
                future.add_done_callback(exception_no_raise_wrapper(add_tensor_event))
            return False
        return True
    def filter_files(self, filenames):
        return list(filter(lambda filename: re.search(r'\.mindir$', filename), filenames))

    def sort_files(self, filenames):
        """Sort by modify time increments and filenames increments."""
        filenames = sorted(filenames, key=lambda file: (
            FileHandler.file_stat(FileHandler.join(self._summary_dir, file)).mtime, file))
        return filenames

    def _set_latest_file(self, filename):
        mtime = FileHandler.file_stat(FileHandler.join(self._summary_dir, filename)).mtime
        if mtime < self._latest_mtime or \
                (mtime == self._latest_mtime and filename <= self._latest_filename):
            return False

        self._latest_mtime = mtime
        self._latest_filename = filename

        return True

    @staticmethod
    def _parse_mindir_file(summary_dir, filename):
        """
        Parse mindir file and write content to `EventsData`.

        Args:
            filename (str): The file path of mindir file.

        Returns:
            TensorEvent, if load mindir file and build graph success, will return tensor event, else return None.
        """
        file_path = FileHandler.join(summary_dir, filename)
        logger.info("Start to load graph from mindir file, file path: %s.", file_path)
        filehandler = FileHandler(file_path)
        model_proto = mind_ir_pb2.ModelProto()

        try:
            model_proto.ParseFromString(filehandler.read())
        except ParseError:
            logger.warning("The given file is not a valid mindir file, file path: %s.", file_path)
            return None
        ret_tensor_events = build_graph_events(model_proto, filename, 0, FileHandler.file_stat(file_path).mtime,True)

        logger.info("Build graph success, file path: %s.", file_path)
        return ret_tensor_events


def build_graph_events(graph_proto, filename, step, wall_time, mindir_graph=False):
    """Build graph events for MSgraph and OptimizedGraph."""
    ret_tensor_events = []
    graph_event = build_graph_event(graph_proto, PluginNameEnum.GRAPH.value, filename, step, wall_time, mindir_graph)
    if graph_event.value.list_node_by_scope():
        ret_tensor_events.append(graph_event)
    optimized_graph_event = build_graph_event(graph_proto, PluginNameEnum.OPTIMIZED_GRAPH.value, filename, step,
                                              wall_time, mindir_graph)
    if optimized_graph_event.value.list_node_by_scope():
        ret_tensor_events.append(optimized_graph_event)
    return ret_tensor_events


def build_graph_event(graph_proto, plugin, filename, step, wall_time, mindir_graph=False):
    """Build a graph event."""
    graph = MSGraph() if plugin == PluginNameEnum.GRAPH.value else OptimizedGraph()

    try:
        graph.build_graph(graph_proto, mindir_graph)

    except Exception as ex:
        # Normally, there are no exceptions, and it is only possible for users on the MindSpore side
        # to dump other non-default graphs.
        logger.error("Build graph failed, file path: %s.", filename)
        logger.exception(ex)
        raise UnknownError(str(ex))

    tensor_event = TensorEvent(wall_time=wall_time,
                               step=step,
                               tag=filename if plugin == PluginNameEnum.GRAPH.value else filename + " (optimized)",
                               plugin_name=plugin,
                               value=graph,
                               filename=filename)
    return tensor_event
