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
"""Definition of search entry."""
from queue import PriorityQueue
from typing import Dict, List

from .common import context, DagGraph, gen_hash_key
from ..constant import MINI_FREQUENCEY
from ..third_party_graph.onnx_utils import BaseNode
from .search_path import SearchPath, Pattern, generate_pattern

# Hold module name of current graph.
module_name_mgr = dict()


def _is_satisfied(path):
    """
    Whether current path is satisfied.

    Args:
        path (SearchPath): A SearchPath instance.

    Returns:
        bool, True or False.
    """
    if len(path.recursion_path) == 2:
        return True
    flag = [cur_pattern.count for _, cur_pattern in path.new_pattern.items()]
    return float(sum(flag)) / len(flag) == 1 or path.actual_v >= 0.80


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
    for _, pattern_inst in sorted_pattern.items():
        queue.put(
            SearchPath(pattern=pattern_inst, sequence=init_topo_order,
                       graph=init_graph,
                       sub_graph_size=sub_graph_size),
            block=False
        )

    available_path = []
    while not queue.empty():
        # a. replace pattern in current topo order.
        cur_path = queue.get(block=False)
        cur_topo_order = cur_path.topo_order_aft_repl
        # b. generate new pattern based on replaced topo order.
        if _is_satisfied(cur_path):
            available_path.append(cur_path)
            continue

        if len(available_path) >= 8:
            break

        for _, cur_pattern in cur_path.new_pattern.items():
            if cur_pattern.count < MINI_FREQUENCEY:
                available_path.append(cur_path)
                break
            key = "/".join([cur_pattern.pattern, gen_hash_key(cur_topo_order)])
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
        if len(available_path) <= 1:
            return available_path
        available_path = sorted(available_path, key=lambda x: x.actual_v, reverse=True)
        return available_path[0] if available_path else None

    topo_order = [node for _, (_, node) in enumerate(context.node_collection.items())]
    context.set_sequence_length(len(topo_order))
    pattern = generate_pattern(topo_order, dag=init_dag, sub_graph_size=sub_graph_size)
    found_path = _search(pattern, topo_order, init_graph=init_dag,
                         sub_graph_size=sub_graph_size)
    return _get_top_1(found_path)


def _retrieve_scope_name(found_path):
    """
    Retrieve scope name.

    Args:
        found_path: Found path.
    """
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
                node.op_type, module_dict[node.op_type])]
        else:
            topo_order_with_scope_name.append(f"Model/{node.op_type}")
    return topo_order_with_scope_name


def _scope_name_deduplication(key, scope_names) -> list:
    """
    Scope name deduplication.

    Args:
        scope_names (list): Scope names.

    Returns:
        list, renamed scope name.
    """
    result = []
    if key not in module_name_mgr:
        module_name_mgr[key] = 0
    for item in scope_names:
        item = item.replace(key, f"{key}_{module_name_mgr.get(key)}")
        result.append(item)
    module_name_mgr[key] += 1
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
    global module_name_mgr
    node_in_pattern = module_path.pattern.pattern.split('->')
    node_list = []
    for node in node_in_pattern:
        if module_dict.get(node):
            node_list += module_dict[node]
        else:
            node_list.append(node)
    key = module_path.pattern.module_name
    val = [f"{key}/{node}" for node in node_list]
    return key, val


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


def generate_scope_name(data_loader):
    """
    Generate scope name according to computation graph.

    Args:
        data_loader (OnnxDataLoader): Data loader instance.

    Returns:
        list[str], generated scope name.
    """
    init_dag = _build_connection(data_loader)
    result = _sub_graph_matching(init_dag, beam_width=5, sub_graph_size=6)
    topo_order_with_scope_name_list = _retrieve_scope_name(result)
    return topo_order_with_scope_name_list
