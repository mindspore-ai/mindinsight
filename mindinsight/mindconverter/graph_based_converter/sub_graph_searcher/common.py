# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Declare generic variable and functions."""

__all__ = ["context",
           "gen_hash_key",
           "DagGraph",
           "MAX_DEGREE",
           "cal_matching_score",
           "ACCEPTABLE_RESULT_COUNT",
           "MINI_FREQUENCY",
           "SATISFIED_SCORE",
           "MAX_ITERATION_DEPTH_OF_MULTI_IPT",
           "MAX_ITERATION_DEPTH_OF_SINGLE_IPT"]

import math
import copy
import functools
from collections import OrderedDict
from typing import List

from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils import BaseNode

MAX_DEGREE = 1
MINI_FREQUENCY = 0.07
MAX_ITERATION_DEPTH_OF_MULTI_IPT = 16
MAX_ITERATION_DEPTH_OF_SINGLE_IPT = 8
SATISFIED_SCORE = 0.74
ACCEPTABLE_RESULT_COUNT = 32
PTN_COVERAGE_THRESHOLD = 0.65
# If pattern length is short than `IGNORE_PTN_LEN`, then do not calculate the coverage.
IGNORE_PTN_LEN = 5


def cal_matching_score(sequence_len: int):
    """
    Calculate matching score.

    Args:
        sequence_len (int): Pattern length.
    """
    return 2 / (1 + math.pow(math.e, -0.1 * sequence_len)) - 1


def _cmp(x, y):
    """Cmp function to sort pattern."""
    if x[1].count > y[1].count:
        return CmpRelation.GREATER
    if x[1].count < y[1].count:
        return CmpRelation.LESS
    if x[1].additional_score > y[1].additional_score:
        return CmpRelation.GREATER
    if x[1].additional_score < y[1].additional_score:
        return CmpRelation.LESS
    if x[1].ptn_length > y[1].ptn_length:
        return CmpRelation.GREATER
    if x[1].ptn_length < y[1].ptn_length:
        return CmpRelation.LESS
    return CmpRelation.EQUAL


class CmpRelation:
    """Define cmp relation between `x` and `y`."""
    # When x is equal to y in logic.
    EQUAL = 0
    # When x is less than y in logic.
    LESS = -1
    # When x is greater than y in logic.
    GREATER = 1


def gen_hash_key(sequence: List[BaseNode], separator="-", without_module: bool = False):
    """Generate hash key."""
    seq = []
    for item in sequence:
        if without_module and "module" in item.op_type.lower():
            seq.append("_M_")
            continue
        seq.append(item.op_type)
    return separator.join(seq)


class DagGraph:
    """Define dag graph."""

    def __init__(self, nodes, precursor: dict, successor: dict):
        self.node_collection = nodes
        self.precursor_table = precursor
        self.successor_table = successor

    def __copy__(self):
        """
        Override `copy` function.

        Notes:
            Be careful about `copy` method. It's safe to use deepcopy,
            but struck in its poor performance.

        Returns:
            DagGraph, new instance.
        """
        cls = self.__class__
        new_obj = cls(copy.copy(self.node_collection),
                      copy.deepcopy(self.precursor_table),
                      copy.deepcopy(self.successor_table))
        return new_obj


class AlgorithmContext:
    """Define context of sub-graph search algorithm."""
    found_pattern = {}
    visited = set()
    beam_width = 5
    MIN_FREQUENCY = 1
    total_len = 0
    node_collection = None
    precursor_table = {}
    successor_table = {}
    outputs_table = {}
    has_multi_inputs = False

    def set_init_node_collection(self, nd_col):
        """Init node_collection."""
        self.node_collection = nd_col

    def set_sequence_length(self, n):
        """Init sequence length."""
        self.total_len = float(n)

    def get_sequence_length(self):
        """Get sequence length."""
        return self.total_len

    def set_beam_width(self, bw):
        """Set beam width."""
        self.beam_width = bw

    def sort_with_beam(self, pattern_arr):
        """
        Sort patterns according to its frequency and prune by beam width.

        When frequency equals, choose longer pattern.

        Args:
            pattern_arr (dict): Pattern dict.

        Returns:
            OrderedDict, sorted pattern.
        """
        pattern_arr = sorted(pattern_arr.items(), key=functools.cmp_to_key(_cmp),
                             reverse=True)
        if len(pattern_arr) > AlgorithmContext.beam_width:
            new_pattern_arr = pattern_arr[:self.beam_width]
            # Avoid dropping built-in pattern, because built-in patterns are much
            # more potential.
            for i in range(self.beam_width):
                if pattern_arr[i][1].additional_score != 0:
                    new_pattern_arr.append(pattern_arr[i])
        res = OrderedDict()
        for i, (key, ptn) in enumerate(pattern_arr):
            if ptn.count <= AlgorithmContext.MIN_FREQUENCY:
                continue
            if ptn.additional_score > 0 and ptn.ptn_length > IGNORE_PTN_LEN:
                res[key] = ptn
                continue
            skip = False
            for j, (_, candidate) in enumerate(pattern_arr):
                if i == j:
                    continue
                # If `ptn` is a sub-pattern of `candidate`, and `ptn` count equals to `candidate`,
                # then reject the `ptn`.
                if candidate.ptn_length >= ptn.ptn_length and ptn.count == candidate.count \
                        and ptn.pattern in candidate.pattern:
                    skip = True
                    break
                # If `candidate` is sub-pattern of `ptn`, `candidate` has additional score,
                # and `ptn` has no additional score, then calculate its replacement ratio.
                if candidate.ptn_length < ptn.ptn_length and candidate.additional_score != 0 \
                        and ptn.additional_score == 0 and candidate.pattern in ptn.pattern:
                    ratio = candidate.ptn_length / ptn.ptn_length
                    if ratio >= PTN_COVERAGE_THRESHOLD:
                        skip = True
                        break

            if not skip:
                res[key] = ptn

        return res


context = AlgorithmContext()
