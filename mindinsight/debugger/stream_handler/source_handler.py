# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Source Handler."""
from collections import defaultdict

from mindinsight.datavisual.common.log import logger as log
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamTypeError, DebuggerParamValueError
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase
from mindinsight.domain.graph.query import StackQuery


class SourceHandler(StreamHandlerBase):
    """Source Data object."""

    def __init__(self):
        # contains the stack info with different file path and line number
        self._stack_info_set = set()
        # keep the stack info in order
        self._stack_infos = []

    def put(self, value):
        """
        Put source object into cache.

        Args:
            value (list[DebuggerSource]): The list of source object.
        """
        if not isinstance(value, list):
            value = [value]
        for source in value:
            # avoid showing annotation which has no file_path
            if source.file_path:
                self._stack_info_set.add(source)

    def sort(self):
        """Sort the stack info according to file path and line number."""
        self._stack_infos = list(self._stack_info_set)
        self._stack_infos.sort()

    def get(self, filter_condition):
        """
        Get stack infos according to filter_condition.

        Args:
            filter_condition (str): The pattern of stack info.

        Returns:
            list, the list of DebuggerSource objects.
        """
        if filter_condition:
            query = StackQuery(self._stack_infos)
            stack_infos = query.filter(filter_condition).all()
        else:
            stack_infos = self._stack_infos
        return stack_infos

    def get_stack_info_by_offset(self, pattern=None, limit=0, offset=0):
        """
        Get stack infos.

        Args:
            pattern (str): The pattern of stack infos. Default: None. If not given, return all stack infos.
            limit (int): The size of each page. Default: 0. If 0, there is no limitation.
            offset (int): The index of the page. Valid only when `limit` is not 0.

        Returns:
            dict, stack info objects. The format is like:
                {
                    'total': int,
                    'offset': int,
                    'stack_infos': [{<file_path>: [{'file_path': str, 'line_no': int, 'code_line': str}]]
                }

        """
        # validate params
        self.check_int('limit', limit, min_num=0, max_num=100)
        self.check_int('offset', offset, min_num=0, max_num=len(self._stack_infos))
        validate_stack_pattern(pattern)
        if not limit and offset > 0:
            return {}
        # get filter results
        filter_res = self.get(pattern)
        if not filter_res:
            log.debug("No stack info with pattern %s", pattern)
            return {}
        merged_res = self._merge_stack_by_file_path(filter_res)
        total_size = len(merged_res)
        if not limit:
            limit = total_size
        st_index = offset * limit
        query_res = merged_res[st_index: st_index + limit]
        for stack_info in query_res:
            source_items = stack_info['items']
            stack_info['items'] = list(map(lambda x: x.to_dict(), source_items))

        return {'total': total_size,
                'offset': offset,
                'stack_infos': query_res}

    @staticmethod
    def check_int(param_name, value, min_num, max_num):
        """Check if the value is positive integer."""
        if isinstance(value, int) and min_num <= value <= max_num:
            return
        log.error("Invalid param `%s`. The integer should be in [%d, %d].", param_name, min_num, max_num)
        raise DebuggerParamTypeError(f"Invalid param `{param_name}`.")

    @staticmethod
    def _merge_stack_by_file_path(stack_infos):
        """
        Merge stack infos by file path.

        Args:
            stack_infos (list[DebuggerSource]): List of Debugger Source objects which is sorted already.

        Returns:
            list, list of merged stack infos. The format of stack info is like:
                {'file_path': str, 'items': [DebuggerSource]}
        """
        merged_dict = defaultdict(list)
        for stack_info in stack_infos:
            merged_dict[stack_info.file_path].append(stack_info)
        res = [None] * len(merged_dict)
        for index, (file_path, source_items) in enumerate(merged_dict.items()):
            res[index] = {'file_path': file_path, 'items': source_items}
        return res


def validate_stack_pattern(stack_pattern):
    """Check stack pattern."""
    if stack_pattern:
        if not isinstance(stack_pattern, str):
            log.error("Invalid stack pattern. String type is required, but got %s.", type(stack_pattern))
            raise DebuggerParamTypeError("stack_pattern is not string type.")
        pattern_limit = 255
        if len(stack_pattern) > pattern_limit:
            log.error("The length of stack_pattern is %s, which should no greater than %s.", len(stack_pattern),
                      pattern_limit)
            raise DebuggerParamValueError("stack_pattern is over length limit.")
