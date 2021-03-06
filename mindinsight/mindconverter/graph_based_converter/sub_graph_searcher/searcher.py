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
from queue import PriorityQueue
from typing import Dict, List

from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import context, DagGraph, gen_hash_key, \
    ACCEPTABLE_RESULT_COUNT
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.common import MINI_FREQUENCY, \
    MAX_ITERATION_DEPTH, SATISFIED_SCORE
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_utils import BaseNode
from mindinsight.mindconverter.graph_based_converter.sub_graph_searcher.search_path import SearchPath, Pattern, \
    generate_pattern, find_built_in_pattern
from mindinsight.mindconverter.common.exceptions import SubGraphSearchingError


def _is_satisfied(path):
    """
    Whether current path is satisfied.

    Args:
        path (SearchPath): A SearchPath instance.

    Returns:
        bool, True or False.
    """
    if len(path.recursion_path) > MAX_ITERATION_DEPTH:
        return True
    if not path.new_pattern or not any([is_pattern_satisfied(p, path) for p in path.new_pattern.values()]):
        return True
    if path.evaluate_score() > SATISFIED_SCORE:
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


def _retrieve_operators(module_path, module_dict):
    """
    Retrieve operators from path.

    Args:
        module_path(SearchPath): module path.
        module_dict(dict): module dictionary.

    Returns:
        str: module_name, operators in module.
    """

    def _whether_to_lift(sub_module):
        """Whether to lift a scope according to its depth."""
        return max(*[len(m.split("/")) for m in sub_module]) > 2

    def _lift(sub_module):
        """Lift nodes upper."""
        nonlocal added_module
        lifted_submodule = []
        record = dict()
        lift_needed = _whether_to_lift(sub_module)
        for m in sub_module:
            scopes = m.split("/")
            if lift_needed and len(scopes) == 3:
                # If the scope depth is 3, like ModuleX/ModuleY/Gemm,
                # then we lift ModuleY to top level.
                md_name, md_idx = scopes[-2].split("_")
                if record.get(md_name, -1) != md_idx:
                    record[md_name] = md_idx
                    added_module[md_name] = added_module.setdefault(md_name, -1) + 1
                lifted_submodule.append(f"{md_name}_{added_module.setdefault(md_name, 0)}/{scopes[-1]}")
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
        result = _sub_graph_matching(init_dag, beam_width=5, sub_graph_size=6)
        topo_order_with_scope_name_list = _retrieve_scope_name(result) if result else flatten_graph(init_dag)

        if len(topo_order_with_scope_name_list) != len(data_loader.nodes_dict):
            topo_order_with_scope_name_list = flatten_graph(init_dag)

        if result:
            _add_known_module_name(result)

    except (ValueError, IndexError, AttributeError, KeyError) as _:
        topo_order_with_scope_name_list = flatten_graph(init_dag)

    return topo_order_with_scope_name_list
