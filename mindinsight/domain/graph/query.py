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
"""Query module."""

import re


def construct_filter_func(query_str, case_sensitive=False, use_regex=False):
    """Get filter func."""
    if use_regex:
        if case_sensitive:
            func = lambda x: bool(re.search(query_str, str(x)))
        else:
            func = lambda x: bool(re.search(query_str, str(x), flags=re.I))
    else:
        if case_sensitive:
            func = lambda x: str(x).find(query_str) > -1
        else:
            func = lambda x: str(x).lower().find(query_str.lower()) > -1
    return func


class StackQuery:
    """Stack query."""

    def __init__(self, operators):
        self.operators = operators

    def all(self):
        """
        Retrieve all operators.

        Returns:
            list, all operators.
        """
        return self.operators

    def get(self, index=0):
        """
        Retrieve one operator.

        Args:
            index (int): Operator index, default is 0.

        Returns:
            Operator, single operator.
        """
        if 0 <= index < len(self.operators):
            return self.operators[index]
        return None

    def filter(self, qs, case_sensitive=False, use_regex=False):
        """
        Filter operators with query.

        Args:
            qs (str): Query string.
            case_sensitive (bool): Indicates if case is sensitive. Default is False.
            use_regex (bool): Indicates if qs is regex. Default is False.

        Returns:
            StackQuery, cloned object.
        """
        func = construct_filter_func(qs, case_sensitive, use_regex)
        operators = []
        for operator in self.operators:
            for res in map(func, operator.stack):
                if res:
                    operators.append(operator)
                    break

        return self.clone(operators)

    def clone(self, operators):
        """
        Clone query object.

        Returns:
            StackQuery, cloned object.
        """
        return StackQuery(operators)
