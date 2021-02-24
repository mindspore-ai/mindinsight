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
"""
File parser for MindExplain data.

This module is used to parse the MindExplain log file.
"""
from collections import namedtuple

from mindinsight.datavisual.common import exceptions
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.ms_data_loader import _SummaryParser
from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2
from mindinsight.explainer.common.enums import ExplainFieldsEnum
from mindinsight.explainer.common.log import logger
from mindinsight.utils.exceptions import UnknownError

HEADER_SIZE = 8
CRC_STR_SIZE = 4
MAX_EVENT_STRING = 500000000

BenchmarkContainer = namedtuple('BenchmarkContainer', ['benchmark', 'status'])
MetadataContainer = namedtuple('MetadataContainer', ['metadata', 'status'])
InferfenceContainer = namedtuple('InferenceContainer', ['ground_truth_prob',
                                                        'ground_truth_prob_sd',
                                                        'ground_truth_prob_itl95_low',
                                                        'ground_truth_prob_itl95_hi',
                                                        'predicted_label',
                                                        'predicted_prob',
                                                        'predicted_prob_sd',
                                                        'predicted_prob_itl95_low',
                                                        'predicted_prob_itl95_hi'])
SampleContainer = namedtuple('SampleContainer', ['sample_id', 'image_path', 'ground_truth_label', 'inference',
                                                 'explanation', 'hierarchical_occlusion', 'status'])


class ExplainParser(_SummaryParser):
    """The summary file parser."""

    def __init__(self, summary_dir):
        super(ExplainParser, self).__init__(summary_dir)
        self._latest_offset = 0

    def list_events(self, filenames):
        """
        Load summary file and parse file content.

        Args:
            filenames (list[str]): File name list.

        Returns:
            tuple, the elements of the tuple are:

                - file_changed (bool): True if the latest file is changed.
                - is_end (bool): True if all the summary files are finished loading.
                - event_data (dict): Event data where keys are explanation field.
        """
        summary_files = self.sort_files(filenames)

        is_end = False
        file_changed = False
        event_data = {}
        filename = summary_files[-1]

        file_path = FileHandler.join(self._summary_dir, filename)
        if filename != self._latest_filename:
            self._summary_file_handler = FileHandler(file_path, 'rb')
            self._latest_filename = filename
            self._latest_offset = 0
            file_changed = True

        new_size = FileHandler.file_stat(file_path).size
        if new_size == self._latest_offset:
            is_end = True
            return file_changed, is_end, event_data

        while True:
            start_offset = self._summary_file_handler.offset
            try:
                event_str = self.event_load(self._summary_file_handler)
                if event_str is None:
                    self._summary_file_handler.reset_offset(start_offset)
                    is_end = True
                    return file_changed, is_end, event_data
                if len(event_str) > MAX_EVENT_STRING:
                    logger.warning("file_path: %s, event string: %d exceeds %d and drop it.",
                                   self._summary_file_handler.file_path, len(event_str), MAX_EVENT_STRING)
                    continue

                field_list, tensor_value_list = self._event_decode(event_str)
                for field, tensor_value in zip(field_list, tensor_value_list):
                    event_data[field] = tensor_value

                logger.debug("Parse summary file offset %d, file path: %s.",
                             self._summary_file_handler.offset, file_path)
                return file_changed, is_end, event_data
            except (exceptions.CRCFailedError, exceptions.CRCLengthFailedError) as ex:
                self._summary_file_handler.reset_offset(start_offset)
                is_end = True
                logger.warning("Check crc failed and reset offset, file_path=%s, offset=%s. Detail: %r.",
                               self._summary_file_handler.file_path, self._summary_file_handler.offset, str(ex))
                return file_changed, is_end, event_data
            except Exception as ex:
                # Note: If an unknown error occurs, we will set the offset to the end of this file,
                # which is equivalent to stopping parsing this file. We do not delete the current job
                # and retain the data that has been successfully parsed.
                self._summary_file_handler.reset_offset(new_size)

                # Notice: If the current job is the latest one in the loader pool and the job is deleted,
                # the job goes into an infinite cycle of load-fail-delete-reload-load-fail-delete.
                # We need to prevent this infinite loop.
                logger.error("Parse summary file failed, will set offset to the file end. file_path: %s, "
                             "offset: %d, detail: %s.", file_path, self._summary_file_handler.offset, str(ex))
                logger.exception(ex)
                raise UnknownError(str(ex))
            finally:
                self._latest_offset = self._summary_file_handler.offset

    @staticmethod
    def _event_decode(event_str):
        """
        Transform `Event` data to tensor_event and update it to EventsData.

        Args:
            event_str (str): Message event string in summary proto, data read from file handler.

        Returns:
            tuple, the elements of the result tuple are:

                - field_list (list): Explain fields to be parsed.
                - tensor_value_list (list): Parsed data with respect to the field list.
        """

        logger.debug("Start to parse event string. Event string len: %s.", len(event_str))
        event = summary_pb2.Event.FromString(event_str)
        logger.debug("Deserialize event string completed.")

        fields = {
            'sample_id': ExplainFieldsEnum.SAMPLE_ID,
            'benchmark': ExplainFieldsEnum.BENCHMARK,
            'metadata': ExplainFieldsEnum.METADATA
        }

        tensor_event_value = getattr(event, 'explain')

        field_list = []
        tensor_value_list = []
        for field in fields:
            if getattr(tensor_event_value, field, None) is None:
                continue

            if ExplainFieldsEnum.METADATA.value == field and not tensor_event_value.metadata.label:
                continue

            tensor_value = None
            if field == ExplainFieldsEnum.SAMPLE_ID.value:
                tensor_value = ExplainParser._add_image_data(tensor_event_value)
            elif field == ExplainFieldsEnum.BENCHMARK.value:
                tensor_value = ExplainParser._add_benchmark(tensor_event_value)
            elif field == ExplainFieldsEnum.METADATA.value:
                tensor_value = ExplainParser._add_metadata(tensor_event_value)
            logger.debug("Event generated, label is %s, step is %s.", field, event.step)
            field_list.append(field)
            tensor_value_list.append(tensor_value)
        return field_list, tensor_value_list

    @staticmethod
    def _add_image_data(tensor_event_value):
        """
        Parse image data based on sample_id in Explain message.

        Args:
            tensor_event_value (Event): The object of Explain message.

        Returns:
            SampleContainer, a named tuple containing sample data.
        """
        inference = InferfenceContainer(
            ground_truth_prob=tensor_event_value.inference.ground_truth_prob,
            ground_truth_prob_sd=tensor_event_value.inference.ground_truth_prob_sd,
            ground_truth_prob_itl95_low=tensor_event_value.inference.ground_truth_prob_itl95_low,
            ground_truth_prob_itl95_hi=tensor_event_value.inference.ground_truth_prob_itl95_hi,
            predicted_label=tensor_event_value.inference.predicted_label,
            predicted_prob=tensor_event_value.inference.predicted_prob,
            predicted_prob_sd=tensor_event_value.inference.predicted_prob_sd,
            predicted_prob_itl95_low=tensor_event_value.inference.predicted_prob_itl95_low,
            predicted_prob_itl95_hi=tensor_event_value.inference.predicted_prob_itl95_hi
        )
        sample_data = SampleContainer(
            sample_id=tensor_event_value.sample_id,
            image_path=tensor_event_value.image_path,
            ground_truth_label=tensor_event_value.ground_truth_label,
            inference=inference,
            explanation=tensor_event_value.explanation,
            hierarchical_occlusion=tensor_event_value.hoc,
            status=tensor_event_value.status
        )
        return sample_data

    @staticmethod
    def _add_benchmark(tensor_event_value):
        """
        Parse benchmark data from Explain message.

        Args:
            tensor_event_value (Event): The object of Explain message.

        Returns:
            BenchmarkContainer, a named tuple containing benchmark data.
        """
        benchmark_data = BenchmarkContainer(
            benchmark=tensor_event_value.benchmark,
            status=tensor_event_value.status
        )

        return benchmark_data

    @staticmethod
    def _add_metadata(tensor_event_value):
        """
        Parse  metadata from Explain message.

        Args:
            tensor_event_value (Event): The object of Explain message.

        Returns:
            MetadataContainer, a named tuple containing benchmark data.
        """
        metadata_value = MetadataContainer(
            metadata=tensor_event_value.metadata,
            status=tensor_event_value.status
        )

        return metadata_value
