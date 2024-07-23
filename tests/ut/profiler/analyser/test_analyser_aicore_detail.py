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
import json
import os
from unittest import TestCase

from mindinsight.profiler.analyser.analyser_factory import AnalyserFactory
from tests.ut.profiler import PROFILER_DIR

COL_NAMES = ['op_name', 'kernel_name', 'kernel_type', 'avg_execution_time', 'execution_frequency',
             'MFLOPs(10^6 cube)', 'GFLOPS(10^9 cube)', 'MFLOPs(10^6 vector)', 'GFLOPS(10^9 vector)', 'op_info']


def get_detail_infos(indexes=None, sort_name=None, sort_type=True):
    """
    Get AICORE operator detail information.

    Args:
        indexes (list[int]): The operator indexes. Default: None.
        sort_name (str): The sort name. Default: None.
        sort_type (bool): The sort type. If the parameter is `True`, the results
            are sorted in descending order, else `False`. Default: True.
    Returns:
        list[list], the AICORE operator detail information.
    """
    framework_path = os.path.join(PROFILER_DIR, 'framework_raw_1.csv')
    detail_path = os.path.join(PROFILER_DIR, 'aicore_intermediate_1_detail.csv')
    flops_path = os.path.join(PROFILER_DIR, 'flops_1.txt')

    with open(framework_path, 'r') as fm_file, open(detail_path, 'r') as detail_file,\
         open(flops_path, 'r') as flops_file:
        fm_csv_reader = csv.reader(fm_file)
        detail_csv_reader = csv.reader(detail_file)
        flops_reader = flops_file.readlines()[1:]
        _ = next(fm_csv_reader)
        _ = next(detail_csv_reader)
        cache = []
        for fm_info, detail_info, flops_line in zip(fm_csv_reader, detail_csv_reader, flops_reader):
            flops = flops_line.strip().split(',')
            cache.append(
                [fm_info[4], fm_info[5], fm_info[6], round(float(detail_info[1]) * 1e3, 3), int(detail_info[2]),
                 float(flops[1]), float(flops[2]), float(flops[3]), float(flops[4]),
                 json.loads(fm_info[8]) if fm_info[8] else None]
            )

    if indexes:
        result = [cache[index] for index in indexes]
    else:
        result = cache

    if sort_name:
        sort_index = COL_NAMES.index(sort_name)
        result.sort(key=lambda item: item[sort_index], reverse=sort_type)

    return result


class TestAicoreDetailAnalyser(TestCase):
    """Test the class of `AicoreDetailAnalyser`."""
    def setUp(self) -> None:
        """Initialization before test case execution."""
        self._analyser = AnalyserFactory.instance().get_analyser(
            'aicore_detail', PROFILER_DIR, '1'
        )

    def test_query_success_1(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(),
            'size': 10
        }
        result = self._analyser.query({})
        self.assertDictEqual(expect_result, result)

        result = self._analyser.query()
        self.assertDictEqual(expect_result, result)

    def test_query_success_2(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(indexes=[9]),
            'size': 1
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['MatMul']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        condition = {
            'filter_condition': {
                'kernel_type': {
                    'not_in': ['AtomicAddrClean', 'Cast', 'TransData', 'Conv2D']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        condition = {
            'filter_condition': {
                'kernel_name': {
                    'partial_match_str_in': ['op9']
                }
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_3(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(sort_name='avg_execution_time', sort_type=True),
            'size': 10
        }
        condition = {
            'sort_condition': {
                'name': 'avg_execution_time',
                'type': 'descending'
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(sort_name='kernel_name', sort_type=False),
            'size': 10
        }
        condition = {
            'sort_condition': {
                'name': 'kernel_name',
                'type': 'ascending'
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_4(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(indexes=[2, 3]),
            'size': 10
        }
        condition = {
            'group_condition': {
                'limit': 2,
                'offset': 1
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': [],
            'size': 10
        }
        condition = {
            'group_condition': {
                'limit': 2,
                'offset': 5
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_5(self):
        """Test the success of the querying function."""
        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(
                indexes=[1, 2], sort_name='avg_execution_time', sort_type=True
            ),
            'size': 4
        }
        condition = {
            'filter_condition': {
                'kernel_name': {
                    'partial_match_str_in': ['Atomic', 'Conv']
                }
            },
            'sort_condition': {
                'name': 'avg_execution_time'
            },
            'group_condition': {
                'limit': 2,
                'offset': 1
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES,
            'object': get_detail_infos(
                indexes=[0, 1, 2, 8], sort_name='avg_execution_time', sort_type=True
            ),
            'size': 4
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['Conv2D', 'AtomicAddrClean', 'TransData']
                },
                'kernel_name': {
                    'partial_match_str_in': ['Atomic', 'Conv']
                }
            },
            'sort_condition': {
                'name': 'avg_execution_time'
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

    def test_query_success_6(self):
        """Test the success of the querying function."""
        detail_infos = get_detail_infos(indexes=[9])

        expect_result = {
            'col_name': COL_NAMES[0:9],
            'object': [item[0:9] for item in detail_infos],
            'size': 1
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['MatMul']
                },
                'is_display_detail': False
            }
        }
        result = self._analyser.query(condition)
        self.assertDictEqual(expect_result, result)

        expect_result = {
            'col_name': COL_NAMES[1:9],
            'object': [item[1:9] for item in detail_infos],
            'size': 1
        }
        condition = {
            'filter_condition': {
                'kernel_type': {
                    'in': ['MatMul']
                },
                'is_display_detail': False,
                'is_display_full_op_name': False
            }
        }
        result = self._analyser.query(condition)
        print(expect_result, result)
        self.assertDictEqual(expect_result, result)

    def test_query_and_sort_by_op_type_1(self):
        """Test the success of the querying and sorting function by operator type."""
        detail_infos = get_detail_infos(indexes=[9, 0, 2, 1, 5, 3, 4])
        expect_result = {
            'col_name': COL_NAMES[1:9],
            'object': [item[1:9] for item in detail_infos]
        }

        filter_condition = {
            'kernel_type': {
                'in': ['AtomicAddrClean', 'Cast', 'MatMul'],
                'not_in': ['TransData']
            },
            'is_display_detail': False,
            'is_display_full_op_name': False
        }
        op_type_order = ['MatMul', 'AtomicAddrClean', 'Cast']
        result = self._analyser.query_and_sort_by_op_type(
            filter_condition, op_type_order
        )
        self.assertDictEqual(expect_result, result)

    def test_col_names(self):
        """Test the querying column names function."""
        self.assertListEqual(COL_NAMES, self._analyser.col_names)

    def test_data(self):
        """Test the querying data function."""
        expect_result = get_detail_infos()
        self.assertListEqual(expect_result, self._analyser.data)
