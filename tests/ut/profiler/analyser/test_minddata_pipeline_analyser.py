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
"""Test the minddata pipeline analyser module."""
import csv
import json
import os

import pytest

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerPipelineOpNotExistException
from tests.ut.profiler import PROFILER_DIR

COL_NAMES = ['op_id', 'op_type', 'num_workers', 'output_queue_size',
             'output_queue_average_size', 'output_queue_length',
             'output_queue_usage_rate', 'sample_interval', 'parent_id',
             'children_id']


def get_pipeline_infos(pipeline_path, indexes=None, sort_name=None,
                       sort_type=True):
    """
    Get minddata pipeline operator and queue information.

    Args:
        pipeline_path (str): The parsed minddata pipeline file path.
        indexes (list[int]): The operator indexes. Default: None.
        sort_name (str): The sort name. Default: None.
        sort_type (bool): The sort type. If the parameter is `True`, the results
            are sorted in descending order, else `False`. Default: True.
    Returns:
        list[list], the minddata pipeline operator and queue information.
    """
    with open(pipeline_path, 'r') as file:
        csv_reader = csv.reader(file)
        _ = next(csv_reader)
        cache = []
        for row in csv_reader:
            cache.append(
                [
                    int(row[0]),
                    row[1],
                    int(row[2]),
                    json.loads(row[3]) if row[3] else None,
                    float(row[4]) if row[4] else None,
                    int(row[5]) if row[5] else None,
                    float(row[6]) if row[6] else None,
                    int(row[7]),
                    int(row[8]) if row[8] else None,
                    json.loads(row[9]) if row[9] else None
                ]
            )

    if indexes:
        result = [cache[index] for index in indexes]
    else:
        result = cache

    if sort_name:
        sort_index = COL_NAMES.index(sort_name)
        result.sort(key=lambda item: item[sort_index], reverse=sort_type)

    return result


def get_simple_row_info(row):
    """
    Get simple minddata pipeline row information.

    Args:
        row (list[str, int, float]): The minddata pipeline row information.

    Returns:
        list[str, int, float], the simple minddata pipeline row information.
    """
    simple_info = row[0:2]
    simple_info.extend(row[4:])
    return simple_info


class TestMinddataPipelineAnalyser:
    """Test the class of `MinddataPipelineAnalyser`."""
    def setup_method(self):
        """Initialization before test case execution."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', PROFILER_DIR, '0'
        )
        self._pipeline_path = os.path.join(
            PROFILER_DIR, 'minddata_pipeline_raw_0.csv'
        )

    def test_query_success_1(self):
        """Test the success of the querying function."""
        detail_infos = get_pipeline_infos(self._pipeline_path)
        col_name = get_simple_row_info(COL_NAMES)
        expect_result = {
            'col_name': col_name,
            'object': [get_simple_row_info(item) for item in detail_infos],
            'size': 4
        }
        result = self._analyser.query({})
        assert expect_result == result

        result = self._analyser.query()
        assert expect_result, result

    def test_query_success_2(self):
        """Test the success of the querying function."""
        detail_infos = get_pipeline_infos(self._pipeline_path, indexes=[0])
        col_name = get_simple_row_info(COL_NAMES)
        expect_result = {
            'col_name': col_name,
            'object': [get_simple_row_info(item) for item in detail_infos],
            'size': 1
        }
        condition = {
            'filter_condition': {
                'op_id': {
                    'in': [0]
                }
            }
        }
        result = self._analyser.query(condition)
        assert expect_result == result

        detail_infos = get_pipeline_infos(self._pipeline_path, indexes=[0, 1])
        expect_result = {
            'col_name': col_name,
            'object': [get_simple_row_info(item) for item in detail_infos],
            'size': 2
        }
        condition = {
            'filter_condition': {
                'op_type': {
                    'not_in': ['TFReader']
                }
            }
        }
        result = self._analyser.query(condition)
        assert expect_result == result

        detail_infos = get_pipeline_infos(self._pipeline_path, indexes=[2, 3])
        expect_result = {
            'col_name': col_name,
            'object': [get_simple_row_info(item) for item in detail_infos],
            'size': 2
        }
        condition = {
            'filter_condition': {
                'op_type': {
                    'partial_match_str_in': ['TF']
                }
            }
        }
        result = self._analyser.query(condition)
        assert expect_result, result

    def test_query_success_3(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_pipeline_infos(self._pipeline_path),
            'size': 4
        }
        condition = {
            'filter_condition': {
                'is_display_op_detail': True
            }
        }
        result = self._analyser.query(condition)
        assert expect_result == result

    def test_query_success_4(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': [],
            'size': 0
        }
        condition = {
            'filter_condition': {
                'threshold': [0.8, 0.2],
                'is_display_op_detail': True
            }
        }
        result = self._analyser.query(condition)
        assert expect_result == result

    def test_query_success_5(self):
        """
        Test the success of the querying function.

        The upstream queue utilization of the operator is greater than
        the highest threshold, and the downstream queue utilization of
        the operator is lower than the lowest threshold.
        """
        profiling_dir = os.path.join(os.path.dirname(__file__), 'resource')
        pipeline_path = os.path.join(
            profiling_dir, 'minddata_pipeline_raw_0.csv'
        )
        analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', profiling_dir, '0'
        )

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_pipeline_infos(pipeline_path, [1]),
            'size': 1
        }
        condition = {
            'filter_condition': {
                'threshold': [0.8, 0.2],
                'is_display_op_detail': True
            }
        }
        result = analyser.query(condition)
        assert expect_result == result

    def test_query_success_6(self):
        """
        Test the success of the querying function.

        The upstream queue utilization of the operator is greater than
        the highest threshold, and the downstream queue utilization of
        the operator is lower than the lowest threshold.
        """
        profiling_dir = os.path.join(os.path.dirname(__file__), 'resource')
        pipeline_path = os.path.join(
            profiling_dir, 'minddata_pipeline_raw_1.csv'
        )
        analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', profiling_dir, '1'
        )

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_pipeline_infos(pipeline_path, [2]),
            'size': 1
        }
        condition = {
            'filter_condition': {
                'threshold': [0.8, 0.6],
                'is_display_op_detail': True
            }
        }
        result = analyser.query(condition)
        assert expect_result == result

    def test_query_success_7(self):
        """
        Test the success of the querying function.

        All queues utilization are greater than the highest threshold.
        """
        profiling_dir = os.path.join(os.path.dirname(__file__), 'resource')
        pipeline_path = os.path.join(
            profiling_dir, 'minddata_pipeline_raw_2.csv'
        )
        analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', profiling_dir, '2'
        )

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_pipeline_infos(pipeline_path, [0]),
            'size': 1
        }
        condition = {
            'filter_condition': {
                'threshold': [0.8, 0.6],
                'is_display_op_detail': True
            }
        }
        result = analyser.query(condition)
        assert expect_result == result

    def test_query_success_8(self):
        """
        Test the success of the querying function.

        All queues utilization are lower than the lowest threshold.
        """
        profiling_dir = os.path.join(os.path.dirname(__file__), 'resource')
        pipeline_path = os.path.join(
            profiling_dir, 'minddata_pipeline_raw_3.csv'
        )
        analyser = AnalyserFactory.instance().get_analyser(
            'minddata_pipeline', profiling_dir, '3'
        )

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_pipeline_infos(pipeline_path, [3, 4]),
            'size': 2
        }
        condition = {
            'filter_condition': {
                'threshold': [0.8, 0.2],
                'is_display_op_detail': True
            }
        }
        result = analyser.query(condition)
        assert expect_result == result

    def test_get_op_and_parent_op_info_success(self):
        """Test the success of the function of querying operator and parent operator."""
        expect_result = {
            'current_op': {
                'op_id': 0,
                'op_type': 'Batch',
                'num_workers': 4
            },
            'parent_op': None,
            'queue_info': None
        }
        result = self._analyser.get_op_and_parent_op_info(0)
        assert expect_result == result

        expect_result = {
            'current_op': {
                'op_id': 1,
                'op_type': 'Shuffle',
                'num_workers': 1
            },
            'queue_info': {
                'output_queue_size': [10, 20, 30],
                'output_queue_average_size': 20.0,
                'output_queue_length': 64,
                'output_queue_usage_rate': 0.3125,
                'sample_interval': 10
            },
            'parent_op': {
                'op_id': 0,
                'op_type': 'Batch',
                'num_workers': 4
            }
        }
        result = self._analyser.get_op_and_parent_op_info(1)
        assert expect_result == result

    def test_get_op_and_parent_op_info_fail(self):
        """Test the function of fail to query operator and parent operator."""
        with pytest.raises(ProfilerPipelineOpNotExistException) as exc_info:
            self._analyser.get_op_and_parent_op_info(5)
        assert exc_info.value.error_code == '50546188'
        assert exc_info.value.message == 'The minddata pipeline operator 5 ' \
                                         'does not exist.'
