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
"""Declare search path related."""
import copy
import uuid
from collections import OrderedDict
from typing import Dict, List, Callable, Union

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.built_in_pattern import BUILT_IN_PATTERN, \
    is_built_in_pattern
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import context, gen_hash_key, DagGraph, \
    MAX_DEGREE, cal_matching_score
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.known_module_name import BUILT_IN_MODULE_NAME
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.pattern import Pattern, scope_name_mapping
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.pattern_fuzzy_matching import \
    pattern_fuzzy_matching
from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils import OnnxNode, BaseNode

module_name_to_src = {}
used_module_name = dict()
global_idx = 0


class OptimizeRules:
    """Define optimize rules."""
    ACTIVATION = {"Relu", "Clip", "Tanh"}
    CAN_NOT_BE_HEAD = ACTIVATION.union({"Add"})
    HAS_MULTI_IPTS = {"Add", "Concat"}


def _is_connected(parent, child, dag):
    """
    Whether two node are connected.

    Args:
        parent (BaseNode): Parent node.
        child (BaseNode): Child node.
        dag (DagGraph): Graph instance.

    Returns:
        bool, True or False.
    """
    return parent.name in dag.precursor_table.get(child.name)


def _is_activation(node_type):
    """
    Whether a node is activation function.

    Args:
        node_type (str): Node type.

    Returns:
        bool, True or False.
    """
    return node_type in OptimizeRules.ACTIVATION


def _is_valid_pattern(pattern, dag):
    """
    Whether a pattern is valid.

    Args:
        pattern (dict): Pattern dict.
        dag (DagGraph): Dag instance.

    Returns:
        bool, True or False.
    """
    if not pattern:
        return False
    head = dag.node_collection[list(pattern.keys())[0]]
    op_type = head.op_type
    if isinstance(head, MergedONNXNode) and "LayerNorm" in head.known_module_name:
        return False
    if len(pattern) == 1:
        return False
    if op_type in OptimizeRules.CAN_NOT_BE_HEAD:
        return False
    return True


def match_known_module_name(pattern):
    """
    Matching with know module name.

    Args:
        pattern (Pattern): To be replaced pattern.

    Returns:
        str, matched module name, return None if not matched.
    """
    matched_result = []
    for ptn, module_name in BUILT_IN_MODULE_NAME.items():
        if pattern.in_degree == ptn.in_degree and pattern.out_degree == ptn.out_degree and \
                ptn.head == pattern.head and ptn.tail == pattern.tail:
            is_matched, score = pattern_fuzzy_matching(pattern.ptn_items, ptn.ptn_items)
            if is_matched:
                matched_result.append((module_name, score))
    if matched_result:
        module_name = (matched_result if len(matched_result) == 1 else
                       sorted(matched_result, key=lambda x: x[1], reverse=True))[0][0]
        if pattern.pattern not in used_module_name:
            used_module_name[pattern.pattern] = 1
        else:
            module_name = f"{module_name}{used_module_name[pattern.pattern]}"
            used_module_name[pattern.pattern] += 1
        return module_name
    return None


def generate_module_name():
    """Generate module name."""
    global global_idx
    name = f"Module{global_idx}"
    global_idx += 1
    return name


def random_name(module_name):
    """Generate node name."""
    return f"{module_name}_{str(uuid.uuid4()).split('-')[0]}"


class MergedONNXNode(BaseNode):
    """Define merged onnx node."""

    def __init__(self, name, module_name, ori_nodes, inputs, outputs, known_module_name):
        super(MergedONNXNode, self).__init__(node_name=name, op_type=module_name)
        self.nodes = ori_nodes
        self.inputs = inputs
        self.outputs = outputs
        self.known_module_name = known_module_name if known_module_name else ""

    def get_name(self):
        return self.name

    def get_op(self):
        return self.op_type


def _find_idx(sequence: List[BaseNode], target: str, equal_func: Callable,
              start_idx: int = 0, end_idx=None) -> int:
    """
    Find matched result according to `equal_func` in [`start_idx`, `end_idx`).

    Args:
        sequence (list): Raw topo sequence.
        target (str): Target node name.
        equal_func (Callable): Function to judge whether matched.
        start_idx (int): Start index.
        end_idx (int): End index.

    Returns:
        int, index.
    """
    not_found = -1
    if not sequence:
        msg = "Empty sequence is not supported."
        raise ValueError(msg)

    end_idx = end_idx if end_idx else len(sequence)
    for i in range(start_idx, end_idx):
        if equal_func(sequence[i], target):
            return i
    return not_found


def _match(x: OnnxNode, y: str):
    """
    Match func.

    Args:
        x (OnnxNode): Node instance.
        y (int): To be compared value.
    """
    return x.name == y


def _get_pattern_degree(sequence: Union[OrderedDict, dict, list],
                        dag: DagGraph):
    """
    Get degree of the pattern.

    Args:
        sequence (Union[OrderedDict, dict, list]): Pattern to calculate.
        dag (DagGraph): Graph instance.

    Returns:
        tuple[int, int, set, set], in degree, out degree, precursors and successors.
    """
    in_node = set()
    node_in_seq = set()
    items = sequence if isinstance(sequence, list) else sequence.keys()
    for item in items:
        node_in_seq.add(item.name if not isinstance(item, str) else item)
    out_node = set()
    for item in items:
        item = item.name if not isinstance(item, str) else item
        for ipt in dag.precursor_table[item]:
            in_node.add(ipt)
        for opt in dag.successor_table[item]:
            if opt not in node_in_seq:
                if item not in context.outputs_table:
                    out = dag.node_collection[item].outputs
                else:
                    out = set(context.outputs_table[item])
                out_node.update(out)
    in_degree = len(in_node - node_in_seq)
    # Because only record nodes that outputs are referred by other nodes,
    # the outputs number of each node must be calculated.
    out_degree = len(out_node)
    return in_degree, out_degree, in_node - node_in_seq, out_node


def _find_pattern_tail(sequence: List[BaseNode], pattern: Dict[str, str], tail_idx: int, dag: DagGraph):
    """
    Supply tail of the pattern sequence.

    Args:
        sequence (list): Raw sequence.
        pattern (dict[str, str]): Pattern to be supplied.
        tail_idx (int): The position where pattern ends.
        dag (DagGraph): Graph object.

    Returns:
        int, tail index in the sequence.
    """
    tail_append_idx = -1
    pattern_len = len(pattern)
    for j, node_name in enumerate(pattern):
        if len(dag.successor_table[node_name]) <= 1:
            continue
        if j == pattern_len - 1:
            # If last node of the pattern has multi-successors,
            # then ignore it.
            continue
        for nd_name in dag.successor_table[node_name]:
            if nd_name not in pattern:
                fd_idx = _find_idx(sequence=sequence, target=nd_name,
                                   equal_func=_match, start_idx=tail_idx)
                tail_append_idx = max(fd_idx, tail_append_idx)
    return tail_append_idx


def _supply_sequence(sequence: List[BaseNode], pattern: Dict[str, str], offset: int, dag: DagGraph):
    """
    Supply sequence from front to end.

    Args:
        sequence (list): Raw sequence.
        pattern (dict[str, str]): Pattern to be supplied.
        offset (int): The position where pattern ends.
        dag (DagGraph): Graph object.

    Returns:
        tuple[dict, tuple[int, int]], found pattern and corresponding position.
    """
    found_sequence = pattern
    tail_idx = offset
    ori_seq_len = len(found_sequence)
    while True:
        tail_idx = _find_pattern_tail(sequence=sequence, pattern=found_sequence,
                                      tail_idx=tail_idx, dag=dag)
        if tail_idx == -1:
            break
        for j in range(offset + 1, tail_idx + 1):
            # If tail_append_idx==-1, this loop will not be executed.
            node_obj = dag.node_collection[sequence[j].name]
            found_sequence[node_obj.name] = node_obj.op_type

    if offset + len(found_sequence) - ori_seq_len + 1 >= len(sequence):
        return found_sequence, (offset - ori_seq_len + 1,
                                offset + len(found_sequence) - ori_seq_len)

    # If the next node after `found_sequence` is an activation and
    # has only one edge from `found_sequence`, then link it
    # to `found_sequence`.
    last_node = sequence[offset + len(found_sequence) - ori_seq_len]
    next_node = sequence[offset + len(found_sequence) - ori_seq_len + 1]
    if _is_activation(next_node.op_type) and _is_connected(last_node, next_node, dag):
        found_sequence[next_node.name] = next_node.op_type

    return found_sequence, (offset - ori_seq_len + 1,
                            offset + len(found_sequence) - ori_seq_len)


def find_built_in_pattern(topo_order: List[BaseNode], dag: DagGraph) -> Dict[str, Pattern]:
    """
    Find built-in pattern.

    Args:
        dag (DagGraph): Graph object.
        topo_order (list): Topo sequence.

    Returns:
        dict[str, Pattern], found pattern.
    """
    pattern = dict()
    cur_idx, total_len = 0, len(topo_order)
    for k in BUILT_IN_PATTERN:
        ptn_len = BUILT_IN_PATTERN[k].ptn_length
        cur_idx = 0
        while cur_idx < total_len:
            matched = True
            init_pattern = OrderedDict()
            if cur_idx + ptn_len > total_len:
                break
            for i in range(ptn_len):
                init_pattern[topo_order[cur_idx + i].name] = topo_order[cur_idx + i].op_type
                if topo_order[cur_idx + i].op_type != BUILT_IN_PATTERN[k].ptn_items[i]:
                    matched = False
                    break
            if not matched:
                cur_idx += 1
                continue
            in_degree, out_degree, _, _ = _get_pattern_degree(init_pattern, dag)
            if in_degree != BUILT_IN_PATTERN[k].in_degree or out_degree != BUILT_IN_PATTERN[k].out_degree:
                cur_idx += 1
                continue
            ptn_key = f"{BUILT_IN_PATTERN[k].pattern}" \
                      f"[{BUILT_IN_PATTERN[k].in_degree}, {BUILT_IN_PATTERN[k].out_degree}]"
            if ptn_key not in pattern:
                pattern[ptn_key] = copy.deepcopy(BUILT_IN_PATTERN[k])

            pattern[ptn_key].insert(cur_idx, ptn_len)
            cur_idx = cur_idx + 1
    return pattern


def generate_pattern(topo_order: List[BaseNode], dag: DagGraph,
                     sub_graph_size: int = 2) -> Dict[str, Pattern]:
    """
    Use self-adaptive sliding window to found sub-graph.

    Args:
        dag (DagGraph): Graph object.
        topo_order (list): Topo sequence.
        sub_graph_size (int): Mini sub-graph size.

    Returns:
        dict[str, Pattern], found pattern.
    """
    pattern = {}
    cur_idx, total_len = 0, len(topo_order)
    while cur_idx < total_len:
        if cur_idx < sub_graph_size - 1:
            cur_idx += 1
            continue
        cur_node = topo_order[cur_idx]
        init_pattern = OrderedDict()
        prev_node = None
        jump_step = 0
        for j in range(sub_graph_size - 1, 0, -1):
            node_obj = dag.node_collection.get(topo_order[cur_idx - j].name)
            # If current node is not child of `prev_node`,
            # then break it. The topo order got from ONNX has a
            # good feature, nodes belonging to one scope would be together.
            # Thus, we can do linear scan on topo order.
            if j != sub_graph_size - 1 and prev_node not in dag.precursor_table.get(topo_order[cur_idx - j].name):
                jump_step = j + 1
                break
            init_pattern[node_obj.name] = node_obj.op_type
            prev_node = topo_order[cur_idx - j].name

        if jump_step == 0:
            init_pattern[cur_node.name] = cur_node.op_type

        if not _is_valid_pattern(init_pattern, dag):
            # in OptimizeRules.CAN_NOT_BE_HEAD:
            # If pattern starts with "ReLU", then pass it.
            cur_idx += 1
            continue

        found_sequence, _ = _supply_sequence(sequence=topo_order,
                                             pattern=init_pattern,
                                             offset=cur_idx - jump_step,
                                             dag=dag)

        in_degree, out_degree, _, _ = _get_pattern_degree(found_sequence, dag)
        if out_degree > MAX_DEGREE or (not context.has_multi_inputs and in_degree > MAX_DEGREE):
            cur_idx += 1
            continue

        ptn = '->'.join(found_sequence.values())
        ptn_key = f"{ptn}[{in_degree}, {out_degree}]"
        if ptn_key not in pattern:
            pattern[ptn_key] = Pattern(ptn, len(found_sequence),
                                       in_degree=in_degree, out_degree=out_degree)
            if is_built_in_pattern(pattern[ptn_key]):
                pattern[ptn_key].additional_score = cal_matching_score(pattern[ptn_key].ptn_length)

        pattern[ptn_key].insert(cur_idx - sub_graph_size + 1, len(found_sequence))
        cur_idx = cur_idx + 1

    pattern = _post_process_overlap(pattern)
    return pattern


def _post_process_overlap(patterns) -> Dict:
    """Post process overlap of found pattern."""
    for name in patterns:
        prev_end = patterns[name].end_index[0]
        idx = 1
        while idx < len(patterns[name].end_index):
            if patterns[name].start_index[idx] <= prev_end:
                patterns[name].start_index.pop(idx)
                patterns[name].end_index.pop(idx)
                continue
            prev_end = patterns[name].end_index[idx]
            idx += 1
    return patterns


class BasePath:
    """Base class of SearchPath (auto-search) and ReplacePath (greedy-match)."""

    def __init__(self, pattern, sequence: List, prev_path=None):
        self.pattern = pattern
        self.recursion_path = prev_path.recursion_path[:] if prev_path is not None else list()
        if prev_path is not None:
            self.recursion_path.append(prev_path)
        self.topo_order_bef_repl = sequence


class SearchPath(BasePath):
    """
    Use SearchPath to store the search path.

    Args:
        pattern (Pattern): Pattern instance to be matched.
        sequence (list): A list of nodes in topological order.
        prev_path (SearchPath): Previous search path instance.
        graph (DagGraph): Graph instance.
        sub_graph_size (int): Mini sub-graph size to search.

    """

    def __init__(self, pattern, sequence: List[BaseNode], prev_path=None,
                 graph=None, sub_graph_size: int = 2):
        super(SearchPath, self).__init__(pattern, sequence, prev_path)
        self.graph = copy.copy(prev_path.graph) if prev_path is not None \
            else copy.copy(graph)
        self.topo_order_aft_repl, self.inverted_index = self._create_new_order()
        self.node_collection = dict()
        self.hash_of_aft_repl = gen_hash_key(self.topo_order_aft_repl)
        if self.hash_of_aft_repl not in context.found_pattern:
            built_in_ptn = find_built_in_pattern(self.topo_order_aft_repl, self.graph)
            auto_search_ptn = generate_pattern(self.topo_order_aft_repl, dag=self.graph,
                                               sub_graph_size=sub_graph_size)
            built_in_ptn.update(auto_search_ptn)
            context.found_pattern[self.hash_of_aft_repl] = context.sort_with_beam(
                built_in_ptn
            )

        self.new_pattern = context.found_pattern[self.hash_of_aft_repl]
        self._created_modules = {
            path.pattern.module_name: path.pattern for path in self.recursion_path
        }
        self._created_modules[self.pattern.module_name] = self.pattern
        self.heuristic_v = self._heuristic_val()
        self.replacement_ratio = self._repl_ratio()
        self.actual_v = self._actual_val()

    def _create_new_order(self):
        """
        Replace sequence with pattern.

        Returns:
            tuple[list, dict], topo sequence and inverted index
            to recover the sequence.
        """
        if self.pattern.pattern not in scope_name_mapping:
            module_name = generate_module_name()
            known_module_name = match_known_module_name(self.pattern)
            scope_name_mapping[self.pattern] = module_name
            module_name_to_src[module_name] = self.pattern.pattern
        else:
            module_name = scope_name_mapping[self.pattern.pattern]
            known_module_name = module_name_to_src[module_name].known_module_name
        self.pattern.module_name = module_name
        self.pattern.known_module_name = known_module_name
        if known_module_name:
            self.pattern.additional_score += cal_matching_score(self.pattern.ptn_length)
        topo_order, inverted_index = self.replace_sub_graph_completely(self.pattern, self.topo_order_bef_repl)
        return topo_order, inverted_index

    def replace_sub_graph_completely(self, pattern: Pattern,
                                     original_topo_order: List[BaseNode]):
        """
        Replace sequence with pattern.

        Match pattern from scratch.

        Notes:
            Bugs here, replace the sub-graph in sequence will have multi-path.
            However, we use greedy-strategy, replace the pattern that appear at front,
            and only keep one path.

        Args:
            pattern (Pattern): Pattern to be used.
            original_topo_order (list): Sequence.

        Returns:
            tuple[list, dict], topo sequence and inverted index
            to recover the sequence.
        """
        inverted_index = {}
        topo_order = []
        path_length = 0
        index = 0
        pattern_len = pattern.ptn_length
        ori_seq_len = len(original_topo_order)
        while index < ori_seq_len:
            if original_topo_order[index].op_type != pattern.ptn_items[0] or \
                    ori_seq_len - index < pattern_len:
                topo_order.append(original_topo_order[index])
                index += 1
                path_length += 1
                continue

            visited_node, j = [], 0
            matched = True
            for j in range(pattern_len):
                visited_node.append(original_topo_order[index + j])
                if original_topo_order[index + j].op_type != pattern.ptn_items[j]:
                    matched = False
                    break

            if not matched:
                topo_order.append(original_topo_order[index])
                index += 1
                path_length += 1
                continue

            in_degree, out_degree, inputs, outputs = _get_pattern_degree(visited_node, self.graph)
            if in_degree != pattern.in_degree or out_degree != pattern.out_degree:
                topo_order.extend(visited_node)
                index += j + 1
                path_length += j + 1
                continue

            inverted_index[path_length] = [j + index for j in range(pattern_len)]
            new_node = MergedONNXNode(name=random_name(pattern.module_name),
                                      module_name=pattern.module_name,
                                      ori_nodes=visited_node[:],
                                      inputs=inputs,
                                      outputs=outputs,
                                      known_module_name=pattern.known_module_name)
            self._reconnect(new_node)
            self.graph.node_collection[new_node.name] = new_node
            topo_order.append(new_node)
            path_length += 1
            index += pattern_len

        return topo_order, inverted_index

    def _reconnect(self, merged_node):
        """
        Re-connect merged_node with its precursor and successor nodes.

        Args:
            merged_node (MergedONNXNode): Merged node.
        """
        in_node, out_node = [], []
        node_in_seq = [item.name for item in merged_node.nodes]
        for _, item in enumerate(merged_node.nodes):
            item = item.name if not isinstance(item, str) else item
            for ipt in self.graph.precursor_table[item]:
                if ipt not in node_in_seq:
                    in_node.append(ipt)
            for opt in self.graph.successor_table[item]:
                if opt not in node_in_seq:
                    out_node.append(opt)
        self.graph.precursor_table[merged_node.name] = in_node
        self._relink_precursor(merged_node, in_node, node_in_seq)
        self._relink_successor(merged_node, out_node, node_in_seq)

    def _relink_precursor(self, merged_node, in_node, node_in_seq):
        """
        Relink node to precursor.

        Args:
            merged_node (MergedONNXNode): Merged node instance.
            in_node (list): In nodes list.
            node_in_seq (list): Node name in sequence.
        """
        # Add current node to precursor table.
        self.graph.precursor_table[merged_node.name] = in_node
        # Link the precursor to current node.
        for p_nd in in_node:
            scsr_nodes = self.graph.successor_table[p_nd].copy()
            for i, nd_name in enumerate(scsr_nodes):
                if nd_name in node_in_seq:
                    scsr_nodes[i] = merged_node.name
            self.graph.successor_table[p_nd] = scsr_nodes

    def _relink_successor(self, merged_node, out_node, node_in_seq):
        """
        Relink node to successor.

        Args:
            merged_node (MergedONNXNode): Merged node.
            out_node (list): Out nodes.
            node_in_seq (list): Node name in sequence.
        """
        # Add current node to successor table.
        self.graph.successor_table[merged_node.name] = out_node
        # Link successor to current node.
        for s_nd in out_node:
            p_nodes = self.graph.precursor_table[s_nd].copy()
            for i, nd_name in enumerate(p_nodes):
                if nd_name in node_in_seq:
                    p_nodes[i] = merged_node.name
            self.graph.precursor_table[s_nd] = p_nodes

    def evaluate_score(self):
        """Evaluate path score."""
        return .7 * self.actual_v + .3 * self.heuristic_v

    def _cal_merged_module_length(self, ptn):
        """Calculate module length."""
        ptn_len = 0
        for item in ptn.ptn_items:
            if item in self._created_modules:
                ptn_len += self._cal_merged_module_length(self._created_modules[item])
                continue
            ptn_len += 1
        return ptn_len

    def _heuristic_val(self):
        """Calculate heuristic score of the path."""
        res = []
        for ptn in self.new_pattern.items():
            res.append(ptn[1].count * self._cal_merged_module_length(ptn[1]) / context.get_sequence_length())
        if not res:
            return 1.0
        return max(res)

    def _cal_bonus(self):
        """Calculate total pattern length."""
        score = self.pattern.additional_score
        for search_path in self.recursion_path:
            score += search_path.pattern.additional_score
        return score

    def _repl_ratio(self):
        """Calculate replacement ratio of current path."""
        return (context.get_sequence_length() - len(self.topo_order_aft_repl)) / context.get_sequence_length()

    def _actual_val(self):
        """Calculate ground-truth score of the path."""
        bonus = self._cal_bonus()
        return (bonus + self.replacement_ratio) / 2

    def __lt__(self, other):
        """Override `<` operator."""
        return self.evaluate_score() > other.evaluate_score()

    def __eq__(self, other):
        """Override `==` operator."""
        return self.evaluate_score() == other.evaluate_score()

    def __str__(self):
        """Override `str()` method."""
        return self.__repr__()

    def __repr__(self):
        """Override `repr()` method."""

        def _dfs(module_name):
            chain = []
            src = module_name_to_src[module_name]
            for sub_module in src.split("->"):
                if sub_module in module_name_to_src:
                    chain.append(_dfs(sub_module))
                else:
                    chain.append(sub_module)
            return "->".join(chain)

        repr_str = f"{self.pattern.pattern}[{self.pattern.module_name}], " \
                   f"H: {self.heuristic_v}, G: {self.actual_v}, E: {self.evaluate_score()}"

        return repr_str


class ReplacePath(BasePath):
    """Data struct of replacing path with greedy matching."""

    def __init__(self, pattern, sequence: List, prev_path=None):
        super(ReplacePath, self).__init__(pattern, sequence, prev_path)
        self.topo_order_aft_repl = None

    def replace(self, increment_idx):
        """
        Greedy matching.

        Args:
            increment_idx (int): To deduplicate module name.
        """
        src = ",".join(self.topo_order_bef_repl)
        tgt = self.pattern.pattern
        md_name = f"Module{increment_idx}"
        src_aft_repl = src.replace(tgt, md_name)
        if src != src_aft_repl:
            self.pattern.module_name = md_name
            self.topo_order_aft_repl = src_aft_repl.split(",")
            return md_name
        return None
