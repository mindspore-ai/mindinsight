# Copyright 2020 Huawei Technologies Co., Ltd
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
"""
Predefined watchpoints.

This module predefine recommend watchpoints.
"""
import queue as Queue

from mindinsight.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.conditionmgr.condition import TargetTypeEnum
from mindinsight.conditionmgr.condition import ConditionIdEnum
from mindinsight.conditionmgr.common.utils import NodeBasicInfo
from mindinsight.conditionmgr.log import logger
from mindinsight.conf import settings


UNSELECTED_STATUS = 0
HALF_SELECTED_STATUS = 1
SELECTED_STATUS = 2


class _WatchPointData:
    """WatchPoint data container"""
    def __init__(self, watch_condition, watch_nodes):
        self.watch_condition = watch_condition
        self.watch_nodes = watch_nodes

    def get_watch_condition_dict(self):
        return {
            "id": self.watch_condition.get("condition"),
            "params": [{
                "name": param.get_parameter_name(),
                "disable": False,
                "value": param.value
            } for param in self.watch_condition.get("params")]
        }


class _ConditionParameterValue:
    """Condition parameter data container"""
    def __init__(self, parameter, value):
        self.parameter = parameter
        self.value = value

    def get_parameter_name(self):
        return self.parameter.name


def recommend_watchpoints(condition_mgr: ConditionMgr, graph_stream, condition_context):
    """
    Recommend watchpoints.

    Args:
        condition_mgr (ConditionMgr): Condition manager instance.
        graph_stream (GraphHandler): Graph handler instance.
        condition_context (ConditionContext): Context for condition.

    Returns:
        list[WatchPointData], watch points to be created.
    """
    watch_points = []

    if not graph_stream.graph:
        logger.warning("Given graph is None.")
        return watch_points

    if not settings.ENABLE_RECOMMENDED_WATCHPOINTS:
        return watch_points

    # add weight watch points
    merged_info = _get_basic_node_info(TargetTypeEnum.WEIGHT.value, graph_stream)
    _recommend_weight_initialization(merged_info, condition_mgr, watch_points, condition_context)
    _recommend_weight_change_too_large(merged_info, condition_mgr, watch_points, condition_context)

    # Because we cannot identify trainable weights currently, weight_no_change and weight_change_too_small will not be
    # recommended.
    trainable_weight_nodes = []
    _recommend_weight_not_changed(condition_mgr, trainable_weight_nodes, watch_points, condition_context)
    _recommend_weight_change_too_small(condition_mgr, trainable_weight_nodes, watch_points, condition_context)

    # add gradient watch points
    merged_info = _get_basic_node_info(TargetTypeEnum.GRADIENT.value, graph_stream)
    _recommend_gradient_vanishing(merged_info, condition_mgr, watch_points, condition_context)

    # add tensor watch points
    merged_info = _get_basic_node_info(TargetTypeEnum.TENSOR.value, graph_stream)
    _recommend_overflow_ascend_chip(merged_info, condition_mgr, watch_points, condition_context)
    _recommend_tensor_overflow(merged_info, condition_mgr, watch_points, condition_context)
    _recommend_tensor_all_zero(merged_info, condition_mgr, watch_points, condition_context)
    return watch_points


def _recommend_tensor_all_zero(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend tensor all zero watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.TENSOR_ALL_ZERO.value, condition_context):
        return
    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.TENSOR_ALL_ZERO.value)
    tensor_all_zero_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [_ConditionParameterValue(
                parameter=condition.get_parameter_definition("zero_percentage_ge"),
                value=100  # set default value to 100
            )]
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(tensor_all_zero_watchpoint)


def _recommend_tensor_overflow(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend tensor general overflow watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.TENSOR_OVERFLOW.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.TENSOR_OVERFLOW.value)
    overflow_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": []
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(overflow_watchpoint)


def _recommend_overflow_ascend_chip(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend tensor overflow watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.OVERFLOW_ASCEND_CHIP.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.OVERFLOW_ASCEND_CHIP.value)
    overflow_d_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": []
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(overflow_d_watchpoint)


def _recommend_gradient_vanishing(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend gradient vanishing watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.GRADIENT_VANISHING.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.GRADIENT_VANISHING.value)
    gradient_vanishing_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [_ConditionParameterValue(
                parameter=condition.get_parameter_definition("abs_mean_lt"),
                value=1e-9  # set default value to 1e-9
            )]
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(gradient_vanishing_watchpoint)


def _recommend_weight_change_too_small(condition_mgr, trainable_weight_nodes, watch_points, condition_context):
    """Recommend weight change too small watchpoint."""
    if not trainable_weight_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.WEIGHT_CHANGE_TOO_SMALL.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.WEIGHT_CHANGE_TOO_SMALL.value)
    weight_change_too_small_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [
                _ConditionParameterValue(
                    parameter=condition.get_parameter_definition("abs_update_ratio_mean_lt"),
                    value=1.0e-4  # set default value to 1.0e-4
                ),
            ]
        },
        watch_nodes=trainable_weight_nodes,
    )
    watch_points.append(weight_change_too_small_watchpoint)


def _recommend_weight_not_changed(condition_mgr, trainable_weight_nodes, watch_points, condition_context):
    """Recommend weight not changed watchpoint."""
    if not trainable_weight_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.WEIGHT_NOT_CHANGED.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.WEIGHT_NOT_CHANGED.value)
    weight_no_change_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [
                _ConditionParameterValue(
                    parameter=condition.get_parameter_definition("rtol"),
                    value=1.0e-5  # set default value to 1.0e-5
                ),
                _ConditionParameterValue(
                    parameter=condition.get_parameter_definition("atol"),
                    value=1.0e-8  # set default value to 1.0e-8
                ),
            ]
        },
        watch_nodes=trainable_weight_nodes,
    )
    watch_points.append(weight_no_change_watchpoint)


def _recommend_weight_change_too_large(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend weight change too large watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.WEIGHT_CHANGE_TOO_LARGE.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.WEIGHT_CHANGE_TOO_LARGE.value)
    weight_initialization_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [_ConditionParameterValue(
                parameter=condition.get_parameter_definition("abs_update_ratio_mean_gt"),
                value=0.1  # set default value to 0.1
            )]
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(weight_initialization_watchpoint)


def _recommend_weight_initialization(basic_info_nodes, condition_mgr, watch_points, condition_context):
    """Recommend weight initialization watchpoint."""
    if not basic_info_nodes:
        return
    if not condition_mgr.has_condition(ConditionIdEnum.WEIGHT_INITIALIZATION.value, condition_context):
        return

    condition = condition_mgr.get_condition(condition_id=ConditionIdEnum.WEIGHT_INITIALIZATION.value)
    weight_initialization_watchpoint = _WatchPointData(
        watch_condition={
            "condition": condition.id,
            "params": [_ConditionParameterValue(
                parameter=condition.get_parameter_definition("zero_percentage_ge"),
                value=100  # set default value to 100
            )]
        },
        watch_nodes=basic_info_nodes.copy(),
    )
    watch_points.append(weight_initialization_watchpoint)


def _get_basic_node_info(node_category, graph_stream):
    """Get node merged info."""
    basic_info_nodes = _get_basic_node_info_by_node_category(node_category, graph_stream)
    merged_info = _merge_nodes(basic_info_nodes, graph_stream.whole_graph)
    merged_info = _add_graph_name(merged_info, graph_stream)
    return merged_info


def _get_basic_node_info_by_node_category(node_category, graph_stream):
    """Get node basic info by node category."""
    all_graph_nodes = graph_stream.get_searched_nodes(pattern={'node_category': node_category})
    basic_info_nodes = []
    for graph_name, nodes in all_graph_nodes.items():
        if len(all_graph_nodes) == 1:
            logger.debug("This is a single graph")
            graph_name = ""
        for node in nodes:
            if graph_name == "":
                basic_node_info = NodeBasicInfo(name=node.name, full_name=node.full_name, type=node.type)
            else:
                basic_node_info = graph_stream.construct_node_basic_info(
                    full_name=node.full_name, graph_name=graph_name, node_name=node.name, node_type=node.type)
            basic_info_nodes.append(basic_node_info)
    return basic_info_nodes


def _merge_nodes(leaf_nodes, graph):
    """merge nodes in one graph"""
    unmerged_tree = graph.get_nodes(leaf_nodes)
    tmp_node_queue = Queue.Queue()

    # watch node list in layer order
    watch_nodes = []
    for node in unmerged_tree:
        if node["type"] != "name_scope":
            # if node is leaf_node, it is totally chosen
            node["status"] = SELECTED_STATUS
        else:
            # if node is not leaf_node, it is not chosen initially
            node["status"] = UNSELECTED_STATUS
        tmp_node_queue.put(node)
    while not tmp_node_queue.empty():
        cur_node = tmp_node_queue.get()
        watch_nodes.append(cur_node)
        for sub_node in cur_node["nodes"]:
            if sub_node["type"] != "name_scope":
                # if node is leaf_node, it is totally chosen
                sub_node["status"] = SELECTED_STATUS
            else:
                # if node is not leaf_node, it is not chosen initially
                sub_node["status"] = UNSELECTED_STATUS
            tmp_node_queue.put(sub_node)

    merged_watch_nodes = []
    while watch_nodes:
        cur_node = watch_nodes.pop()
        node_name = cur_node["name"]
        sub_count = graph.normal_node_map.get(node_name).subnode_count
        if len(cur_node["nodes"]) < sub_count or not cur_node["nodes"]:
            continue
        is_all_chosen = True
        for sub_node in cur_node["nodes"]:
            if sub_node["status"] != SELECTED_STATUS:
                is_all_chosen = False
                break

        if is_all_chosen:
            cur_node["status"] = SELECTED_STATUS
            merged_watch_nodes.append(cur_node)
        else:
            cur_node["status"] = HALF_SELECTED_STATUS
    logger.debug("merged_watch_nodes: %s", merged_watch_nodes)
    out_nodes = []
    for node_info in merged_watch_nodes:
        node_basic_info = NodeBasicInfo(name=node_info["name"], full_name=node_info["name"], type=node_info["type"])
        out_nodes.append(node_basic_info)
    logger.debug("out_nodes: %s", out_nodes)
    return out_nodes


def _add_graph_name(nodes, graph_stream):
    """add graph_name in node.name"""
    if len(graph_stream.graph) > 1:
        return nodes
    graph_name = graph_stream.graph_names[0]
    output_nodes = []
    for node in nodes:
        node_basic_info = graph_stream.construct_node_basic_info(
            full_name=node.name, graph_name=graph_name, node_name=node.name, node_type=node.type)
        output_nodes.append(node_basic_info)
    return output_nodes
