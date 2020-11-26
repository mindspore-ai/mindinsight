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
"""Declare generic variable and functions."""
import copy
import functools
from collections import OrderedDict
from typing import List

from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils import BaseNode

MAX_OUT_DEGREE = 1
MINI_FREQUENCY = 4
MAX_ITERATION_DEPTH = 4
SATISFIED_SCORE = 0.55
ACCEPTABLE_RESULT_COUNT = 16


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
    total_len = 0
    MIN_FREQUENCY = 1
    node_collection = None
    precursor_table = {}
    successor_table = {}

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

        def _cmp(x, y):
            """Cmp function to sort pattern."""
            if x[1].count > y[1].count:
                return CmpRelation.GREATER
            if x[1].count < y[1].count:
                return CmpRelation.LESS
            if x[1].ptn_length > y[1].ptn_length:
                return CmpRelation.GREATER
            if x[1].ptn_length < y[1].ptn_length:
                return CmpRelation.LESS
            return CmpRelation.EQUAL

        pattern_arr = sorted(pattern_arr.items(), key=functools.cmp_to_key(_cmp),
                             reverse=True)
        if len(pattern_arr) > self.beam_width:
            pattern_arr = pattern_arr[:self.beam_width]
        res = OrderedDict()
        for i, (key, ptn) in enumerate(pattern_arr):
            if ptn.count <= self.MIN_FREQUENCY:
                continue
            skip = False
            for j, (_, candidate) in enumerate(pattern_arr):
                if i == j:
                    continue
                if candidate.ptn_length >= ptn.ptn_length and ptn.ptn_items == candidate.ptn_items[:ptn.ptn_length]:
                    skip = True
                    break
            if skip:
                continue
            res[key] = ptn
        return res


context = AlgorithmContext()

__all__ = ["context",
           "gen_hash_key",
           "DagGraph",
           "MAX_OUT_DEGREE",
           "MAX_ITERATION_DEPTH",
           "SATISFIED_SCORE",
           "MINI_FREQUENCY",
           "ACCEPTABLE_RESULT_COUNT"]
