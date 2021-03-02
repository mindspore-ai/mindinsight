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
"""Definition of search entry."""
from queue import PriorityQueue, Queue
from typing import Dict, List

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.built_in_pattern import USER_DEFINED_PATTERN
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.pattern_fuzzy_matching import \
    pattern_fuzzy_matching
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import context, DagGraph, gen_hash_key, \
    ACCEPTABLE_RESULT_COUNT, MAX_ITERATION_DEPTH_OF_SINGLE_IPT
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import MINI_FREQUENCY, \
    MAX_ITERATION_DEPTH_OF_MULTI_IPT, SATISFIED_SCORE
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils import BaseNode
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.search_path import SearchPath, Pattern, \
    generate_pattern, find_built_in_pattern, ReplacePath
from mindinsight.mindconverter.common.exceptions import SubGraphSearchingError


def _is_satisfied(path):
    """
    Whether current path is satisfied.

    Args:
        path (SearchPath): A SearchPath instance.

    Returns:
        bool, True or False.
    """
    recursion_depth = MAX_ITERATION_DEPTH_OF_MULTI_IPT if context.has_multi_inputs \
        else MAX_ITERATION_DEPTH_OF_SINGLE_IPT
    if len(path.recursion_path) > recursion_depth:
        return True
    candidate_eval = any([is_pattern_satisfied(p, path) for p in path.new_pattern.values()])
    if not path.new_pattern or not candidate_eval:
        return True
    if path.evaluate_score() > SATISFIED_SCORE and not candidate_eval:
        return True
    return False


def is_pattern_satisfied(pattern, seq):
    """Whether a pattern is valid."""
    rpl_ratio = 1.0 * pattern.count * pattern.ptn_length / len(seq.topo_order_aft_repl)
    # If replacement ratio is larger than 7%,
    # then take it, otherwise, reject this pattern.
    if rpl_ratio >= MINI_FREQUENCY:
        return True
    return False


def _search(init_pattern: Dict[str, Pattern], init_topo_order: List[BaseNode],
            init_graph, sub_graph_size: int = 2) -> List[SearchPath]:
    """
    Search base on merged graph, until all frequency is 1.

    Args:
        init_pattern (dict): Init pattern to be replaced.
        init_topo_order (list): Init topo sequence.
        init_graph (DagGraph): Graph instance.
        sub_graph_size (int): Min sub-graph size.

    Returns:
        list, available path.
    """
    # 1. Sort the pattern by frequency.
    sorted_pattern = context.sort_with_beam(init_pattern)
    # 2. Put pattern into queue.
    queue = PriorityQueue()
    for pattern_inst in sorted_pattern.values():
        queue.put(
            SearchPath(pattern=pattern_inst, sequence=init_topo_order,
                       graph=init_graph,
                       sub_graph_size=sub_graph_size),
            block=False
        )

    available_path = []
    deduplicate_path = set()
    while not queue.empty():
        # a. replace pattern in current topo order.
        cur_path = queue.get(block=False)
        cur_topo_order = cur_path.topo_order_aft_repl
        # b. generate new pattern based on replaced topo order.
        if _is_satisfied(cur_path):
            available_path.append(cur_path)
            deduplicate_path.add(cur_path.hash_of_aft_repl)
            _is_satisfied(cur_path)
            continue

        if len(available_path) >= ACCEPTABLE_RESULT_COUNT:
            break

        for cur_pattern in cur_path.new_pattern.values():
            if not is_pattern_satisfied(cur_pattern, cur_path):
                if cur_path.hash_of_aft_repl in deduplicate_path:
                    continue
                available_path.append(cur_path)
                deduplicate_path.add(cur_path.hash_of_aft_repl)
                continue
            key = "/".join([f"{cur_pattern.pattern}[{cur_pattern.in_degree},{cur_pattern.out_degree}]",
                            gen_hash_key(cur_topo_order, without_module=True)])
            if key in context.visited:
                continue
            # c. create new SearchPath.
            new_path = SearchPath(pattern=cur_pattern, sequence=cur_topo_order, prev_path=cur_path,
                                  sub_graph_size=sub_graph_size)
            context.visited.add(key)
            # d. put it into heap to sort.
            queue.put(new_path, block=False)

    return available_path


def _sub_graph_matching(init_dag, beam_width=5, sub_graph_size=4):
    """
    Sub-graph matching.

    Args:
        init_dag (DagGraph): Graph instance.
        beam_width (int): Beam width used to prune search path.
        sub_graph_size (int): Mini sub-graph size to find.

    Returns:
        SearchPath, found path.
    """
    context.set_beam_width(beam_width)

    def _get_top_1(available_path: list):
        if not available_path:
            return None
        available_path = sorted(available_path, key=lambda x: x.actual_v, reverse=True)
        return available_path[0]

    topo_order = [node for _, (_, node) in enumerate(context.node_collection.items())]
    context.set_sequence_length(len(topo_order))
    built_in_pattern = find_built_in_pattern(topo_order, init_dag)
    pattern = generate_pattern(topo_order, dag=init_dag, sub_graph_size=sub_graph_size)
    pattern.update(built_in_pattern)
    found_path = _search(pattern, topo_order, init_graph=init_dag, sub_graph_size=2)
    return _get_top_1(found_path)


def _retrieve_scope_name(found_path):
    """
    Retrieve scope name.

    Args:
        found_path: Found path.
    """
    _add_known_module_name(found_path)
    module_name_mgr = dict()

    module_dict = dict()
    for module_path in found_path.recursion_path:
        key, val = _retrieve_operators(module_path, module_dict)
        module_dict[key] = val
    if found_path.pattern:
        key, val = _retrieve_operators(found_path, module_dict)
        module_dict[key] = val

    topo_order_with_scope_name = []
    for node in found_path.topo_order_aft_repl:
        if module_dict.get(node.op_type):
            topo_order_with_scope_name += [f"Model/{item}" for item in _scope_name_deduplication(
                node.op_type, module_dict[node.op_type], module_name_mgr)]
        else:
            topo_order_with_scope_name.append(f"Model/{node.op_type}")
    return topo_order_with_scope_name


def _scope_name_deduplication(key, scope_names, memo) -> list:
    """
    Scope name deduplication.

    Args:
        key (str): Module name.
        scope_names (list): Scope names.
        memo (dict): Memo to record module name.

    Returns:
        list, renamed scope name.
    """
    memo[key] = memo.setdefault(key, -1) + 1
    result = [item.replace(key, f"{key}_{memo.get(key)}") for item in scope_names]
    return result


def _is_attn_layer(split_module):
    """
    Whether the submodule is attention layer.

    Attention layer is defined as: attn-add-norm-fc-gelu-fc-add-norm.

    Args:
        split_module (list[list[str]]): Operations list in module.

    Returns:
        list, found module name.
    """

    def _matched(modules):
        """If the similarity score of sub_module and attention pattern is greater than 0.95, take it."""
        threshold = 0.95
        leaf_node = [m[-1] for m in modules]
        attn_layer_ptn_with_gelu = [
            "MatMul", "Add", "MatMul", "Add", "Reshape", "MatMul", "Add", "Reshape", "Transpose", "Reshape",
            "Transpose", "Transpose", "MatMul", "Div", "Add", "Softmax", "MatMul", "Transpose", "Reshape", "MatMul",
            "Add", "Add", "ReduceMean", "Sub", "Cast", "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add",
            "MatMul", "Add", "Div", "Erf", "Add", "Mul", "Mul", "MatMul", "Add", "Add", "ReduceMean", "Sub", "Cast",
            "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add"
        ]
        attn_layer_ptn_with_new_gelu = [
            "MatMul", "Add", "MatMul", "Add", "MatMul", "Add", "Reshape", "Transpose", "Reshape", "Reshape",
            "Transpose", "Transpose", "MatMul", "Div", "Add", "Softmax", "MatMul", "Transpose", "Einsum", "Add", "Add",
            "ReduceMean", "Sub", "Cast", "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add", "MatMul", "Add",
            "Mul", "Pow", "Mul", "Add", "Mul", "Tanh", "Add", "Mul", "MatMul", "Add", "Add", "ReduceMean", "Sub",
            "Cast", "Pow", "ReduceMean", "Add", "Sqrt", "Div", "Mul", "Add"
        ]
        matched = max(pattern_fuzzy_matching(leaf_node, attn_layer_ptn_with_gelu)[1],
                      pattern_fuzzy_matching(leaf_node, attn_layer_ptn_with_new_gelu)[1]) > threshold
        return matched

    candidates = Queue()
    candidates.put(split_module, block=False)
    while not candidates.empty():
        candidate = candidates.get(block=False)
        if _matched(candidate):
            return candidate[0][0].split("_")[0]
        cur_scope = candidate[0][1]
        split_sub_module = []
        for item in candidate:
            # It's not necessary to scan the module which depth is 2.
            if len(item) == 2:
                continue
            if item[1] != cur_scope:
                cur_scope = item[1]
                if split_sub_module:
                    candidates.put(split_sub_module[:], block=False)
                    split_sub_module.clear()
            split_sub_module.append(item[1:])
        if split_sub_module:
            candidates.put(split_sub_module[:], block=False)
    return None


def _lift_each_module(sub_module):
    """Lift each module in sub-module."""
    lifted_module = []
    split_module = []
    cur_scope = sub_module[0].split("/")[0]
    segmented_pos = 0

    def _lift(modules):
        nonlocal lifted_module, split_module
        exceed_max_depth = max(*[len(m.split("/")) for m in modules]) > 2
        if not exceed_max_depth:
            for _ in range(len(split_module)):
                lifted_module.append((False, 0))
            return
        # attn_module_name has been normalized without "_idx", only has raw module name.
        attn_module_name = _is_attn_layer(split_module)
        for s_md in split_module:
            if attn_module_name:
                md_name = [md for md in s_md if attn_module_name in md]
                if md_name:
                    md_name = md_name[0]
                    attn_idx = s_md.index(md_name)
                    if attn_idx > 0:
                        lifted_module.append((True, attn_idx))
                        continue
                    lifted_module.append((False, 0))
                    continue
            lifted_module.append((True, 0))

    for i, m in enumerate(sub_module):
        split_md = m.split("/")
        # Find one module.
        if cur_scope != split_md[0]:
            _lift(sub_module[segmented_pos:i])
            # Clean up.
            cur_scope = split_md[0]
            segmented_pos = i
            split_module.clear()
        split_module.append(split_md)

    # Do lift on last module.
    _lift(sub_module[segmented_pos:])
    return lifted_module


def _retrieve_operators(module_path, module_dict):
    """
    Retrieve operators from path.

    Args:
        module_path(SearchPath): module path.
        module_dict(dict): module dictionary.

    Returns:
        str: module_name, operators in module.
    """

    def _lift(sub_module):
        """Lift nodes upper."""
        nonlocal added_module
        lifted_submodule = []
        record = dict()
        # DO NOT lift on attn-add-norm-fc with GeLU-fc-add-norm.
        # It's a fix pattern in Transformer model.
        lift_on_each_module = _lift_each_module(sub_module)
        for i, m in enumerate(sub_module):
            lift_needed, lift_from = lift_on_each_module[i]
            scopes = m.split("/")
            if lift_needed and len(scopes) >= 3:
                # If the scope depth is 3, like ModuleX/ModuleY/Gemm,
                # then we lift ModuleY to top level.
                md_name, md_idx = scopes[-2 if lift_from == 0 else lift_from].split("_")
                if record.get(md_name, -1) != md_idx:
                    record[md_name] = md_idx
                    added_module[md_name] = added_module.setdefault(md_name, -1) + 1
                if lift_from != 0:
                    lifted_md = "/".join([f"{md_name}_{added_module.setdefault(md_name, 0)}"] + scopes[lift_from + 1:])
                else:
                    lifted_md = f"{md_name}_{added_module.setdefault(md_name, 0)}/{scopes[-1]}"
                lifted_submodule.append(lifted_md)
                continue
            if lift_needed and len(scopes) == 2:
                # If the module is required to lifted, then lift leaf node to parent.
                lifted_submodule.append(scopes[-1])
                continue
            # If lift is not required, then add it directly.
            lifted_submodule.append(m)
        return lifted_submodule

    added_module = dict()
    node_in_pattern = module_path.pattern.ptn_items
    node_list = []
    for node in node_in_pattern:
        if module_dict.get(node):
            sub_scope = _scope_name_deduplication(node, module_dict[node], added_module)
            node_list += _lift(sub_scope)
        else:
            node_list.append(node)
    val = [f"{module_path.pattern.module_name}/{node}" for node in node_list]
    return module_path.pattern.module_name, val


def _build_connection(loader):
    """
    Build dag graph.

    Args:
        loader (OnnxDataLoader): Dataloader.
    """
    context.set_init_node_collection(loader.nodes_dict)
    # Output name is not same with node name
    for node_name, node in loader.nodes_dict.items():
        context.precursor_table[node_name] = list(node.get_precursor_dict().keys())
        context.successor_table[node_name] = list(node.get_successor_dict().keys())
        context.outputs_table[node_name] = node.output_name_list

    # Record the model inputs count, use it to control the search algorithm.
    context.has_multi_inputs = len(loader.input_nodes) > 1
    dag = DagGraph(nodes=context.node_collection.copy(),
                   precursor=context.precursor_table.copy(),
                   successor=context.successor_table.copy())
    return dag


def flatten_graph(graph):
    """
    Flatten graph into a sequence.

    Args:
        graph (DagGraph): DagGraph instance.

    Returns:
        list[str], corresponding scope name.
    """
    return [f"Model/{node.op_type}" for node in graph.node_collection.values()]


def validate_topo_order_succession():
    """Validate whether topological order is successive."""
    module_interval = dict()
    for idx, node_name in enumerate(context.node_collection.keys()):
        name_arr = node_name.split("/")
        if len(name_arr) <= 2:
            continue
        node_name = "/".join(name_arr[:-2])
        if node_name not in module_interval:
            module_interval[node_name] = [idx]
            continue
        if module_interval[node_name][-1] != idx - 1:
            return False
        module_interval[node_name].append(idx)
    return True


def _add_known_module_name(search_path):
    """
    Add known module name to GlobalContext.

    Args:
        search_path (SearchPath): Search path.

    """
    ctx = GlobalContext()
    if search_path.pattern.known_module_name:
        ctx.known_module_name[search_path.pattern.module_name] = search_path.pattern.known_module_name
    for it in search_path.recursion_path:
        if it.pattern.known_module_name:
            ctx.known_module_name[it.pattern.module_name] = it.pattern.known_module_name
    return ctx


def greedy_match(topo_order, user_defined_ptn):
    """
    Greedy replace topological order with given pattern by user.

    Args:
        topo_order (list[str]): Topological order sequence.
        user_defined_ptn (dict): User defined pattern.
    """
    increment_idx = 0
    prev_path = None
    for md_name, ptn in user_defined_ptn:
        ptn = Pattern(",".join(ptn), len(ptn), -1, -1, ptn)
        ptn.known_module_name = md_name
        topo_order_aft_rpl = topo_order[:] if prev_path is None else prev_path.topo_order_aft_repl
        repl_path = ReplacePath(ptn, topo_order_aft_rpl, prev_path=prev_path)
        module_name = repl_path.replace(increment_idx)
        if module_name is not None:
            increment_idx += 1
            prev_path = repl_path
    return prev_path


@SubGraphSearchingError.check_except("Sub-Graph pattern searching fail.")
def generate_scope_name(data_loader):
    """
    Generate scope name according to computation graph.

    Args:
        data_loader (OnnxDataLoader): Data loader instance.

    Returns:
        list[str], generated scope name.
    """
    init_dag = _build_connection(data_loader)
    try:
        if USER_DEFINED_PATTERN:
            topo_order = [node for _, node in context.node_collection.items()]
            repl_path = greedy_match(topo_order, USER_DEFINED_PATTERN)
            topo_order_with_scope_name_list = _retrieve_scope_name(repl_path) if repl_path else flatten_graph(init_dag)
            return topo_order_with_scope_name_list

        result = _sub_graph_matching(init_dag, beam_width=5, sub_graph_size=6)
        topo_order_with_scope_name_list = _retrieve_scope_name(result) if result else flatten_graph(init_dag)

        if len(topo_order_with_scope_name_list) != len(data_loader.nodes_dict):
            topo_order_with_scope_name_list = flatten_graph(init_dag)

    except (ValueError, IndexError, AttributeError, KeyError) as _:
        topo_order_with_scope_name_list = flatten_graph(init_dag)

    return topo_order_with_scope_name_list
