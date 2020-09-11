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
"""Implement the debugger grpc server."""
from functools import wraps

from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.common.utils import get_ack_reply, ServerStatus, \
    create_view_event_from_tensor_history, Streams
from mindinsight.debugger.proto import debug_grpc_pb2_grpc as grpc_server_base
from mindinsight.debugger.proto.ms_graph_pb2 import GraphProto


def debugger_wrap(func):
    """Wrapper for catch exception."""

    @wraps(func)
    def record_log(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            log.exception(err)
            raise err

    return record_log


class DebuggerGrpcServer(grpc_server_base.EventListenerServicer):
    """The grpc server used to interactive with grpc client."""

    def __init__(self, cache_store):
        """
        Initialize.

        Args:
            cache_store (DebuggerCache): Debugger cache store.
        """
        cache_store.initialize()
        self._cache_store = cache_store
        self._pos = None
        self._status = None
        self._view_event = None
        self._view_round = None
        self._continue_steps = None
        self.init()

    def init(self):
        """Init debugger grpc server."""
        self._pos = '0'
        self._status = ServerStatus.PENDING
        self._view_event = None
        self._view_round = True
        self._continue_steps = 0
        self._cache_store.clean()

    @debugger_wrap
    def WaitCMD(self, request, context):
        """Wait for a command in DebuggerCache."""
        # check if graph have already received.
        log.info("Received WaitCMD at %s-th step.", request.cur_step)
        if self._status == ServerStatus.PENDING:
            log.warning("No graph received before WaitCMD.")
            reply = get_ack_reply(1)
            return reply
        # send graph if has not been sent before
        self._pre_process(request)
        # deal with old command
        reply = self._deal_with_old_command()
        if reply:
            log.info("Reply to WaitCMD with old command: %s", reply)
            return reply
        # send view cmd
        if self._view_round and self._view_event:
            self._view_round = False
            reply = self._view_event
            log.debug("Send ViewCMD.")
        # continue multiple steps training
        elif self._continue_steps != 0:
            reply = get_ack_reply()
            reply.run_cmd.run_steps = 1
            reply.run_cmd.run_level = 'step'
            self._continue_steps = self._continue_steps - 1 if self._continue_steps > 0 else -1
            self._cache_store.get_stream_handler(Streams.WATCHPOINT_HIT).clean()
            log.debug("Send RunCMD. Clean watchpoint hit.")
        # wait for command
        else:
            reply = self._wait_for_next_command()

        if reply is None:
            reply = get_ack_reply(1)
            log.warning("Failed to get command event.")
        else:
            log.info("Reply to WaitCMD: %s", reply)
        return reply

    def _pre_process(self, request):
        """Send graph and metadata when WaitCMD first called."""
        metadata_stream = self._cache_store.get_stream_handler(Streams.METADATA)
        if self._status == ServerStatus.RECEIVE_GRAPH:
            self._status = ServerStatus.WAITING
            metadata_stream.state = 'waiting'
            metadata = metadata_stream.get()
            self._cache_store.clean_command()
            res = self._cache_store.get_stream_handler(Streams.GRAPH).get()
            res.update(metadata)
            self._cache_store.put_data(res)
            log.info("Put graph into data queue.")

        if metadata_stream.step < request.cur_step or metadata_stream.full_name != request.cur_node:
            # clean tensor cache and DataQueue at the beginning of each step
            self._update_metadata(metadata_stream, request)

    def _update_metadata(self, metadata_stream, metadata_proto):
        """Update metadata."""
        # reset view round and clean cache data
        self._view_round = True
        if metadata_stream.step < metadata_proto.cur_step:
            self._cache_store.clean_data()
            self._cache_store.get_stream_handler(Streams.TENSOR).clean_tensors(
                metadata_proto.cur_step)
        # put new metadata into cache
        metadata_stream.put(metadata_proto)
        cur_node = self._cache_store.get_stream_handler(Streams.GRAPH).get_node_name_by_full_name(
            metadata_proto.cur_node) if metadata_proto.cur_node else ''
        metadata_stream.node_name = cur_node
        metadata = metadata_stream.get()
        self._cache_store.put_data(metadata)
        log.info("Put new metadata into data queue.")

    def _deal_with_old_command(self):
        """Deal with old command."""
        event = None
        while self._cache_store.has_command(self._pos) and event is None:
            event = self._get_next_command()
            log.debug("Deal with old %s-th command:\n%s.", self._pos, event)

        return event

    def _wait_for_next_command(self):
        """
        Wait for next command.

        Returns:
            EventReply, the command event.
        """
        log.info("Start to wait for command.")
        self._cache_store.get_stream_handler(Streams.METADATA).state = 'waiting'
        self._cache_store.put_data({'metadata': {'state': 'waiting'}})
        event = None
        while event is None and self._status == ServerStatus.WAITING:
            log.debug("Wait for %s-th command", self._pos)
            event = self._get_next_command()
        return event

    def _get_next_command(self):
        """Get next command."""
        self._pos, event = self._cache_store.get_command(self._pos)
        log.debug("Received event :%s", event)
        if event is None:
            return event
        if isinstance(event, dict) and event.get('reset'):
            self._set_view_event(event)
            event = None
        elif event.HasField('run_cmd'):
            event = self._deal_with_run_cmd(event)
        elif event.HasField('view_cmd'):
            self._view_round = False
        elif event.HasField('exit'):
            self._cache_store.clean()
            log.info("Clean cache for exit cmd.")

        return event

    def _deal_with_run_cmd(self, event):
        """Deal with run cmd."""
        run_cmd = event.run_cmd
        # receive step command
        if run_cmd.run_level == 'step':
            # receive pause cmd
            if run_cmd.run_steps == 0:
                log.debug("Pause training and wait for next command.")
                self._continue_steps = 0
                return None
            # receive step cmd
            self._continue_steps = run_cmd.run_steps - 1
            event.run_cmd.run_steps = 1
        self._cache_store.get_stream_handler(Streams.WATCHPOINT_HIT).clean()
        log.debug("Receive RunCMD. Clean watchpoint hit cache.")

        return event

    def _set_view_event(self, event):
        """Create view event for view cmd."""
        # the first tensor in view cmd is always the output
        node_name = event.get('node_name')
        tensor_history = event.get('tensor_history')
        if not node_name or not tensor_history:
            self._view_event = None
            log.info("Reset view command to None.")
        else:
            # create view event and set
            self._view_event = create_view_event_from_tensor_history(tensor_history)
            log.info("Reset view command to %s.", node_name)

    @debugger_wrap
    def SendMetadata(self, request, context):
        """Send metadata into DebuggerCache."""
        log.info("Received Metadata.")
        if self._status != ServerStatus.PENDING:
            log.info("Re-initialize cache store when new session comes.")
            self.init()

        client_ip = context.peer().split(':', 1)[-1]
        metadata_stream = self._cache_store.get_stream_handler(Streams.METADATA)
        metadata_stream.put(request)
        metadata_stream.client_ip = client_ip
        metadata = metadata_stream.get()
        # put metadata into data queue
        self._cache_store.put_data(metadata)
        log.info("Put new metadata to DataQueue.")
        reply = get_ack_reply()
        log.info("Send the reply to %s.", client_ip)
        return reply

    @debugger_wrap
    def SendGraph(self, request_iterator, context):
        """Send graph into DebuggerCache."""
        log.info("Received graph.")
        serial_graph = b""
        for chunk in request_iterator:
            serial_graph += chunk.buffer
        graph = GraphProto.FromString(serial_graph)
        log.debug("Deserialize the graph. Receive %s nodes", len(graph.node))
        self._cache_store.get_stream_handler(Streams.GRAPH).put(graph)
        self._cache_store.get_stream_handler(Streams.TENSOR).put_const_vals(graph.const_vals)
        self._status = ServerStatus.RECEIVE_GRAPH
        reply = get_ack_reply()
        log.info("Send the reply for graph.")
        return reply

    @debugger_wrap
    def SendTensors(self, request_iterator, context):
        """Send tensors into DebuggerCache."""
        log.info("Received tensor.")
        tensor_construct = []
        tensor_stream = self._cache_store.get_stream_handler(Streams.TENSOR)
        metadata_stream = self._cache_store.get_stream_handler(Streams.METADATA)
        tensor_names = []
        step = metadata_stream.step
        for tensor in request_iterator:
            tensor_construct.append(tensor)
            if tensor.finished:
                tensor_stream.put({'step': step, 'tensor_protos': tensor_construct})
                tensor_construct = []
                tensor_names.append(':'.join([tensor.node_name, tensor.slot]))
                continue
        # send back tensor finished flag when all waiting tensor has value.
        tensor_history = tensor_stream.get_tensor_history(tensor_names)
        self._add_node_name_for_tensor_history(tensor_history)
        metadata = metadata_stream.get()
        tensor_history.update(metadata)
        self._cache_store.put_data({})  # reply to the listening request
        self._cache_store.put_data(tensor_history)
        log.info("Send updated tensor history to data queue.")
        reply = get_ack_reply()
        return reply

    def _add_node_name_for_tensor_history(self, tensor_history):
        """Add node name for tensor history."""
        graph_stream = self._cache_store.get_stream_handler(Streams.GRAPH)
        for tensor_info in tensor_history.get('tensor_history'):
            if tensor_info:
                full_name, slot = tensor_info.get('full_name', '').rsplit(':', 1)
                node_name = graph_stream.get_node_name_by_full_name(full_name)
                tensor_info['name'] = node_name + ':' + slot

    @debugger_wrap
    def SendWatchpointHits(self, request_iterator, context):
        """Send watchpoint hits info DebuggerCache."""
        log.info("Received WatchpointHits. Left steps %d change to 0.", self._continue_steps)
        self._continue_steps = 0
        self._view_event = None
        watchpoint_hit_stream = self._cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        watchpoint_stream = self._cache_store.get_stream_handler(Streams.WATCHPOINT)
        graph_stream = self._cache_store.get_stream_handler(Streams.GRAPH)
        for watchpoint_hit_proto in request_iterator:
            watchpoint_hit = {
                'tensor_proto': watchpoint_hit_proto.tensor,
                'watchpoint': watchpoint_stream.get_watchpoint_by_id(watchpoint_hit_proto.id),
                'node_name': graph_stream.get_node_name_by_full_name(
                    watchpoint_hit_proto.tensor.node_name)
            }
            watchpoint_hit_stream.put(watchpoint_hit)
        watchpoint_hits_info = watchpoint_hit_stream.get()
        self._cache_store.put_data(watchpoint_hits_info)
        log.info("Send the watchpoint hits to DataQueue.\nSend the reply.")
        reply = get_ack_reply()
        return reply
