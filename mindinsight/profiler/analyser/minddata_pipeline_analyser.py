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
"""The minddata pipeline analyser class."""
import csv
import json
import os
import sys

from mindinsight.profiler.analyser.base_analyser import BaseAnalyser
from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerPipelineOpNotExistException
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import validate_and_normalize_path


class MinddataPipelineAnalyser(BaseAnalyser):
    """
    The analyser for analyzing the minddata pipeline operator and queue data.

    Args:
        profiling_dir (str): The directory where the parsed profiling files are
            located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = ['op_id', 'op_type', 'num_workers', 'output_queue_size',
                  'output_queue_average_size', 'output_queue_length',
                  'output_queue_usage_rate', 'sample_interval', 'parent_id',
                  'children_id']
    _file_name_pipeline = 'minddata_pipeline_raw_{}.csv'
    _index_op_id = 0
    _index_op_type = 1
    _index_num_workers = 2
    _index_output_queue_size = 3
    _index_output_queue_average_size = 4
    _index_output_queue_length = 5
    _index_output_queue_usage_rate = 6
    _index_sample_interval = 7
    _index_parent_id = 8
    _index_children_id = 9

    def __init__(self, profiling_dir, device_id):
        super().__init__(profiling_dir, device_id)
        self._none_filter_condition_key = ['threshold', 'is_display_op_detail']
        self._none_sort_col_names = ['output_queue_size', 'children_id']
        self._op_id_index_map = self._get_op_id_index_map()

    def get_op_and_parent_op_info(self, op_id):
        """
        Get the operator and parent operator information by `op_id`.

        Args:
            op_id (int): The minddata pipeline operator ID.

        Returns:
            dict, the operator and parent operator information.

        Raises:
             ProfilerPipelineOpNotExistException: If the minddata pipeline
                operator does not exist.
        """
        index = self._op_id_index_map.get(op_id)
        if index is None:
            raise ProfilerPipelineOpNotExistException(str(op_id))
        op_info = self._data[index]
        parent_id = op_info[self._index_parent_id]
        parent_index = self._op_id_index_map.get(parent_id)
        if parent_index is None:
            parent_op = None
            queue_info = None
        else:
            parent_op_info = self._data[parent_index]
            parent_op = {
                'op_id': parent_op_info[self._index_op_id],
                'op_type': parent_op_info[self._index_op_type],
                'num_workers': parent_op_info[self._index_num_workers]
            }
            queue_info = {
                'output_queue_size': op_info[self._index_output_queue_size],
                'output_queue_average_size':
                    op_info[self._index_output_queue_average_size],
                'output_queue_length': op_info[self._index_output_queue_length],
                'output_queue_usage_rate':
                    op_info[self._index_output_queue_usage_rate],
                'sample_interval': op_info[self._index_sample_interval]
            }

        current_op = {
            'op_id': op_info[self._index_op_id],
            'op_type': op_info[self._index_op_type],
            'num_workers': op_info[self._index_num_workers]
        }
        return {
            'current_op': current_op,
            'parent_op': parent_op,
            'queue_info': queue_info
        }

    def _load(self):
        """Load data according to the parsed minddata pipeline file."""
        pipeline_file_path = os.path.join(
            self._profiling_dir,
            self._file_name_pipeline.format(self._device_id)
        )
        pipeline_file_path = validate_and_normalize_path(
            pipeline_file_path, raise_key="Invalid pipeline file path.")
        if not os.path.isfile(pipeline_file_path):
            logger.warning('The file <%s> does not exist.', pipeline_file_path)
            return

        with open(pipeline_file_path, 'r') as file:
            csv.field_size_limit(sys.maxsize)
            csv_reader = csv.reader(file)
            _ = next(csv_reader)
            for info in csv_reader:
                self._data.append(self._convert_field_type(info))

    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """
        def _inner_filter(item: list):
            return self._default_filter(item, filter_condition)

        def _inner_map(item: list):
            inner_item = item[0:2]
            inner_item.extend(item[4:])
            return inner_item

        threshold = filter_condition.get('threshold')
        is_display_op_detail = filter_condition.get(
            'is_display_op_detail', False
        )
        self._set_display_col_name(is_display_op_detail)

        filter_result = list(filter(_inner_filter, self._data))
        if threshold:
            low_threshold = threshold[1]
            high_threshold = threshold[0]
            filter_result = self._filter_outside_threshold(
                filter_result, low_threshold, high_threshold
            )

        if is_display_op_detail:
            self._result = filter_result
        else:
            self._result = list(map(_inner_map, filter_result))

    def _filter_outside_threshold(self, data, low_threshold, high_threshold):
        """
        Get the data outside the threshold range.

        Args:
            data (list[list]): The filtered data.
            low_threshold (float): The low threshold.
            high_threshold (float): The high threshold.

        Returns:
            list[list], the data outside the threshold range.
        """
        root_node = None
        leaf_nodes = []
        all_below_low_threshold = True
        all_higher_high_threshold = True
        result = []
        for item in data:
            parent_id = item[self._index_parent_id]
            if parent_id is None:
                root_node = item
                continue

            # current usage rate compared to the threshold
            cur_usage_rate = item[self._index_output_queue_usage_rate]
            is_low = False
            if cur_usage_rate < low_threshold:
                is_low = True
            else:
                all_below_low_threshold = False
            if cur_usage_rate < high_threshold:
                all_higher_high_threshold = False

            # the child node usage rate compared to the threshold
            child_ids = item[self._index_children_id]
            if not child_ids:
                leaf_nodes.append(item)
                continue
            child_usage_rates = [
                self._get_usage_rate_by_op_id(op_id) for op_id in child_ids
            ]
            is_high = True
            for usage_rate in child_usage_rates:
                if usage_rate < high_threshold:
                    is_high = False
                    break

            if is_high and is_low:
                result.append(item)

        if all_below_low_threshold:
            result = leaf_nodes
        elif all_higher_high_threshold:
            result = [root_node]
        return result

    def _get_usage_rate_by_op_id(self, op_id):
        """
        Gets the usage rate of the queue corresponding to the specified operator.

        Args:
            op_id (int): The pipeline operator ID.

        Returns:
            float, the usage rate of the queue corresponding to the specified
            operator.
        """
        index = self._op_id_index_map.get(op_id)
        op_info = self._data[index]
        return op_info[self._index_output_queue_usage_rate]

    def _set_display_col_name(self, is_display_op_detail):
        """
        Set the display column name according to the filter condition.

        Args:
            is_display_op_detail (bool): Whether to display the detailed operator
                information.
        """
        if not is_display_op_detail:
            self._display_col_names = self._col_names[0:2]
            self._display_col_names.extend(self._col_names[4:])

    def _convert_field_type(self, row):
        """
        Convert the field type of minddata pipeline file to the specific type.

        Args:
            row (list[str]): One row data from parsed data.

        Returns:
            list[Union[str, int, float]], the converted data.
        """
        return [
            int(row[self._index_op_id]),
            row[self._index_op_type],
            int(row[self._index_num_workers]),
            json.loads(row[self._index_output_queue_size])
            if row[self._index_output_queue_size] else None,
            float(row[self._index_output_queue_average_size])
            if row[self._index_output_queue_average_size] else None,
            int(row[self._index_output_queue_length])
            if row[self._index_output_queue_length] else None,
            float(row[self._index_output_queue_usage_rate])
            if row[self._index_output_queue_usage_rate] else None,
            int(row[self._index_sample_interval]),
            int(row[self._index_parent_id])
            if row[self._index_parent_id] else None,
            json.loads(row[self._index_children_id])
            if row[self._index_children_id] else None
        ]

    def _get_op_id_index_map(self):
        """
        Get the map of the operator id and index in data.

        Returns:
            dict, the map of the operator id and index in data.
        """
        the_map = {}
        for index, op_info in enumerate(self._data):
            the_map[op_info[self._index_op_id]] = index
        return the_map
