# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Whether two pattern are fuzzy matched."""
from typing import List

import numpy as np

MIN_PATTERN_LEN = 3
MATCHED_THRESHOLD = .8
COMPLETELY_MATCHED = 1.


def _levenshtein_distance(pattern_a, pattern_b):
    """
    Calculate Levenshtein distance, aka minimum edit distance.

    Suppose we have two pattern ["conv", "bn", "relu", "norm", "add"] and
    ["conv", "bn", "tanh", "add"], levenshtein distance is calculated as follow:
                # conv   bn tanh  add
           #    0    1    2    3    4
        conv    1    0    1    2    3
          bn    2    1    0    1    2
        relu    3    2    1    1    2
        norm    4    3    2    2    2
         add    5    4    3    3    2

    Args:
        pattern_a (list[str]): Pattern to be inspected.
        pattern_b (list[str]): Pattern to be matched.

    Returns:
        int, minimum edit distance.
    """
    row_count = len(pattern_a) + 1
    col_count = len(pattern_b) + 1
    dp = np.zeros(shape=[row_count, col_count], dtype=np.int)
    for i in range(max(col_count, row_count)):
        if i < col_count:
            dp[0][i] = i
        if i < row_count:
            dp[i][0] = i
    for i in range(1, row_count):
        for j in range(1, col_count):
            flag = 0 if pattern_a[i - 1] == pattern_b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j - 1] + flag,
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1
            )

    return dp[row_count - 1][col_count - 1]


def pattern_fuzzy_matching(query: List[str], target: List[str]):
    """
    Whether a pattern can match to a target.

    Args:
        query (list): Query pattern.
        target (list): Target pattern.

    Returns:
        Tuple[bool, float], true or false and matching score.
    """
    edit_count = _levenshtein_distance(query, target)
    target_len = float(len(target))
    score = (target_len - edit_count) / target_len
    if target_len <= MIN_PATTERN_LEN:
        return score == COMPLETELY_MATCHED, score
    return score >= MATCHED_THRESHOLD, score
