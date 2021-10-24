# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Rebuild code scope according to user's selection."""
from typing import Mapping, Dict

from mindconverter.common.exceptions import ModuleNameDefineError
from mindconverter.graph_based_converter.common.global_context import GlobalContext

MODULE_NAME_INDEXING = 0
MODULE_NAME_MGR = dict()


def get_area_heads_and_tails(nodes, dataloader):
    """
    Get heads and tails from user selection area.

    Args:
        nodes (dict): Node instances.
        dataloader (DataLoader): Dataloader instance which holds the graph info.

    Returns:
        tuple, corresponding head, input tensor, tail and output tensor of the area.
    """
    feed_in_tensors = set()
    output_tensors = set()
    o_tsr2nodes = dict()
    i_tsr2nodes = dict()

    def _record_input_and_output_tensor(nd_obj):
        """Record inputs and outputs tensor."""
        nonlocal feed_in_tensors, output_tensors, o_tsr2nodes, i_tsr2nodes
        # Record output tensor.
        for opt in getattr(nd_obj, "output_name_list", None) or getattr(nd_obj, "outputs", None):
            o_tsr2nodes[opt] = nd_obj
            output_tensors.add(opt)
        # Record input tensor.
        for ipt in getattr(nd_obj, "input_name_list", list()) or getattr(nd_obj, "inputs", list()):
            if ipt in dataloader.tensors_dict:
                continue
            i_tsr2nodes[ipt] = nd_obj
            feed_in_tensors.add(ipt)

    for _, nd_inst in nodes.items():
        _record_input_and_output_tensor(nd_inst)

    # Calculate difference set for heads and tails.
    tsr_from_outside = feed_in_tensors - output_tensors
    tsr_to_outside = output_tensors - feed_in_tensors
    head = [i_tsr2nodes[tsr] for tsr in tsr_from_outside]
    tail = [o_tsr2nodes[tsr] for tsr in tsr_to_outside]
    return head, tsr_from_outside, tail, tsr_to_outside


def get_area_rank(heads, tails, dataloader):
    """
    Get area rank according to its head nodes.

    Args:
        heads (list[str]): Head nodes of the area.
        tails (list[str]): Tail nodes of the area.
        dataloader (OnnxDataLoader): Dataloader instance which holds the graph info.

    Returns:
        int, rank number.
    """
    iter_heads = []
    iter_tails = []

    def _get_ends(node, end="heads"):
        if isinstance(node, UserSelection):
            child_ends = []
            for child_node in getattr(node, end):
                child_ends += _get_ends(child_node, end)
            return child_ends

        return [node.name]

    for nd in heads:
        iter_heads += _get_ends(nd, "heads")
    for nd in tails:
        iter_tails += _get_ends(nd, "tails")

    start_rank = 1e8
    end_rank = -1e8
    topo_order = list(dataloader.nodes_dict.keys())
    for nd in iter_heads:
        idx = topo_order.index(nd)
        start_rank = min(idx, start_rank)
    for nd in iter_tails:
        idx = topo_order.index(nd)
        end_rank = max(idx, end_rank)
    return start_rank, end_rank


class UserSelection:
    """User selection area in the ui."""

    def __init__(self, sid, module_name, nodes, dataloader, merged_modules):
        global MODULE_NAME_MGR, MODULE_NAME_INDEXING
        self.sid = sid
        if module_name in MODULE_NAME_MGR:
            self.fake_module_name = MODULE_NAME_MGR[module_name]
        else:
            self.fake_module_name = f"Module{MODULE_NAME_INDEXING}"
            MODULE_NAME_INDEXING += 1
            MODULE_NAME_MGR[module_name] = self.fake_module_name
        self.module_name = module_name
        if module_name not in GlobalContext().known_module_name:
            GlobalContext().known_module_name[self.fake_module_name] = module_name
        self.nodes = {nd: dataloader.nodes_dict.get(nd) or merged_modules.get(nd) for nd in nodes if
                      nd not in dataloader.constant_nodes}
        self.heads, self.inputs, self.tails, self.outputs = get_area_heads_and_tails(self.nodes, dataloader)
        self.start_rank, self.end_rank = get_area_rank(self.heads, self.tails, dataloader)

    def __lt__(self, other):
        if self.start_rank == other.start_rank:
            return self.end_rank < other.end_rank
        return self.start_rank < other.start_rank

    def __gt__(self, other):
        if self.start_rank == other.start_rank:
            return self.end_rank > other.end_rank
        return self.start_rank > other.start_rank


def _build_scope(selections, dataloader):
    """
    Build nodes scope name from top to bottom.

    Args:
        selections (list[UserSelection]): Selection instance.
        dataloader (DataLoader): Dataloader instance.

    Returns:
        dict, node name and corresponding scope name.
    """
    name_scopes = dict()
    module_cnt = dict()

    def _update_indexing(full_prefix, cur_md_name):
        """Update hierarchical indexing."""
        nonlocal module_cnt
        previous_md = full_prefix.split("/")[-1]

        full_md_name = "-".join((full_prefix.replace("/", "-"), cur_md_name))
        for module_name, cnt in module_cnt.items():
            if cnt.get(full_md_name) and module_name != previous_md:
                module_cnt[module_name][full_md_name] -= 1

        if previous_md not in module_cnt:
            module_cnt[previous_md] = dict()
            module_cnt[previous_md][full_md_name] = 0
            return module_cnt[previous_md][full_md_name]
        if full_md_name not in module_cnt[previous_md]:
            module_cnt[previous_md][full_md_name] = 0
            return module_cnt[previous_md][full_md_name]
        module_cnt[previous_md][full_md_name] = module_cnt[previous_md][full_md_name] + 1
        return module_cnt[previous_md][full_md_name]

    def _hierarchically_update_scope(u_selection, added_prefix=None):
        """Build scope from top to bottom."""
        nonlocal name_scopes
        md_index_in_parent_md = _update_indexing(added_prefix, u_selection.fake_module_name)

        prefix = f"{u_selection.fake_module_name}_{md_index_in_parent_md}"
        if added_prefix:
            prefix = f"{added_prefix}/{prefix}"
        for nd_name, nd_obj in u_selection.nodes.items():
            if isinstance(nd_obj, UserSelection):
                _hierarchically_update_scope(nd_obj, prefix)
                continue
            name_scopes[nd_name] = f"{prefix}/{nd_obj.op_type}"

    for selection in selections:
        _hierarchically_update_scope(selection, "Model")

    # Add rest nodes of the graph.
    scopes = {}
    for name, inst in dataloader.nodes_dict.items():
        if name in name_scopes:
            scopes[name] = name_scopes[name]
            continue
        scopes[name] = f"Model/{inst.op_type}"
    return scopes


def _reset_global_indexing():
    """Reset global indexing each time."""
    global MODULE_NAME_INDEXING, MODULE_NAME_MGR
    MODULE_NAME_MGR.clear()
    MODULE_NAME_INDEXING = 0


def _valid_user_define_module_name(user_operations):
    """Valid user operations."""
    for _, selection in user_operations.items():
        if "_" in selection["module_name"]:
            raise ModuleNameDefineError("User-defined module name is not allowed to contain '_'.")


def rebuild_name_scope_according_to_user_selections(dataloader, user_operations: Mapping[str, Dict]) -> Dict:
    """
    Rebuild name scope for the IR nodes according to user's selections on UI.

    Args:
        dataloader (DataLoader): Dataloader instance.
        user_operations (dict): User operations recorded in UI.

    Returns:
        dict[str, str], each node's scope name.
    """
    _reset_global_indexing()

    selections = []
    module_collection = dict()

    for sid, selection in user_operations.items():
        slt = UserSelection(sid=sid, module_name=selection["module_name"], nodes=selection["nodes"],
                            dataloader=dataloader, merged_modules=module_collection)
        module_collection[sid] = slt
        selections.append(slt)

    sorted_selections = sorted(selections, key=lambda x: int(x.sid))

    name_scopes = _build_scope(sorted_selections, dataloader)
    return name_scopes
