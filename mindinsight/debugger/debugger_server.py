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
"""Implement the debugger server."""
import signal
from concurrent import futures
from threading import Thread
import grpc

from mindinsight.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.conditionmgr.condition import ConditionContext, ConditionIdEnum
from mindinsight.conditionmgr.recommender import recommend_watchpoints
from mindinsight.conf import settings
from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.datavisual.utils.tools import to_float
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError, DebuggerCreateWatchPointError, DebuggerUpdateWatchPointError, \
    DebuggerDeleteWatchPointError, DebuggerContinueError, DebuggerPauseError, \
    DebuggerCompareTensorError, DebuggerRecheckError, DebuggerStepNumError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import get_ack_reply, ServerStatus, \
    create_view_event_from_tensor_history, Streams, is_scope_type, RunLevel
from mindinsight.conditionmgr.common.utils import NodeBasicInfo
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_grpc_server import DebuggerGrpcServer
from mindinsight.debugger.proto import debug_grpc_pb2_grpc as grpc_server_base
from mindinsight.debugger.proto.debug_grpc_pb2 import RunCMD
from mindinsight.debugger.stream_operator.tensor_detail_info import TensorDetailInfo
from mindinsight.utils.exceptions import MindInsightException
from mindinsight.utils.tensor import TensorUtils, MAX_DIMENSIONS_FOR_TENSOR


class DebuggerServer:
    """The server manager of debugger."""
    # max step number should be less than int32
    _MAX_STEP_NUM = 2 ** 31 - 1

    def __init__(self, grpc_port=None):
        self.grpc_port = grpc_port
        self.condition_mgr = ConditionMgr()
        self.cache_store = DebuggerCache()
        self.grpc_server = DebuggerGrpcServer(self.cache_store, self.condition_mgr)
        self.grpc_server_manager = None
        self.back_server = None

    def get_conditions(self, train_id):
        """Get all default conditions"""
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step, (1, 0))
        log.debug("Train_id: %s, backend: %s", train_id, condition_context.backend)
        return self.condition_mgr.get_all(condition_context)

    def get_condition_collections(self, train_id):
        """Get default condition_collections"""
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step, (1, 0))
        log.debug("Train_id: %s, backend: %s", train_id, condition_context.backend)
        return self.condition_mgr.get_all_collections(condition_context)

    def set_recommended_watch_points(self, set_recommended, train_id):
        """set recommended watch points."""
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step, (1, 0))
        log.debug("Train_id: %s, backend: %s", train_id, condition_context.backend)
        res = metadata_stream.get(['state', 'enable_recheck'])
        if set_recommended:
            res['id'] = self._add_recommended_watchpoints(condition_context)
        metadata_stream.recommendation_confirmed = True
        return res

    def _add_recommended_watchpoints(self, condition_context):
        """Add predefined watchpoints."""
        log.debug("Add predefined watchpoints.")
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        watchpoints = recommend_watchpoints(self.condition_mgr, graph_stream, condition_context)
        watch_point_stream_handler = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watch_points_ids = []
        for watchpoint in watchpoints:
            watch_points_id = watch_point_stream_handler.create_watchpoint(
                watch_condition=watchpoint.get_watch_condition_dict(),
                watch_nodes=watchpoint.watch_nodes,
                condition_mgr=self.condition_mgr
            )
            watch_points_ids.append(watch_points_id)
        return watch_points_ids

    def start(self):
        """Start server."""
        grpc_port = self.grpc_port if self.grpc_port else "50051"
        host = settings.HOST if hasattr(settings, 'HOST') else '[::]'
        hostname = "{}:{}".format(host, grpc_port)
        # initialize a grpc server
        grpc_server_manager = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        grpc_server_base.add_EventListenerServicer_to_server(self.grpc_server, grpc_server_manager)
        grpc_server_manager.add_insecure_port(hostname)
        grpc_server_manager.start()
        my_server_thread = Thread(target=grpc_server_manager.wait_for_termination)
        # start grpc server
        my_server_thread.start()
        self.back_server = my_server_thread
        self.grpc_server_manager = grpc_server_manager
        # register stop server handler
        signal.signal(signal.SIGINT, self._stop_handler)
        log.info("Start grpc server %s", hostname)

    def _stop_handler(self, signum, frame):
        """Register stop server handler."""
        self.stop()
        log.debug("Deal with stop signal: %s, %s", signum, frame)

    def stop(self):
        """Stop debugger server."""
        log.info("Send terminate info to client.")
        self.control({'mode': 'terminate'})
        self.grpc_server_manager.stop(grace=None)
        self.back_server.join()
        log.info("Stop debugger server.")

    def poll_data(self, pos):
        """
        Get the pos-th data from DebuggerCache.

        Args:
            pos (int): The index of data.

        Returns:
            dict, the data to be updated.
        """
        if not isinstance(pos, str):
            log.error("Pos should be string. Received: %s", pos)
            raise DebuggerParamValueError("Pos should be string.")

        reply = self.cache_store.get_data(pos)

        return reply

    def search(self, filter_condition):
        """
        Search for single node in graph.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The name pattern.
                - graph_name (str): The graph name.
                - watch_point_id (int): The id of watchpoint. Default: 0.
                - node_category (str): The node_category. Default: None

        Returns:
            dict, the searched nodes.
        """
        log.info("receive search request with filter_condition: %s", filter_condition)
        # validate watchpoint id
        watch_point_id = filter_condition.pop('watch_point_id', 0)
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watchpoint_stream.validate_watchpoint_id(watch_point_id)
        # validate and update graph name
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        graph_name = graph_stream.validate_graph_name(filter_condition.get('graph_name'))
        filter_condition['graph_name'] = graph_name
        # get searched graph
        graph = graph_stream.search_nodes(filter_condition)
        # add watched label to graph
        watchpoint_stream.set_watch_nodes(graph, graph_stream, watch_point_id, graph_name)
        return graph

    def tensor_comparisons(self, name, shape, detail='data', tolerance='0'):
        """
        Get tensor comparisons data for given name, detail, shape and tolerance.

        Args:
            name (str): The name of tensor for ui.
            detail (str): Specify which data to query. Current available value is 'data' which means
                          concrete tensor data. Histogram or unique count can be supported in the future.
            shape (str): Specify concrete dimensions of shape.
            tolerance (str): Specify tolerance of difference between current step tensor and previous
                             step tensor. Default value is 0.

        Raises:
            DebuggerParamValueError, If node type is not parameter or value of detail is not support.
            DebuggerCompareTensorError, If MindSpore is not in waiting state.
        Returns:
            dict, the retrieved data.
        """
        if self.cache_store.get_stream_handler(
                Streams.METADATA).state != ServerStatus.WAITING.value:
            log.error("Failed to compare tensors as the MindSpore is not in waiting state.")
            raise DebuggerCompareTensorError(
                "Failed to compare tensors as the MindSpore is not in waiting state."
            )
        self.validate_tensor_param(name, detail)
        # Limit to query max two dimensions for tensor in table view.
        parsed_shape = TensorUtils.parse_shape(shape, limit=MAX_DIMENSIONS_FOR_TENSOR)
        node_type, tensor_name = self._get_tensor_name_and_type_by_ui_name(name)
        tolerance = to_float(tolerance, 'tolerance')
        tensor_stream = self.cache_store.get_stream_handler(Streams.TENSOR)
        if node_type == NodeTypeEnum.PARAMETER.value:
            reply = tensor_stream.get_tensors_diff(tensor_name, parsed_shape, tolerance)
        else:
            raise DebuggerParamValueError(
                "The node type must be parameter, but got {}.".format(node_type))
        return reply

    def retrieve(self, mode, filter_condition=None):
        """
        Retrieve data according to mode and params.

        Args:
            mode (str): The type of info message.
            filter_condition (dict): The filter condition.

        Returns:
            dict, the retrieved data.
        """
        log.info("receive retrieve request for mode:%s\n, filter_condition: %s", mode,
                 filter_condition)
        mode_mapping = {
            'all': self._retrieve_all,
            'node': self._retrieve_node,
            'watchpoint': self._retrieve_watchpoint,
            'watchpoint_hit': self._retrieve_watchpoint_hit
        }
        # validate param <mode>
        if mode not in mode_mapping.keys():
            log.error("Invalid param <mode>. <mode> should be in ['all', 'node', 'watchpoint', "
                      "'watchpoint_hit'], but got %s.", mode_mapping)
            raise DebuggerParamValueError("Invalid mode.")
        # validate backend status
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state == ServerStatus.PENDING.value:
            log.info("The backend is in pending status.")
            return metadata_stream.get()

        filter_condition = {} if filter_condition is None else filter_condition
        reply = mode_mapping[mode](filter_condition)

        return reply

    def _retrieve_all(self, filter_condition=None):
        """Retrieve metadata, root graph and watchpoint list."""
        if filter_condition:
            log.error("No filter condition required for retrieve all request.")
            raise DebuggerParamTypeError("filter_condition should be empty.")
        self.cache_store.clean_data()
        log.info("Clean data queue cache when retrieve all request.")
        result = {}
        for stream in [Streams.METADATA, Streams.GRAPH]:
            sub_res = self.cache_store.get_stream_handler(stream).get()
            result.update(sub_res)

        sub_res = self._hide_parameters_for_ui()
        result.update(sub_res)

        return result

    def _retrieve_node(self, filter_condition):
        """
        Retrieve node info.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The name of single node.
                - graph_name (str): The relative graph_name of the node.
                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.
                - watch_point_id (int): The id of watchpoint.

        Returns:
            dict, reply with graph.
        """
        log.debug("Retrieve node %s.", filter_condition)
        # validate node name
        node_name = filter_condition.get('name')
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        graph_name = graph_stream.validate_graph_name(filter_condition.get('graph_name'))
        if node_name:
            # validate node name
            graph_stream.get_node_type(node_name, graph_name)
        filter_condition['single_node'] = bool(filter_condition.get('single_node'))
        filter_condition['graph_name'] = graph_name
        reply = self._get_nodes_info(filter_condition)
        return reply

    def _get_nodes_info(self, filter_condition):
        """
        Get nodes info.

        Args:
            filter_condition (dict): The filter condition.

                - name (str): The node name.
                - graph_name (str): The relative graph_name of the node.
                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.
                - watch_point_id (int): The id of watchpoint.

        Returns:
            dict, reply with graph.
        """
        # validate watch_point_id
        watch_point_id = filter_condition.get('watch_point_id', 0)
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watchpoint_stream.validate_watchpoint_id(watch_point_id)
        # get graph
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        reply = graph_stream.get(filter_condition)
        graph = reply.get('graph')
        # add watched label to graph
        watchpoint_stream.set_watch_nodes(graph, graph_stream, watch_point_id, filter_condition.get('graph_name'))
        return reply

    def retrieve_tensor_history(self, node_name, graph_name=None):
        """
        Retrieve tensor history for leaf node.

        Args:
            node_name (str): The name of leaf node.
            graph_name (str): The graph name. Default: None.

        Returns:
            dict, the tensor history and metadata.
        """
        log.info("Retrieve tensor history for node: %s.", node_name)
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state == ServerStatus.PENDING.value:
            log.info("The backend is in pending status.")
            return metadata_stream.get(['state', 'step'])
        res = self._get_tensor_history(node_name, graph_name)
        return res

    def _get_tensor_history(self, node_name, graph_name=None):
        """
        Get tensor history for single node.

        Args:
            node_name (str): The name of leaf node.
            graph_name (str): The graph name. Default: None.

        Returns:
            dict, the tensor history and metadata.
        """
        # get basic tensor history
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        tensor_history = graph_stream.get_tensor_history(node_name, graph_name)
        # add tensor value for tensor history
        self._add_tensor_value_for_tensor_history(tensor_history, node_name)
        # add hit label for tensor history
        watchpoint_hit_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        watchpoint_hit_stream.update_tensor_history(tensor_history)
        # add metadata
        metadata = self.cache_store.get_stream_handler(Streams.METADATA).get(['state', 'step'])
        tensor_history.update(metadata)
        return tensor_history

    def _add_tensor_value_for_tensor_history(self, tensor_history, node_name):
        """
        Add tensor value for_tensor_history and send ViewCMD if tensor value missed.

        Args:
            tensor_history (list[dict]): A list of tensor info, including name and type.
            node_name (str): The UI node name.

        Returns:
            dict, the tensor info.
        """
        tensor_stream = self.cache_store.get_stream_handler(Streams.TENSOR)
        missed_tensors = tensor_stream.update_tensor_history(tensor_history)
        if missed_tensors:
            view_cmd = create_view_event_from_tensor_history(missed_tensors)
            self.cache_store.put_command({'view_cmd': view_cmd, 'node_name': node_name})
            log.debug("Send view cmd.")

    def retrieve_tensor_value(self, name, detail, shape, graph_name=None, prev=False):
        """Retrieve the tensor value."""
        log.info("Retrieve tensor value: name: %s, detail: %s, shape: %s", name, detail, shape)
        self.validate_tensor_param(name, detail)
        # Limit to query max two dimensions for tensor in table view.
        parsed_shape = TensorUtils.parse_shape(shape, limit=MAX_DIMENSIONS_FOR_TENSOR)
        node_type, tensor_name = self._get_tensor_name_and_type_by_ui_name(name, graph_name)
        reply = self.cache_store.get_stream_handler(Streams.TENSOR).get(
            {'name': tensor_name,
             'node_type': node_type,
             'shape': parsed_shape,
             'prev': prev}
        )
        reply['tensor_value']['name'] = name

        return reply

    def _get_tensor_name_and_type_by_ui_name(self, name, graph_name=None):
        """
        Get inner tensor name and type by UI name.

        Args:
            name (str): Node name shown in UI.
            graph_name (Union[str, None]): The graph name, default is: None.

        Returns:
            str, full name of tensor.
            str, node type of tensor.
        """
        node_name, slot = name.rsplit(':', 1)
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        graph_name = graph_name if graph_name else graph_stream.get_graph_id_by_name(node_name)
        node_type = graph_stream.get_node_type(node_name, graph_name)
        full_name = graph_stream.get_full_name(node_name, graph_name)
        tensor_name = full_name + ':' + slot
        return node_type, tensor_name

    @staticmethod
    def validate_tensor_param(name, detail):
        """Validate params for retrieve tensor request."""
        # validate name
        if not isinstance(name, str) or ':' not in name:
            log.error("Invalid tensor name. Received: %s", name)
            raise DebuggerParamValueError("Invalid tensor name.")
        # validate data
        if detail != 'data':
            log.error("Invalid detail value. Received: %s", detail)
            raise DebuggerParamValueError("Invalid detail value.")

    def _retrieve_watchpoint(self, filter_condition):
        """
        Retrieve watchpoint.

        Args:
            filter_condition (dict): Filter condition.

                - watch_point_id (int):  The id of watchpoint. If not given, return all watchpoints.
                - name (str): The name of single node.
                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.

        Returns:
            dict, watch point list or relative graph.
        """
        watchpoint_id = filter_condition.get('watch_point_id', 0)
        if not watchpoint_id:
            reply = self._hide_parameters_for_ui()
            log.debug("Get condition of watchpoints.")
        else:
            reply = self._retrieve_node(filter_condition)
            log.debug("Get graph of %d-th watchpoint.", watchpoint_id)

        return reply

    def _retrieve_watchpoint_hit(self, filter_condition):
        """
        Retrieve watchpoint hit.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The name of single node.
                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.

        Returns:
            dict, watch point list or relative graph.
        """
        node_name = filter_condition.get('name')
        # get all watchpoint hit list
        if node_name is None:
            reply = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT).get()
            return reply
        graph_name = self.cache_store.get_stream_handler(Streams.GRAPH).validate_graph_name(
            filter_condition.get('graph_name'))
        # get tensor history
        reply = self._get_tensor_history(node_name, graph_name)
        log.debug("Get tensor history for watchpoint hit node.")
        # get single graph
        if filter_condition.get('single_node'):
            filter_condition['graph_name'] = graph_name
            graph = self._get_nodes_info(filter_condition)
            reply.update(graph)
        log.debug("Get tensor history for watchpoint hit node.")

        return reply

    def create_watchpoint(self, watch_condition, watch_nodes=None, watch_point_id=None, search_pattern=None,
                          graph_name=None):
        """
        Create watchpoint.

        Args:
            watch_condition (dict): The watch condition. The format is like:
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
            watch_nodes (list[str]): The list of node names.
            watch_point_id (int): The id of watchpoint.
            search_pattern (dict): The search pattern. Default: None.
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            dict, the id of new watchpoint and metadata info.
        """
        log.info("Received create watchpoint request. WatchCondition: %s", watch_condition)
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to create watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerCreateWatchPointError(
                "Failed to create watchpoint as the MindSpore is not in waiting state.")
        if metadata_stream.backend == 'GPU' and watch_condition.get('id') in (
                ConditionIdEnum.OVERFLOW_ASCEND_CHIP.value, ConditionIdEnum.OPERATOR_OVERFLOW.value):
            log.error("GPU doesn't support overflow watch condition.")
            raise DebuggerParamValueError("GPU doesn't support overflow watch condition.")

        if metadata_stream.backend == 'Ascend' and watch_condition.get('id') == ConditionIdEnum.NAN.value:
            log.error("Ascend doesn't support nan watch condition.")
            raise DebuggerParamValueError("Ascend doesn't support nan watch condition.")

        watch_nodes = self._get_watch_node_with_basic_info(
            node_names=watch_nodes, search_pattern=search_pattern, graph_name=graph_name)
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watch_point_id = watchpoint_stream.create_watchpoint(
            self.condition_mgr, watch_condition, watch_nodes, watch_point_id)
        log.info("Create watchpoint %d", watch_point_id)

        metadata_stream.enable_recheck = watchpoint_stream.is_recheckable(metadata_stream.backend)
        res = metadata_stream.get(['state', 'enable_recheck'])
        res['id'] = watch_point_id
        return res

    def update_watchpoint(self, watch_point_id, watch_nodes, mode, search_pattern=None, graph_name=None):
        """
        Update watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.
            watch_nodes (list[str]): The list of node names.
            mode (int): The update operator on nodes. 0 for remove nodes from watch nodes.
                1 for add nodes to watch nodes.
            search_pattern (dict): The search pattern. Default: None.
            graph_name (str): The relative graph_name of the watched node. Default: None.

        Returns:
            dict, the metadata info.
        """
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to update watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerUpdateWatchPointError(
                "Failed to update watchpoint as the MindSpore is not in waiting state."
            )
        # validate parameter
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watchpoint_stream.validate_watchpoint_id(watch_point_id)
        if not watch_nodes or not watch_point_id:
            log.error("Invalid parameter for update watchpoint.")
            raise DebuggerParamValueError("Invalid parameter for update watchpoint.")
        # get node basic info for watch nodes
        watch_nodes = self._get_watch_node_with_basic_info(watch_nodes, search_pattern, graph_name)
        watchpoint_stream.update_watchpoint(watch_point_id, watch_nodes, mode)
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
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        graph_name = graph_stream.validate_graph_name(graph_name)
        if search_pattern is not None:
            watch_nodes = self._get_watch_nodes_by_search(node_names, search_pattern, graph_name)
        else:
            watch_nodes = self._get_node_basic_infos(node_names, graph_name=graph_name)
        return watch_nodes

    def _get_watch_nodes_by_search(self, watch_nodes, search_pattern, graph_name):
        """Get watched leaf nodes by search name."""
        watched_leaf_nodes = []
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
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
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to delete watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerDeleteWatchPointError(
                "Failed to delete watchpoint as the MindSpore is not in waiting state."
            )
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
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
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        node_infos = []
        for node_name in node_names:
            node_info = graph_stream.get_node_basic_info(node_name, graph_name)
            node_infos.append(node_info)

        return node_infos

    def control(self, params=None):
        """
        Control the training process.

        Args:
            params (dict): The control params.

                - mode (str): Acceptable control command, including `continue`,
                    `pause` and `terminate`.
                - level (str): The control granularity, `node` level or `step` level.
                    Default: `step`.
                - steps (int): Specify the steps that training should run.
                    Used when `level` is `step`.
                - name (str): Specify the name of the node. Used when `level` is `node`.
                - graph_name (str): The graph name.

        Returns:
            dict, the response.
        """
        log.info("Receive control request: %s.", params)
        mode = params.get('mode')
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if mode == 'continue':
            reply = self._continue(metadata_stream, params)
        elif mode in ['pause', 'terminate']:
            mode_mapping = {
                'pause': self._pause,
                'terminate': self._terminate
            }
            reply = mode_mapping.get(mode)(metadata_stream)
        else:
            log.error("Invalid control mode %s", mode)
            raise DebuggerParamValueError("Invalid control mode.")

        return reply

    def _continue(self, metadata_stream, params):
        """
        Send RunCMD to MindSpore.

        Args:
            metadata_stream (MetadataHandler): The metadata_handler
            params (dict): The control params.

        Returns:
            dict, metadata info.
        """
        if metadata_stream.state != ServerStatus.WAITING.value:
            self.cache_store.put_data(metadata_stream.get())
            log.error("MindSpore is not ready to run. Current state is: %s", metadata_stream.state)
            raise DebuggerContinueError(
                "MindSpore is not ready to run or is running currently."
            )
        metadata_stream.state = ServerStatus.RUNNING.value
        try:
            self._validate_continue_params(params)
            event = self._construct_run_event(params)
            self._send_watchpoints()
            self.cache_store.put_command(event)
        except MindInsightException as err:
            log.error("Failed to send run event.")
            log.exception(err)
            metadata_stream.state = ServerStatus.WAITING.value
            raise DebuggerContinueError("Failed to send run command.")
        else:
            metadata_stream.enable_recheck = False
            log.debug("Send the RunCMD to command queue.")
        return metadata_stream.get(['state', 'enable_recheck'])

    def _validate_continue_params(self, params):
        """
        Validate continue params.

        Args:
            params (dict): The control params.

                - level (str): The control granularity, `node`, `step` or `recheck` level.
                    Default: `step`.
                - steps (int): Specify the steps that training should run.
                    Used when `level` is `step`.
                - name (str): Specify the name of the node. Used when `level` is `node`.
                - graph_name (str): The graph name.

        Raises:
            DebuggerParamValueError: Params are invalid.
        """
        # validate level
        level = params.get('level', 'step')
        if level not in [RunLevel.NODE.value, RunLevel.STEP.value, RunLevel.RECHECK.value]:
            log.error("Invalid Value. `level` should be `step`, `node` or `recheck`. Got %s", level)
            raise DebuggerParamValueError("level` should be `step`, `node` or `recheck`.")

        # validate steps
        step_num = params.get('steps', 1)
        if not isinstance(step_num, int) or not (step_num == -1 or 0 < step_num <= self._MAX_STEP_NUM):
            log.error("Invalid step value. Step number should be integer and in [1, 2^31 - 1] or -1.")
            raise DebuggerStepNumError

        # validate node name
        if level == RunLevel.NODE.value:
            node_name = params.get('name')
            graph_name = params.get('graph_name')
            self._validate_continue_node_name(node_name, graph_name)

    def _construct_run_event(self, params):
        """
        Construct run cmd from input control params.

        Args:
            params (dict): The control params.

                - level (str): The control granularity, `node`, `step` or `recheck` level.
                    Default: `step`.
                - steps (int): Specify the steps that training should run.
                    Used when `level` is `step`.
                - name (str): Specify the name of the node. Used when `level` is `node`.
                - graph_name (str): The graph name.

        Returns:
            EventReply, control event with run command.
        """
        level = params.get('level', 'step')
        # construct run command events
        event = get_ack_reply()
        if level == 'step':
            steps = params.get('steps', 1)
            run_cmd = RunCMD(run_level='step', run_steps=steps)
        elif level == 'node':
            name = params.get('name', '')
            graph_name = params.get('graph_name')
            if name:
                name = self.cache_store.get_stream_handler(Streams.GRAPH).get_full_name(name, graph_name)
            run_cmd = RunCMD(run_level='node', node_name=name)
        else:
            run_cmd = RunCMD(run_level='recheck')

        event.run_cmd.CopyFrom(run_cmd)
        log.debug("Construct run event. %s", event)
        return event

    def _validate_continue_node_name(self, node_name, graph_name):
        """Validate if the node is a leaf node."""
        if not node_name:
            return
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        node_type = graph_stream.get_node_type(node_name, graph_name)
        if is_scope_type(node_type):
            log.error("Scope type node has no tensor history.")
            raise DebuggerParamValueError("Invalid leaf node name.")

    def _send_watchpoints(self):
        """Set watchpoints."""
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        set_commands = watchpoint_stream.get_pending_commands(self.cache_store.get_stream_handler(Streams.GRAPH))
        if set_commands:
            for set_cmd in set_commands:
                event = get_ack_reply()
                event.set_cmd.CopyFrom(set_cmd)
                self.cache_store.put_command(event)
            watchpoint_stream.sync_set_cmd(set_commands)
            log.debug("Send SetCMD to MindSpore. %s", event)

    def _pause(self, metadata_stream):
        """
        Pause the training.

        Args:
            metadata_stream (MetadataHandler): The metadata stream handler.

        Returns:
            dict, metadata info.
        """
        if metadata_stream.state != ServerStatus.RUNNING.value:
            self.cache_store.put_data(metadata_stream.get())
            log.error("The MindSpore is not running.")
            raise DebuggerPauseError("The MindSpore is not running.")
        metadata_stream.state = 'waiting'
        event = get_ack_reply()
        event.run_cmd.CopyFrom(RunCMD(run_level='step', run_steps=0))
        self.cache_store.put_command(event)
        metadata_stream.enable_recheck = False
        log.debug("Send the Pause command")
        return metadata_stream.get(['state', 'enable_recheck'])

    def _terminate(self, metadata_stream):
        """
        Terminate the training.

        Args:
            metadata_stream (MetadataHandler): The metadata stream handler.

        Returns:
            dict, metadata info.
        """
        metadata_stream.state = 'pending'
        self.cache_store.clean_data()
        self.cache_store.clean_command()
        event = get_ack_reply()
        event.exit = True
        self.cache_store.put_command(event)
        metadata_stream.enable_recheck = False
        log.debug("Send the ExitCMD.")
        return metadata_stream.get(['state', 'enable_recheck'])

    def retrieve_node_by_bfs(self, node_name, graph_name=None, ascend=False):
        """
        Get the graph of the next node according to node_name.

        Args:
            node_name (str): The name of current chosen leaf node.
            graph_name (str): The graph name.
            ascend (bool): If True, traverse the input nodes;
                If False, traverse the output nodes. Default is True.

        Returns:
            dict, the next node information.
        """
        log.info("Retrieve node <%s> by bfs, `ascend` is :%s",
                 node_name, ascend)
        reply = {}
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        graph_name = graph_stream.validate_graph_name(graph_name)
        next_node_name = graph_stream.get_node_by_bfs_order(node_name, ascend)
        # no next node
        if next_node_name is None:
            return reply
        # add graph and tensor history for next node
        filter_condition = {
            'name': next_node_name,
            'graph_name': graph_name,
            'single_node': True
        }
        search_graph = self._get_nodes_info(filter_condition)
        reply = {'name': next_node_name}
        reply.update(search_graph)

        return reply

    def recheck(self):
        """
        Recheck all watchpoints.

        Returns:
            dict, metadata info.
        """
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        # validate backend status is able to recheck watchpoint
        if not metadata_stream.enable_recheck:
            log.error("Recheck is not available.")
            raise DebuggerRecheckError("Recheck is not available.")
        metadata_stream.state = ServerStatus.RUNNING.value
        metadata_stream.enable_recheck = False
        # send updated watchpoint and recheck command
        try:
            event = self._construct_run_event({'level': 'recheck'})
            self._send_watchpoints()
            self.cache_store.put_command(event)
        except MindInsightException as err:
            log.error("Failed to send recheck event.")
            log.exception(err)
            metadata_stream.state = ServerStatus.WAITING.value
            metadata_stream.enable_recheck = True
            raise DebuggerContinueError("Failed to send run command.")
        else:
            log.debug("Send the recheck to command queue.")
        return metadata_stream.get(['state', 'enable_recheck'])

    def retrieve_tensor_graph(self, tensor_name, graph_name):
        """
        Retrieve tensor graph.

        Args:
            tensor_name (str): The tensor name from UI.
            graph_name (str): The graph name.

        Returns:
            dict, tensor graph object.
        """
        log.info("Retrieve tensor graph for %s from %s", tensor_name, graph_name)
        tensor_graph_ops = TensorDetailInfo(self.cache_store).get_tensor_graph(tensor_name, graph_name)
        return tensor_graph_ops

    def retrieve_tensor_hits(self, tensor_name, graph_name):
        """
        Retrieve tensor hit information.

        Args:
            tensor_name (str): The tensor name from UI.
            graph_name (str): The graph name.

        Returns:
            dict, tensor hit info.
        """
        log.info("Retrieve tensor hits for %s from %s", tensor_name, graph_name)
        watch_points = TensorDetailInfo(self.cache_store).get_tensor_watch_points(tensor_name, graph_name)
        return {'watch_points': watch_points}

    def _hide_parameters_for_ui(self):
        """
        Hide some parameters on ui.

        Returns:
            dict, watch point list.
        """
        reply = self.cache_store.get_stream_handler(Streams.WATCHPOINT).get()
        watch_points = reply.get('watch_points')
        for i, watch_point in enumerate(watch_points):
            watch_condition = watch_point.get('watch_condition')
            parameters = watch_condition.get('params')
            watch_condition_id = watch_condition.get('id')
            mgr_condition = self.condition_mgr.get_condition(watch_condition_id)
            ui_watch_condition = []
            for param in parameters:
                parameter_definition = mgr_condition.get_parameter_definition(param['name'])
                if not parameter_definition.visible_on_ui:
                    continue
                ui_watch_condition.append(param)
            reply['watch_points'][i]['watch_condition']['params'] = ui_watch_condition
        return reply
