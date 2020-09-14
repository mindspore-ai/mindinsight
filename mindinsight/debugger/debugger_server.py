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

from mindinsight.conf import settings
from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.datavisual.utils.tools import to_float
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError, DebuggerCreateWatchPointError, DebuggerUpdateWatchPointError, \
    DebuggerDeleteWatchPointError, DebuggerContinueError, DebuggerPauseError, DebuggerCompareTensorError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.common.utils import get_ack_reply, ServerStatus, \
    create_view_event_from_tensor_history, Streams, is_scope_type, NodeBasicInfo, \
    str_to_slice_or_int
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_grpc_server import DebuggerGrpcServer
from mindinsight.debugger.proto import debug_grpc_pb2_grpc as grpc_server_base
from mindinsight.debugger.proto.debug_grpc_pb2 import RunCMD
from mindinsight.utils.exceptions import MindInsightException


class DebuggerServer:
    """The server manager of debugger."""

    def __init__(self, grpc_port=None):
        self.grpc_port = grpc_port
        self.cache_store = DebuggerCache()
        self.grpc_server = DebuggerGrpcServer(self.cache_store)
        self.grpc_server_manager = None
        self.back_server = None
        self._watch_point_id = 0

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

    def search(self, name, watch_point_id):
        """Search for single node in graph."""
        log.info("receive search request for node:%s, in watchpoint:%d", name, watch_point_id)
        graph = self.cache_store.get_stream_handler(Streams.GRAPH).search_nodes(name)
        self.cache_store.get_stream_handler(Streams.WATCHPOINT).set_watch_nodes(
            graph, watch_point_id)
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
        parsed_shape = self.parse_shape(shape)
        node_type, tensor_name = self._get_tensor_name_and_type_by_ui_name(name)
        tolerance = to_float(tolerance, 'tolerance')
        tensor_stream = self.cache_store.get_stream_handler(Streams.TENSOR)
        if detail == 'data':
            if node_type == NodeTypeEnum.PARAMETER.value:
                reply = tensor_stream.get_tensors_diff(tensor_name, parsed_shape, tolerance)
            else:
                raise DebuggerParamValueError("The node type must be parameter, but got {}.".format(node_type))
        else:
            raise DebuggerParamValueError("The value of detail: {} is not support.".format(detail))
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
        # validate watchpoint_id

        mode_mapping = {
            'all': self._retrieve_all,
            'node': self._retrieve_node,
            'watchpoint': self._retrieve_watchpoint,
            'watchpoint_hit': self._retrieve_watchpoint_hit
        }
        # validate param <mode>
        if mode not in mode_mapping.keys():
            log.error("Invalid param <mode>. <mode> should be in ['all', 'node', 'watchpoint', "
                      "'watchpoint_hit', 'tensor'], but got %s.", mode_mapping)
            raise DebuggerParamTypeError("Invalid mode.")
        filter_condition = {} if filter_condition is None else filter_condition
        reply = mode_mapping[mode](filter_condition)

        return reply

    def _retrieve_all(self, filter_condition=None):
        """Retrieve metadata, root graph and watchpoint list."""
        if filter_condition:
            log.error("No filter condition required for retrieve all request.")
            raise DebuggerParamTypeError("filter_condition should be empty.")
        result = {}
        self._watch_point_id = 0
        self.cache_store.clean_data()
        log.info("Clean data queue cache when retrieve all request.")
        for stream in [Streams.METADATA, Streams.GRAPH, Streams.WATCHPOINT]:
            sub_res = self.cache_store.get_stream_handler(stream).get()
            result.update(sub_res)

        return result

    def _retrieve_node(self, filter_condition):
        """
        Retrieve node info.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The name of single node.

                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.

        Returns:
            dict, the node info.
        """
        log.info("Retrieve node %s.", filter_condition)
        node_name = filter_condition.get('name')
        if node_name:
            # validate node name
            self.cache_store.get_stream_handler(Streams.GRAPH).get_node_type(node_name)
        filter_condition['single_node'] = bool(filter_condition.get('single_node'))
        reply = self._get_nodes_info(filter_condition)
        return reply

    def _get_nodes_info(self, filter_condition):
        """
        Get nodes info.

        Args:
            filter_condition (dict): The filter condition.

                - name (str): The node name.

                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.

        Returns:
            dict, reply with graph.
        """
        # get graph
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        reply = graph_stream.get(filter_condition)
        graph = reply.get('graph')
        # add watched label
        self.cache_store.get_stream_handler(Streams.WATCHPOINT).set_watch_nodes(
            graph, self._watch_point_id)
        return reply

    def retrieve_tensor_history(self, node_name):
        """
        Retrieve tensor history for leaf node.

        Args:
            node_name (str): The name of leaf node.

        Returns:
            dict, the tensor history and metadata.
        """
        log.info("Retrieve tensor history for node: %s.", node_name)
        self._validate_leaf_name(node_name)
        res = self._get_tensor_history(node_name)
        return res

    def _validate_leaf_name(self, node_name):
        """Validate if the node is a leaf node."""
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        node_type = graph_stream.get_node_type(node_name)
        if is_scope_type(node_type):
            log.error("Scope type node has no tensor history.")
            raise DebuggerParamValueError("Invalid leaf node name.")

    def _get_tensor_history(self, node_name):
        """
        Get tensor history for single node.

        Args:
            node_name (str): The name of leaf node.

        Returns:
            dict, the tensor history and metadata.
        """
        # get basic tensor history
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        tensor_history = graph_stream.get_tensor_history(node_name)
        # add tensor value for tensor history
        self._add_tensor_value_for_tensor_history(tensor_history, node_name)
        # add hit label for tensor history
        watchpoint_hit_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        watchpoint_hit_stream.update_tensor_history(tensor_history)
        # add metadata
        metadata = self.cache_store.get_stream_handler(Streams.METADATA).get()
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

    def retrieve_tensor_value(self, name, detail, shape):
        """Retrieve the tensor value."""
        log.info("Retrieve tensor value: name: %s, detail: %s, shape: %s", name, detail, shape)
        self.validate_tensor_param(name, detail)
        parsed_shape = self.parse_shape(shape)
        node_type, tensor_name = self._get_tensor_name_and_type_by_ui_name(name)
        reply = self.cache_store.get_stream_handler(Streams.TENSOR).get(
            {'name': tensor_name,
             'node_type': node_type,
             'shape': parsed_shape}
        )
        reply['tensor_value']['name'] = name

        return reply

    def _get_tensor_name_and_type_by_ui_name(self, name):
        """
        Get inner tensor name and type by UI name.

        Args:
            name (str): Node name shown in UI.

        Returns:
            str, full name of tensor.
            str, node type of tensor.
        """
        node_name, slot = name.rsplit(':', 1)
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        node_type = graph_stream.get_node_type(node_name)
        full_name = graph_stream.get_full_name(node_name)
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

    @staticmethod
    def parse_shape(shape):
        """Parse shape."""
        if shape is None:
            return shape
        if not (isinstance(shape, str) and shape.startswith('[') and shape.endswith(']')):
            log.error("Invalid shape. Received: %s", shape)
            raise DebuggerParamValueError("Invalid shape.")
        shape = shape.strip('[]')
        if shape.count(':') > 2:
            log.error("Invalid shape. At most two dimensions are specified.")
            raise DebuggerParamValueError("Invalid shape.")
        parsed_shape = tuple(
            str_to_slice_or_int(dim) for dim in shape.split(',')) if shape else tuple()
        log.info("Parsed shape: %s from %s", parsed_shape, shape)
        return parsed_shape

    def _retrieve_watchpoint(self, filter_condition):
        """
        Retrieve watchpoint.

        Args:
            filter_condition (dict): Filter condition.

                - watch_point_id (int):  The id of watchoint. If not given, return all watchpoints.

                - name (str): The name of single node.

                - single_node (bool): If False, return the sub-layer of single node. If True, return
                    the node list from root node to single node.

        Returns:
            dict, watch point list or relative graph.
        """
        watchpoint_id = filter_condition.get('watch_point_id')
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watchpoint_stream.validate_watchpoint_id(watchpoint_id)
        self._watch_point_id = watchpoint_id if watchpoint_id else 0
        if not watchpoint_id:
            reply = self.cache_store.get_stream_handler(Streams.WATCHPOINT).get()
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
        # get watchpoint hit list
        if node_name is None:
            reply = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT).get()
            return reply

        self._validate_leaf_name(node_name)
        # get tensor history
        reply = self._get_tensor_history(node_name)
        log.debug("Get tensor history for watchpoint hit node.")
        # get single graph
        if filter_condition.get('single_node'):
            graph = self._get_nodes_info(filter_condition)
            reply.update(graph)
        log.debug("Get tensor history for watchpoint hit node.")

        return reply

    def create_watchpoint(self, watch_condition, watch_nodes=None, watch_point_id=None):
        """
        Create watchpoint.

        Args:
            watch_condition (dict): The watch condition.

                - condition (str): Accept `INF` or `NAN`.

                - param (list[float]): Not defined yet.
            watch_nodes (list[str]): The list of node names.
            watch_point_id (int): The id of watchpoint.

        Returns:
            dict, the id of new watchpoint.
        """
        log.info("Received create watchpoint request. WatchCondition: %s", watch_condition)
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("Failed to create watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerCreateWatchPointError(
                "Failed to create watchpoint as the MindSpore is not in waiting state.")
        if metadata_stream.backend == 'GPU' and watch_condition.get('condition') == 'OVERFLOW':
            log.error("GPU doesn't support OVERFLOW watch condition.")
            raise DebuggerParamValueError("GPU doesn't support OVERFLOW watch condition.")

        watch_nodes = self._get_node_basic_infos(watch_nodes)
        watch_point_id = self.cache_store.get_stream_handler(Streams.WATCHPOINT).create_watchpoint(
            watch_condition, watch_nodes, watch_point_id)
        self._watch_point_id = 0
        log.info("Create watchpoint %d", watch_point_id)
        return {'id': watch_point_id}

    def update_watchpoint(self, watch_point_id, watch_nodes, mode, name=None):
        """
        Update watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.
            watch_nodes (list[str]): The list of node names.
            mode (int): The update operator on nodes. 0 for remove nodes from watch nodes.
                1 for add nodes to watch nodes.
            name (str): The search name. Default: None.

        Returns:
            dict, empty response.
        """
        if self.cache_store.get_stream_handler(
                Streams.METADATA).state != ServerStatus.WAITING.value:
            log.error("Failed to update watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerUpdateWatchPointError(
                "Failed to update watchpoint as the MindSpore is not in waiting state."
            )
        # validate
        if not watch_nodes or not watch_point_id:
            log.error("Invalid parameter for update watchpoint.")
            raise DebuggerParamValueError("Invalid parameter for update watchpoint.")
        # update watch node
        if name is not None:
            watch_nodes = self._get_watch_nodes_by_search(watch_nodes)
        elif mode == 1:
            watch_nodes = self._get_node_basic_infos(watch_nodes)

        self.cache_store.get_stream_handler(Streams.WATCHPOINT).update_watchpoint(
            watch_point_id, watch_nodes, mode)
        self._watch_point_id = watch_point_id
        log.info("Update watchpoint with id: %d", watch_point_id)
        return {}

    def _get_watch_nodes_by_search(self, watch_nodes):
        """Get watched leaf nodes by search name."""
        watched_leaf_nodes = []
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        for search_name in watch_nodes:
            search_nodes = graph_stream.get_searched_node_list()
            search_node_names = [
                NodeBasicInfo(name=node.name, full_name=node.full_name, type=node.type)
                for node in search_nodes
                if node.name.startswith(search_name)]
            watched_leaf_nodes.extend(search_node_names)

        log.debug("Update nodes: %s", watched_leaf_nodes)

        return watched_leaf_nodes

    def delete_watchpoint(self, watch_point_id):
        """
        Delete watchpoint.

        Args:
            watch_point_id (int): The id of watchpoint.

        Returns:
            dict, empty response.
        """
        if self.cache_store.get_stream_handler(
                Streams.METADATA).state != ServerStatus.WAITING.value:
            log.error("Failed to delete watchpoint as the MindSpore is not in waiting state.")
            raise DebuggerDeleteWatchPointError(
                "Failed to delete watchpoint as the MindSpore is not in waiting state."
            )
        self.cache_store.get_stream_handler(Streams.WATCHPOINT).delete_watchpoint(
            watch_point_id)
        self._watch_point_id = 0
        log.info("Delete watchpoint with id: %d", watch_point_id)
        return {}

    def _get_node_basic_infos(self, node_names):
        """Get node info according to node names."""
        if not node_names:
            return []
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        node_infos = []
        for node_name in node_names:
            node_type = graph_stream.get_node_type(node_name)
            # optimizer later
            if node_type == NodeTypeEnum.AGGREGATION_SCOPE.value:
                sub_nodes = graph_stream.get_nodes(node_name)
                sub_infos = [NodeBasicInfo(name=node.name, full_name=node.full_name, type=node.type)
                             for node in sub_nodes]
                node_infos.extend(sub_infos)
                continue
            full_name = graph_stream.get_full_name(node_name)
            node_infos.append(NodeBasicInfo(name=node_name, full_name=full_name, type=node_type))
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
        """
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("MindSpore is not ready to run. Current state is: %s", metadata_stream.state)
            raise DebuggerContinueError(
                "MindSpore is not ready to run or is running currently."
            )
        metadata_stream.state = ServerStatus.RUNNING.value
        current_state = ServerStatus.RUNNING.value
        try:
            event = self._construct_run_event(params)
            self._send_watchpoints()
            self.cache_store.put_command(event)
        except MindInsightException as err:
            log.error("Failed to send run event.")
            log.exception(err)
            current_state = ServerStatus.WAITING.value
            metadata_stream.state = current_state
            raise DebuggerContinueError("Failed to send run command.")
        else:
            log.debug("Send the RunCMD to command queue.")

        return {'metadata': {'state': current_state}}

    def _validate_node_type(self, node_name):
        """Check the node type in node control."""
        if not node_name:
            return
        node_type = self.cache_store.get_stream_handler(Streams.GRAPH).get_node_type(node_name)
        unsupported_types = [item.value for item in list(NodeTypeEnum)]
        if node_type in unsupported_types:
            log.error("Invalid node type. %s", node_name)
            raise DebuggerParamValueError(f"The type of node {node_name} is unsupported for "
                                          "continue to command.")

    def _construct_run_event(self, params):
        """
        Construct run cmd from input control params.

        Args:
            params (dict): The control params.

                - level (str): The control granularity, `node` level or `step` level.
                    Default: `step`.

                - steps (int): Specify the steps that training should run.
                    Used when `level` is `step`.

                - full_name (str): Specify the name of the node. Used when `level` is `node`.

        Returns:
            EventReply, control event with run command.
        """
        level = params.get('level', 'step')
        event = get_ack_reply()
        if level == 'step':
            steps = params.get('steps')
            if not steps:
                steps = 1
            run_cmd = RunCMD(run_level='step', run_steps=steps)
        elif level == 'node':
            self._validate_node_type(params.get('name'))
            name = self.cache_store.get_stream_handler(Streams.GRAPH).get_full_name(
                params['name'])
            if not name:
                name = ''
            run_cmd = RunCMD(run_level='node', node_name=name)
        else:
            log.error("Invalid Value. `level` should be `step` or `node`. Got %s", level)
            raise DebuggerParamValueError("level` should be `step` or `node`")

        event.run_cmd.CopyFrom(run_cmd)
        log.debug("Construct run event. %s", event)
        return event

    def _send_watchpoints(self):
        """Set watchpoints."""
        watchpoint_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT)
        watchpoints = watchpoint_stream.get(filter_condition=True).get('watch_points')
        if watchpoints:
            for watchpoint in watchpoints:
                event = get_ack_reply()
                event.set_cmd.CopyFrom(watchpoint)
                self.cache_store.put_command(event)
            watchpoint_stream.sync_set_cmd()
            log.debug("Send SetCMD to MindSpore. %s", event)

    def _pause(self, metadata_stream):
        """
        Pause the training.

        Args:
            metadata_stream (MetadataHandler): The metadata stream handler.
        """
        if metadata_stream.state != ServerStatus.RUNNING.value:
            log.error("The MindSpore is not running.")
            raise DebuggerPauseError("The MindSpore is not running.")
        metadata_stream.state = 'waiting'
        event = get_ack_reply()
        event.run_cmd.CopyFrom(RunCMD(run_level='step', run_steps=0))
        self.cache_store.put_command(event)
        log.debug("Send the Pause command")
        return {'metadata': {'state': 'waiting'}}

    def _terminate(self, metadata_stream):
        """
        Terminate the training.

        Args:
            metadata_stream (MetadataHandler): The metadata stream handler.
        """
        metadata_stream.state = 'pending'
        event = get_ack_reply()
        event.exit = True
        self.cache_store.put_command(event)
        log.debug("Send the ExitCMD.")
        return {'metadata': {'state': 'pending'}}

    def retrieve_node_by_bfs(self, node_name, ascend=False):
        """Get the graph and tensor history of the next node name according to node_name."""
        log.info("Retrieve node <%s> by bfs, `ascend` is :%s",
                 node_name, ascend)
        reply = {}
        graph_stream = self.cache_store.get_stream_handler(Streams.GRAPH)
        next_node_name = graph_stream.get_node_by_bfs_order(node_name, ascend)
        # no next node
        if next_node_name is None:
            return reply
        # add graph and tensor history for next node
        filter_condition = {
            'name': next_node_name,
            'single_node': True
        }
        search_graph = self._get_nodes_info(filter_condition)
        tensor_history = self._get_tensor_history(next_node_name)
        reply = {'name': next_node_name}
        reply.update(search_graph)
        reply.update(tensor_history)

        return reply
