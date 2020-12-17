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
from queue import Queue

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerCreateWatchPointError, DebuggerUpdateWatchPointError, \
    DebuggerDeleteWatchPointError, DebuggerConditionUnavailableError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import ServerStatus, \
    Streams, is_cst_type
from mindinsight.debugger.conditionmgr.condition import ConditionIdEnum, ConditionContext
from mindinsight.debugger.conditionmgr.recommender import get_basic_node_info
from mindinsight.debugger.stream_handler.watchpoint_handler import validate_watch_condition


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

        validate_watch_condition(self._condition_mgr, watch_condition)
        condition_id = watch_condition.get('id')
        condition = self._condition_mgr.get_condition(condition_id)
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step)
        if not condition.is_available(condition_context):
            log.error("Failed to create watchpoint as the condition is not available.")
            raise DebuggerConditionUnavailableError(
                "Failed to create watchpoint as the condition is not available.")

        watch_nodes = get_basic_node_info(condition.supported_target_type.value, self._graph_stream).copy()
        watchpoint_stream = self._watchpoint_stream
        watch_point_id = watchpoint_stream.create_watchpoint(
            self._condition_mgr, watch_condition, watch_nodes, params.get('watch_point_id'))
        log.info("Create watchpoint %d", watch_point_id)

        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable()
        res = metadata_stream.get(['state', 'enable_recheck'])
        res['id'] = watch_point_id
        return res

    def _validate_watch_condition(self, watch_condition):
        """Validate watch condition."""
        metadata_stream = self._metadata_stream
        if metadata_stream.backend == 'GPU' and watch_condition.get('id') == ConditionIdEnum.OPERATOR_OVERFLOW.value:
            log.error("GPU doesn't support overflow watch condition.")
            raise DebuggerParamValueError("GPU doesn't support overflow watch condition.")

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
        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable()
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
        if not node_names:
            return []
        graph_name = self._graph_stream.validate_graph_name(graph_name)
        if search_pattern is not None:
            watch_nodes = self._get_watch_nodes_by_search(node_names, search_pattern, graph_name)
        else:
            watch_nodes = self._get_node_basic_infos(node_names, graph_name=graph_name)
        return watch_nodes

    def _get_watch_nodes_by_search(self, node_names, search_pattern, graph_name):
        """
        Get watched leaf nodes by search name.

        Args:
            node_names (list[str]): A list of node names.
            search_pattern (dict): Get watch node with search pattern.

                - name (str): The name pattern.
                - node_category (str): The node_category.
            graph_name (str): The relative graph_name of the watched node.

        Returns:
            list[NodeBasicInfo], a list of node basic infos.
        """
        search_pattern['graph_name'] = graph_name
        search_nodes = self._graph_stream.search_nodes(search_pattern)
        watch_node_names = set()
        for name in node_names:
            names = self._get_watch_names_by_search(search_nodes, name)
            watch_node_names.update(names)
        watch_node_info = self._get_node_basic_infos(watch_node_names, graph_name=graph_name)
        log.debug("Update nodes: %s", watch_node_info)

        return watch_node_info

    def _get_watch_names_by_search(self, search_nodes, target_node_name):
        """
        Get watch names according to search results.

        Args:
            search_nodes (dict): Search result.
                The format is like {'nodes': [<Search Node>]}. The <Search Node> format is like
                {'name': <UI node name>, 'type': <node type>, 'nodes': [<Search Node>]}
            target_node_name (str): Node name for UI.

        Returns:
            set[str], collection of names.
        """
        names = set()
        tmp_queue = Queue()
        tmp_queue.put(search_nodes)
        while not tmp_queue.empty():
            cur_node = tmp_queue.get()
            for node in cur_node.get('nodes'):
                node_name = node.get('name')
                if not target_node_name.startswith(node_name) or is_cst_type(node.get('type')):
                    continue
                if target_node_name == node_name:
                    self._add_leaf_node_collection(node, names)
                    return names
                tmp_queue.put(node)
        # the target node name is not in search nodes.
        log.debug("node %s is not in search nodes.")
        names.add(target_node_name)
        return names

    def _add_leaf_node_collection(self, node, names):
        """
        Get leaf node collection in search node object.

        Args:
            node (dict): Search Node object.
            names (set): Set of node names.
        """
        # if the node is leaf node
        if not node.get('nodes'):
            names.add(node.get('name'))
            return
        # traverse the search node object
        for sub_node in node.get('nodes'):
            self._add_leaf_node_collection(sub_node, names)

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
        Get watch node info according to node names.

        Args:
            node_names (Union[set[str], list[str]]): A collection of node names.
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            list[NodeBasicInfo], a list of basic watch nodes info.
        """
        if not node_names:
            return []
        graph_stream = self._graph_stream
        node_infos = []
        for node_name in node_names:
            node_info = graph_stream.get_node_basic_info(node_name, graph_name)
            if not is_cst_type(node_info.type):
                node_infos.append(node_info)

        return node_infos
