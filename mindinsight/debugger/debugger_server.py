# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
from functools import wraps
from threading import Thread

import grpc

from mindinsight.debugger.conditionmgr.condition import ConditionContext
from mindinsight.debugger.conditionmgr.conditionmgr import ConditionMgr
from mindinsight.debugger.conditionmgr.recommender import recommend_watchpoints
from mindinsight.conf import settings
from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.datavisual.utils.tools import to_float
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, \
    DebuggerParamTypeError, DebuggerCompareTensorError, DebuggerTensorGraphError, \
    DebuggerTensorHitError, DebuggerSetRecommendWatchpointsError, MindInsightException
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import ServerStatus, \
    create_view_event_from_tensor_basic_info, Streams
from mindinsight.debugger.debugger_cache import DebuggerCache
from mindinsight.debugger.debugger_grpc_server import DebuggerGrpcServer
from mindinsight.debugger.proto import debug_grpc_pb2_grpc as grpc_server_base
from mindinsight.debugger.stream_operator.tensor_detail_info import TensorDetailInfo
from mindinsight.debugger.stream_operator.training_control_operator import TrainingControlOperator
from mindinsight.debugger.stream_operator.watchpoint_operator import WatchpointOperator
from mindinsight.utils.tensor import TensorUtils, MAX_DIMENSIONS_FOR_TENSOR


def try_except(func):
    """Send latest metadata when catch exception."""

    @wraps(func)
    def send_latest_metadata(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except MindInsightException as err:
            metadata = self.cache_store.get_stream_handler(Streams.METADATA).get()
            self.cache_store.put_data(metadata)
            log.info("Put latest metadata into data-queue.")
            raise err

    return send_latest_metadata


class DebuggerServer:
    """The server manager of debugger."""

    def __init__(self):
        self.condition_mgr = ConditionMgr()
        self.cache_store = DebuggerCache()
        self.grpc_server = DebuggerGrpcServer(self.cache_store, self.condition_mgr)
        self.grpc_server_manager = None
        self.back_server = None

    def get_condition_collections(self, train_id):
        """Get default condition_collections"""
        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step)
        log.debug("Train_id: %s, backend: %s", train_id, condition_context.backend)
        return self.condition_mgr.get_all_collections(condition_context)

    def set_recommended_watch_points(self, set_recommended, train_id):
        """set recommended watch points."""
        if not isinstance(set_recommended, bool):
            log.error("Bool param should be given for set_recommended")
            raise DebuggerParamValueError("Bool param should be given.")

        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.recommendation_confirmed:
            log.error("User has confirmed setting recommended watchpoints")
            raise DebuggerSetRecommendWatchpointsError()

        metadata_stream.recommendation_confirmed = True
        condition_context = ConditionContext(metadata_stream.backend, metadata_stream.step)
        log.debug("Train_id: %s, backend: %s", train_id, condition_context.backend)
        res = metadata_stream.get(['state', 'enable_recheck'])
        if set_recommended:
            res['id'] = self._add_recommended_watchpoints(condition_context)

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
                name=watchpoint.name,
                condition_mgr=self.condition_mgr
            )
            watch_points_ids.append(watch_points_id)
        return watch_points_ids

    def start(self):
        """Start server."""
        grpc_port = settings.DEBUGGER_PORT if hasattr(settings, 'DEBUGGER_PORT') else 50051
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
        self._add_tensor_value_for_tensor_history(tensor_history, node_name, graph_name)
        # add hit label for tensor history
        watchpoint_hit_stream = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        watchpoint_hit_stream.update_tensor_history(tensor_history)
        # add metadata
        metadata = self.cache_store.get_stream_handler(Streams.METADATA).get(['step'])
        tensor_history.update(metadata)
        return tensor_history

    def _add_tensor_value_for_tensor_history(self, tensor_history, node_name, graph_name):
        """
        Add tensor value for_tensor_history and send ViewCMD if tensor value missed.

        Args:
            tensor_history (list[dict]): A list of tensor info, including name and type.
            node_name (str): The UI node name.
            graph_name (str): The graph name. Default: None.

        Returns:
            dict, the tensor info.
        """
        tensor_stream = self.cache_store.get_stream_handler(Streams.TENSOR)
        missed_tensors = tensor_stream.update_tensor_history(tensor_history)
        if missed_tensors:
            view_cmd = create_view_event_from_tensor_basic_info(missed_tensors)
            self.cache_store.put_command({'view_cmd': view_cmd, 'node_name': node_name, 'graph_name': graph_name})
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

    def search_watchpoint_hits(self, group_condition):
        """
        Retrieve watchpoint hit.

        Args:
            group_condition (dict): Filter condition.

                - limit (int): The limit of each page.
                - offset (int): The offset of current page.
                - node_name (str): The retrieved node name.
                - graph_name (str): The retrieved graph name.

        Returns:
            dict, watch point list or relative graph.
        """
        if not isinstance(group_condition, dict):
            log.error("Group condition for watchpoint-hits request should be a dict")
            raise DebuggerParamTypeError("Group condition for watchpoint-hits request should be a dict")

        metadata_stream = self.cache_store.get_stream_handler(Streams.METADATA)
        if metadata_stream.state == ServerStatus.PENDING.value:
            log.info("The backend is in pending status.")
            return metadata_stream.get()

        reply = self.cache_store.get_stream_handler(Streams.WATCHPOINT_HIT).group_by(group_condition)
        reply['outdated'] = self.cache_store.get_stream_handler(Streams.WATCHPOINT).is_recheckable()
        return reply

    def create_watchpoint(self, params):
        """
        Create watchpoint.

        Args:
            params (dict): Params for create watchpoint.

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
        watchpoint_opt = WatchpointOperator(self.cache_store, self.condition_mgr)
        return watchpoint_opt.create_watchpoint(params)

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
        watchpoint_opt = WatchpointOperator(self.cache_store, self.condition_mgr)
        return watchpoint_opt.update_watchpoint(params)

    def delete_watchpoint(self, watch_point_id=None):
        """
        Delete watchpoint.

        Args:
            watch_point_id (Union[None, int]): The id of watchpoint.
                If None, delete all watchpoints. Default: None.

        Returns:
            dict, the metadata info.
        """
        watchpoint_opt = WatchpointOperator(self.cache_store, self.condition_mgr)
        return watchpoint_opt.delete_watchpoint(watch_point_id=watch_point_id)

    @try_except
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
        mode = params.pop('mode', None) if params else None
        training_controller = TrainingControlOperator(self.cache_store)
        training_controller.validate_mode(mode)
        return training_controller.control(mode, params)

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

    @try_except
    def recheck(self):
        """
        Recheck all watchpoints.

        Returns:
            dict, metadata info.
        """
        return TrainingControlOperator(self.cache_store).recheck()

    def retrieve_tensor_graph(self, tensor_name, graph_name):
        """
        Retrieve tensor graph.

        Args:
            tensor_name (str): The tensor name from UI.
            graph_name (str): The graph name.

        Returns:
            dict, tensor graph object.
        """
        if self.cache_store.get_stream_handler(Streams.METADATA).state != ServerStatus.WAITING.value:
            log.error("Failed to get tensor graph the MindSpore is not in waiting state.")
            raise DebuggerTensorGraphError
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
        if self.cache_store.get_stream_handler(Streams.METADATA).state != ServerStatus.WAITING.value:
            log.error("Failed to get tensor hits as the MindSpore is not in waiting state.")
            raise DebuggerTensorHitError
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
