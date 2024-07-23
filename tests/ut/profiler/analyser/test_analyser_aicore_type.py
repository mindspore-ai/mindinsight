# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""Test the analyser module."""
import csv
import os
from unittest import TestCase

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.ut.profiler import PROFILER_DIR

COL_NAMES = ['kernel_type', 'total_time', 'execution_frequency', 'total_percent', 'avg_time']


def get_type_infos(indexes=None, sort_name=None, sort_type=True):
    """
    Get AICORE operator type information.

    Args:
        indexes (list[int]): The operator indexes. Default: None.
        sort_name (str): The sort name. Default: None.
        sort_type (bool): The sort type. If the parameter is `True`, the results
            are sorted in descending order, else `False`. Default: True.
    Returns:
        list[list], the AICORE operator type information.
    """
    aicore_type_path = os.path.join(
        PROFILER_DIR, 'aicore_intermediate_1_type.csv'
    )

    with open(aicore_type_path, 'r') as file:
        csv_reader = csv.reader(file)
        _ = next(csv_reader)
        cache = []
        for type_info in csv_reader:
            total_time = round(float(type_info[1]) * 1e3, 3)
            cache.append(
                [type_info[0], total_time, int(type_info[2]),
                 float(type_info[3]) * 100, round(total_time / int(type_info[2]), 3)]
            )

    if indexes:
        result = [cache[index] for index in indexes]
    else:
        result = cache

    if sort_name:
        sort_index = COL_NAMES.index(sort_name)
        result.sort(key=lambda item: item[sort_index], reverse=sort_type)

    return result


class TestAicoreTypeAnalyser(TestCase):
    """Test the class of `AicoreTypeAnalyser`."""
    def setUp(self) -> None:
        """Initialization before test case execution."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'aicore_type', PROFILER_DIR, '1'
        )

    def test_query_success_1(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(),
            'size': 5
        }
        condition = {}
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        result = self._analyser.query()
        self.assertDictEqual(expect_result, result)

    def test_query_success_2(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[1]),
            'size': 1
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['Cast']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[0, 2, 3, 4]),
            'size': 4
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'not_in': ['Cast']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[0, 1, 3]),
            'size': 3
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'partial_match_str_in': ['C']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_3(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[1, 3]),
            'size': 2
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['Cast', 'Conv2D']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[0, 2, 4]),
            'size': 3
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'not_in': ['Cast', 'Conv2D']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[2, 3]),
            'size': 2
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'partial_match_str_in': ['Trans', 'Conv']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_4(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(sort_name='kernel_type', sort_type=True),
            'size': 5}
        condition = {
            'sort_condition': {
                'name': 'kernel_type',
                'type': 'descending'
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(sort_name='total_time', sort_type=False),
            'size': 5
        }
        condition = {
            'sort_condition': {
                'name': 'total_time',
                'type': 'ascending'
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_5(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[0, 1]),
            'size': 5
        }
        condition = {
            'group_condition': {
                'limit': 2,
                'offset': 0
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(indexes=[3, 4]),
            'size': 5
        }
        condition = {
            'group_condition': {
                'limit': 3,
                'offset': 1
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_6(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_type_infos(
                indexes=[1, 3], sort_name='total_time', sort_type=True
            ),
            'size': 3
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'partial_match_str_in': ['C']
                }
            },
            'sort_condition': {
                'name': 'total_time'
            },
            'group_condition': {
                'limit': 2,
                'offset': 0
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_col_names(self):
        """Test the querying column names function."""
        self.assertListEqual(COL_NAMES, self._analyser.col_names)

    def test_data(self):
        """Test the querying data function."""
        expect_result = get_type_infos()
        self.assertListEqual(expect_result, self._analyser.data)
