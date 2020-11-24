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
"""This module is aimed to deal with watchpoint commands."""

from mindinsight.conditionmgr.common.utils import NodeBasicInfo
from mindinsight.conditionmgr.condition import ConditionIdEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerCreateWatchPointError, DebuggerUpdateWatchPointError, \
    DebuggerDeleteWatchPointError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import ServerStatus, \
    Streams


class WatchpointOperator:
    """Watchpoint Operator."""

    def __init__(self, cache_store, condition_mgr):
        self._watchpoint_stream = cache_store.get_stream_handler(Streams.WATCHPOINT)
        self._graph_stream = cache_store.get_stream_handler(Streams.GRAPH)
        self._metadata_stream = cache_store.get_stream_handler(Streams.METADATA)
        self._condition_mgr = condition_mgr

    def create_watchpoint(self, params):
        """
        Create watchpoint.

        Args:
            - watch_condition (dict): The watch condition. The format is like:
                    {
                        "id": "tensor_too_large",
                        "params": [
                            {
                                "name": "abs_mean_gt",
                                "disable": false,
                                "value": 1.1
                            }
                        ]
                    }

                    - id (str): Id of condition.
                    - params (list[dict]): The list of param for this condition.
                - watch_nodes (list[str]): The list of node names.
                - watch_point_id (int): The id of watchpoint.
                - search_pattern (dict): The search pattern.
                - graph_name (str): The relative graph_name of the watched node.

        Returns:
            dict, the id of new watchpoint and metadata info.
        """
        watch_condition = params.get('watch_condition')
        log.info("Received create watchpoint request. WatchCondition: %s", watch_condition)
        metadata_stream = self._metadata_stream
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to create watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerCreateWatchPointError(
                "Failed to create watchpoint as the MindSpore is not in waiting state.")
        self._validate_watch_condition(watch_condition)

        watch_nodes = self._get_watch_node_with_basic_info(
            node_names=params.get('watch_nodes'),
            search_pattern=params.get('search_pattern'),
            graph_name=params.get('graph_name'))
        watchpoint_stream = self._watchpoint_stream
        watch_point_id = watchpoint_stream.create_watchpoint(
            self._condition_mgr, watch_condition, watch_nodes, params.get('watch_point_id'))
        log.info("Create watchpoint %d", watch_point_id)

        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable(metadata_stream.backend)
        res = metadata_stream.get(['state', 'enable_recheck'])
        res['id'] = watch_point_id
        return res

    def _validate_watch_condition(self, watch_condition):
        """Validate watch condition."""
        metadata_stream = self._metadata_stream
        if metadata_stream.backend == 'GPU' and watch_condition.get('id') in (
                ConditionIdEnum.OVERFLOW_ASCEND_CHIP.value, ConditionIdEnum.OPERATOR_OVERFLOW.value):
            log.error("GPU doesn't support overflow watch condition.")
            raise DebuggerParamValueError("GPU doesn't support overflow watch condition.")
        if metadata_stream.backend == 'Ascend' and watch_condition.get('id') == ConditionIdEnum.NAN.value:
            log.error("Ascend doesn't support nan watch condition.")
            raise DebuggerParamValueError("Ascend doesn't support nan watch condition.")

    def update_watchpoint(self, params):
        """
        Update watchpoint.

        Args:
            params (dict): Params for update watchpoint.

                - watch_point_id (int): The id of watchpoint.
                - watch_nodes (list[str]): The list of node names.
                - mode (int): The update operator on nodes. 0 for remove nodes from watch nodes.
                    1 for add nodes to watch nodes.
                - search_pattern (dict): The search pattern.
                - graph_name (str): The relative graph_name of the watched node.

        Returns:
            dict, the metadata info.
        """
        metadata_stream = self._metadata_stream
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to update watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerUpdateWatchPointError(
                "Failed to update watchpoint as the MindSpore is not in waiting state."
            )
        # validate parameter
        watchpoint_stream = self._watchpoint_stream
        watch_point_id = params.get('watch_point_id')
        watch_nodes = params.get('watch_nodes')
        if not watch_nodes or not watch_point_id:
            log.error("Invalid parameter for update watchpoint.")
            raise DebuggerParamValueError("Invalid parameter for update watchpoint.")
        watchpoint_stream.validate_watchpoint_id(watch_point_id)
        # get node basic info for watch nodes
        watch_nodes = self._get_watch_node_with_basic_info(
            node_names=params.get('watch_nodes'),
            search_pattern=params.get('search_pattern'),
            graph_name=params.get('graph_name'))
        watchpoint_stream.update_watchpoint(watch_point_id, watch_nodes, params.get('mode'))
        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable(metadata_stream.backend)
        log.info("Update watchpoint with id: %d", watch_point_id)
        return metadata_stream.get(['state', 'enable_recheck'])

    def _get_watch_node_with_basic_info(self, node_names, search_pattern=None, graph_name=None):
        """
        Get watch node with basic info.

        Args:
            node_names (list[str]): A list of node names.
            search_pattern (dict): Get watch node with search pattern. Default: None
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            list[NodeBasicInfo], a list of node basic infos.
        """
        graph_name = self._graph_stream.validate_graph_name(graph_name)
        if search_pattern is not None:
            watch_nodes = self._get_watch_nodes_by_search(node_names, search_pattern, graph_name)
        else:
            watch_nodes = self._get_node_basic_infos(node_names, graph_name=graph_name)
        return watch_nodes

    def _get_watch_nodes_by_search(self, watch_nodes, search_pattern, graph_name):
        """Get watched leaf nodes by search name."""
        watched_leaf_nodes = []
        graph_stream = self._graph_stream
        new_pattern = {'graph_name': graph_name}.update(search_pattern)
        for search_name in watch_nodes:
            search_nodes = graph_stream.get_searched_node_list(new_pattern)
            search_node_names = [
                NodeBasicInfo(name=node.name, full_name=node.full_name, type=node.type)
                for node in search_nodes
                if node.name.startswith(search_name)]
            watched_leaf_nodes.extend(search_node_names)

        log.debug("Update nodes: %s", watched_leaf_nodes)

        return watched_leaf_nodes

    def delete_watchpoint(self, watch_point_id=None):
        """
        Delete watchpoint.

        Args:
            watch_point_id (Union[None, int]): The id of watchpoint.
                If None, delete all watchpoints. Default: None.

        Returns:
            dict, the metadata info.
        """
        metadata_stream = self._metadata_stream
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to delete watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerDeleteWatchPointError(
                "Failed to delete watchpoint as the MindSpore is not in waiting state."
            )
        watchpoint_stream = self._watchpoint_stream
        watchpoint_stream.delete_watchpoint(watch_point_id)
        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable()
        log.info("Delete watchpoint with id: %s", watch_point_id)
        return metadata_stream.get(['state', 'enable_recheck'])

    def _get_node_basic_infos(self, node_names, graph_name=None):
        """
        Get node info according to node names.

        Args:
            node_names (list[str]): A list of node names.
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            list[NodeBasicInfo], a list of basic node infos.
        """
        if not node_names:
            return []
        graph_stream = self._graph_stream
        node_infos = []
        for node_name in node_names:
            node_info = graph_stream.get_node_basic_info(node_name, graph_name)
            node_infos.append(node_info)

        return node_infos
