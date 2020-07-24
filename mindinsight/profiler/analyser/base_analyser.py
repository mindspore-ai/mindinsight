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
"""The base analyser."""
import functools
from abc import ABC, abstractmethod

from marshmallow import ValidationError

from mindinsight.profiler.common.exceptions.exceptions import \
    ProfilerColumnNotExistException, ProfilerPathErrorException, \
    ProfilerIOException, ProfilerColumnNotSupportSortException
from mindinsight.profiler.common.log import logger
from mindinsight.profiler.common.validator.validate_path import \
    validate_and_normalize_path


class BaseAnalyser(ABC):
    """
    The base analyser.

    A concrete analyser class can be constructed by inheriting the class. The
    analyser provides the ability to filter, sort and group. The subclass only
    need to implement `_load`, `_filter`, `_sort` and `_group`. The condition
    defines the rules for filtering, sorting and grouping.

    Args:
        profiling_dir (str): The directory where the parsed profiling files
            are located.
        device_id (str): The device ID.

    Raises:
        ProfilerPathErrorException: If the profiling dir is invalid.
    """
    _col_names = []

    def __init__(self, profiling_dir, device_id):
        self._profiling_dir = self._normalize_profiling_dir(profiling_dir)
        self._device_id = device_id
        self._data = []
        self._result = None
        self._display_col_names = None
        self._size = 0
        self._none_filter_condition_key = []
        self._none_sort_col_names = []

        try:
            self._load()
        except IOError as err:
            logger.exception(err)
            raise ProfilerIOException()

    @property
    def col_names(self):
        """The column names in the parsed profiling file."""
        return self._col_names

    @property
    def data(self):
        """The data in the parsed profiling file."""
        return self._data

    def query(self, condition=None):
        """
        Query data according to the condition.

        Args:
            condition (dict): The search condition, including filter condition,
                sort condition and group condition. If the condition is `None`,
                all data will be returned. Default: None.

        Returns:
            dict, the result after filtered, sorted and grouped.
        """
        if condition is None:
            condition = {}
        filter_condition = condition.get('filter_condition', {})
        sort_condition = condition.get('sort_condition')
        group_condition = condition.get('group_condition')

        self._result = []
        self._display_col_names = self._col_names[:]
        self._filter(filter_condition)
        self._size = len(self._result)
        if sort_condition:
            self._sort(sort_condition)
        if group_condition:
            self._group(group_condition)
        return self._organize_query_result()

    @abstractmethod
    def _load(self):
        """Load data according to the parsed profiling files."""

    @abstractmethod
    def _filter(self, filter_condition):
        """
        Filter the profiling data according to the filter condition.

        Args:
            filter_condition (dict): The filter condition.
        """

    def _sort(self, sort_condition: dict):
        """
        Sort the profiling data according to the filter condition.

        Args:
            sort_condition (dict): The sort condition.

        Raises:
            ProfilerColumnNotExistException: If the sort name does not exist.
        """
        def _cmp(item1, item2):
            value1 = item1[index]
            value2 = item2[index]

            if value1 is None and value2 is None:
                cmp_result = 0
            elif value1 is None:
                cmp_result = -1
            elif value2 is None:
                cmp_result = 1
            else:
                try:
                    cmp_result = (value1 > value2) - (value1 < value2)
                except TypeError:
                    type1 = type(value1).__name__
                    type2 = type(value2).__name__
                    cmp_result = (type1 > type2) - (type1 < type2)
            return cmp_result

        sort_name = sort_condition.get('name')
        sort_type = sort_condition.get('type', 'descending')
        reverse = sort_type == 'descending'
        if not sort_name:
            return
        try:
            index = self._col_names.index(sort_name)
        except ValueError:
            raise ProfilerColumnNotExistException(sort_name)
        if self._none_sort_col_names and sort_name in self._none_sort_col_names:
            raise ProfilerColumnNotSupportSortException(sort_name)
        self._result.sort(key=functools.cmp_to_key(_cmp), reverse=reverse)

    def _group(self, group_condition: dict):
        """
        Group the profiling data according to the group condition.

        Args:
            group_condition (dict): The group condition.
        """
        limit = group_condition.get('limit')
        offset = group_condition.get('offset')
        if limit is None and offset is None:
            return
        if limit is None:
            limit = 10
        if offset is None:
            offset = 0
        self._result = self._result[limit * offset: limit * (offset + 1)]

    def _default_filter(self, item, condition):
        """
        The default filter method.

        Args:
            item (list[Union[str, float, int]]): A piece of data to be filtered.
            condition (dict): The filter condition.

        Returns:
            bool, `True` if the item is satisfied.
        """
        for condition_key, condition_value in condition.items():
            if condition_key in self._none_filter_condition_key:
                continue
            if condition_key in self._col_names:
                index = self._col_names.index(condition_key)
                actual_value = item[index]
                for exp_key, exp_value in condition_value.items():
                    if not self._is_match_condition(
                            exp_key, exp_value, actual_value):
                        return False
        return True

    def _is_match_condition(self, exp_key, exp_value, actual_value):
        """
        Check whether the actual value meets the expect condition.

        Args:
            exp_key (str): Expect key of the condition.
            exp_value (str): Expect value.
            actual_value (str): Actual value.

        Returns:
            bool, `True` if the actual meets the expect condition, else `False`.
        """
        if exp_key == 'in':
            if actual_value not in exp_value:
                return False
        elif exp_key == 'not_in':
            if actual_value in exp_value:
                return False
        elif exp_key == 'partial_match_str_in':
            for partial_match_str in exp_value:
                if partial_match_str.lower() in actual_value.lower():
                    return True
            return False
        else:
            return False

        return True

    def _normalize_profiling_dir(self, profiling_dir):
        """
        Normalize the profiling dir.

        Args:
            profiling_dir (str): The directory where the parsed profiling files
                are located.

        Returns:
            str, the normalized profiling dir.
        """
        try:
            normalized_profiling_dir = validate_and_normalize_path(
                profiling_dir, 'profiler'
            )
        except ValidationError:
            raise ProfilerPathErrorException('The profiling dir is invalid.')
        return normalized_profiling_dir

    def _organize_query_result(self):
        """
        Organize the query result.

        Returns:
            dict, the query result.
        """
        return {
            'col_name': self._display_col_names,
            'object': self._result,
            'size': self._size
        }
