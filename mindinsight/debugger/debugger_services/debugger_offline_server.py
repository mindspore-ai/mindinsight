# Copyright 2021 Huawei Technologies Co., Ltd
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
"""Debugger Offline server."""
import copy
from collections import defaultdict
from importlib import import_module
from multiprocessing import Process, Manager
from threading import Event

import mindinsight
from mindinsight.debugger.common.exceptions.exceptions import DebuggerModuleNotFoundError, DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import Streams, ServerStatus, version_match, DebuggerServerMode, get_ack_reply, \
    RunLevel, MAX_SINGLE_TENSOR_CACHE, load_tensor
from mindinsight.debugger.conditionmgr.condition import ParamNameEnum
from mindinsight.debugger.debugger_services.debugger_server_base import DebuggerServerBase, debugger_server_wrap
from mindinsight.debugger.proto.debug_grpc_pb2 import EventReply
from mindinsight.debugger.stream_cache.data_loader import DataLoader
from mindinsight.domain.graph.proto.ms_graph_pb2 import TensorProto
from mindinsight.utils.exceptions import MindInsightException


class DebuggerOfflineServer(DebuggerServerBase):
    """Debugger Offline Server."""
    _MAX_TRY_EXCEPT_COUNT = 500

    def __init__(self, cache_store, context):
        super(DebuggerOfflineServer, self).__init__(cache_store, context)
        self._offline_server_manager = DebuggerOfflineManager(cache_store, context.dbg_dir)
        self._running = Event()
        self._running.clear()

    def run(self):
        """Start the debugger offline server."""
        log.info("Initialize Offline Debugger Server for dbg_dir: %s", self._context.dbg_dir)
        self._offline_server_manager.initialize()
        log.info("Start Offline Debugger Server for dbg_dir: %s", self._context.dbg_dir)
        self._running.set()
        try_count = 0
        while self._running.is_set() and try_count < self._MAX_TRY_EXCEPT_COUNT:
            try:
                self._offline_server_manager.wait_for_termination()
                if not self._offline_server_manager.is_runnable():
                    break
            except MindInsightException as err:
                log.exception(err)
                log.warning("Error happens during listening on user commands. Restart listening again.")
            finally:
                try_count += 1
        # protect server from too much failure commands.
        if try_count == self._MAX_TRY_EXCEPT_COUNT:
            self._cache_store.clean()
            metadata = self._cache_store.get_stream_handler(Streams.METADATA).get()
            self._cache_store.put_data(metadata)
            log.warning("Exception exceed %d times, stop server.", try_count)

    def stop(self):
        """Stop offline debugger server."""
        if not self.is_alive():
            log.info("Offline debugger has already stop")
            return
        log.debug("Start to wait for thread started.")
        self._running.wait()
        log.info("Start to stop offline debugger server.")
        self._running.clear()
        self._offline_server_manager.stop()
        self.join()


class DebuggerOfflineManager:
    """Debugger offline manager which is used to handle user commands."""

    def __init__(self, cache_store, dbg_dir):
        cache_store.initialize()
        self._cache_store = cache_store
        self._metadata_stream = cache_store.get_stream_handler(Streams.METADATA)

        self._dbg_dir = dbg_dir
        self._dbg_services_module = self._get_dbg_service_module()
        self._dbg_service = None

        self._command_listener = CommandListener(cache_store)
        self._data_loader = DataLoader(dbg_dir)
        self._is_running_flag = False
        self._old_run_cmd = {}

    def stop(self):
        """Stop server."""
        self._is_running_flag = False
        self._command_listener.stop()
        self._cache_store.clean()
        event = get_ack_reply()
        event.exit = True
        self._cache_store.put_command(event)
        log.info("Stop debugger offline manager.")

    def is_runnable(self):
        """Check if the offline manager is runnable."""
        state = self._metadata_stream.state
        flag = self._is_running_flag and state not in [ServerStatus.MISMATCH.value, ServerStatus.PENDING.value]
        if not flag:
            log.debug("The offline manager is not runnable, is_running_flag: %s, metadata state: %s",
                      self._is_running_flag, state)
        return flag

    @staticmethod
    def _get_dbg_service_module():
        """Get dbg service module from MindSpore."""
        try:
            dbg_services_module = import_module('mindspore.offline_debug.dbg_services')
        except (ModuleNotFoundError, ImportError) as err:
            log.error("Failed to find module dbg_services. %s", err)
            raise DebuggerModuleNotFoundError("dbg_services")
        return dbg_services_module

    @debugger_server_wrap
    def initialize(self):
        """Start to load offline debugger data."""
        is_sync = self._data_loader.get_sync_flag()
        net_name = self._data_loader.get_net_name()
        dump_dir = self._data_loader.get_dump_dir()
        self._dbg_service = self._dbg_services_module.DbgServices(dump_dir)
        self._dbg_service.initialize(net_name=net_name, is_sync_mode=is_sync)
        self._cache_store.clean()
        self._command_listener.start()
        self._is_running_flag = True
        self._check_version()
        if self._metadata_stream.state == ServerStatus.MISMATCH.value:
            log.info("The MindSpore and MindInsight version are mismatched. Failed to initialize offline server.")
            return
        self._load_metadata()
        self._load_graphs()
        log.info("Success initialize offline server for %s", self._dbg_dir)

    def _check_version(self):
        """Check version."""
        ms_version = self._dbg_services_module.get_version()
        mi_version = mindinsight.__version__
        self._metadata_stream.debugger_version = {'ms': ms_version, 'mi': mi_version}
        if version_match(ms_version, mi_version) is False:
            log.info("Version is mismatched, dbg_services is: %s, mindinsight is: %s",
                     ms_version, mi_version)
            self._metadata_stream.state = ServerStatus.MISMATCH.value
            metadata = self._metadata_stream.get(['state', 'debugger_version'])
            self._cache_store.put_data(metadata)

    def _load_metadata(self):
        """Load metadata."""
        self._metadata_stream.debugger_type = DebuggerServerMode.OFFLINE.value
        device_info = self._data_loader.load_device_info()
        # The backend referred to the running environment on which the offline debugger
        # data was generated.
        # Currently supported options: `GPU`, `Ascend`
        backend = device_info.get('device_target', 'Ascend')
        self._metadata_stream.backend = backend
        device_stream = self._cache_store.get_stream_handler(Streams.DEVICE)
        device_stream.put(device_info.get('server_list'))
        first_rank_info = device_stream.get()['devices'][0]
        self._metadata_stream.client_ip = first_rank_info.get('server_id')
        # get step number per device. dict(rank_id, step_num), may be increased with time goes by
        step_num_per_rank = self._data_loader.load_step_number()
        device_stream.add_step_num_info(step_num_per_rank)
        self._metadata_stream.max_step_num = max(step_num_per_rank.values()) if step_num_per_rank else 0

    def _load_graphs(self):
        """Load graphs."""
        # the format of graphs is a list of {'rank_id': int, 'graph_protos': [GraphProto]}}
        log.debug("Begin to load graphs.")
        graphs = self._data_loader.load_graphs()
        device_stream = self._cache_store.get_stream_handler(Streams.DEVICE)
        graph_per_rank = {}
        for graph in graphs:
            rank_id = graph.get('rank_id')
            graph_per_rank[rank_id] = {}
            tensor_stream_per_rank = self._cache_store.get_stream_handler(Streams.TENSOR). \
                get_tensor_handler_by_rank_id(rank_id, create_if_not_exit=True)
            for graph_proto in graph.get('graph_protos'):
                graph_per_rank[rank_id][graph_proto.name] = graph_proto
                tensor_stream_per_rank.put_const_vals(graph_proto.const_vals)
        # the graph_per_rank is format like: Dict[<rank_id>, Dict[<graph_name>, <GraphProto>]]
        try:
            self._cache_store.get_stream_handler(Streams.GRAPH).put(graph_per_rank)
            self._cache_store.get_stream_handler(Streams.GRAPH).parse_stack_infos()
            device_stream.add_graph_name_info(graph_per_rank)
        except DebuggerParamValueError:
            log.warning("Parse graph failed. The graph file is invalid.")
            self._cache_store.get_stream_handler(Streams.GRAPH).clean()
        self._metadata_stream.state = ServerStatus.RECEIVE_GRAPH.value
        log.debug("Finish to load graphs.")

    @debugger_server_wrap
    def wait_for_termination(self):
        """Begin to listen on command event."""
        log.info("Begin to listen for user commands.")
        self._send_graph()
        while self.is_runnable():
            if not self._command_listener.has_new_command() and self._old_run_cmd:
                self._deal_with_old_run_cmd()
                continue
            cmd = self._command_listener.get_next_command()
            self.deal_with_cmd(cmd)

    def _send_graph(self):
        """Put graph and metadata info into data queue."""
        if not self.is_runnable():
            return
        self._metadata_stream.state = ServerStatus.WAITING.value
        metadata = self._metadata_stream.get()
        res = self._cache_store.get_stream_handler(Streams.GRAPH).get()
        res.update(metadata)
        self._cache_store.put_data(res)

    def _deal_with_old_run_cmd(self):
        """Deal with old run command."""
        left_step_count = self._old_run_cmd.get('left_step_count')
        if left_step_count:
            self._execute_one_step()
            # if old_run_cmd is not cleared due to hit.
            if self._old_run_cmd:
                self._old_run_cmd['left_step_count'] = left_step_count - 1 if left_step_count > 0 else -1
        if not self._old_run_cmd.get('left_step_count'):
            self._old_run_cmd.clear()

    def deal_with_cmd(self, cmd):
        """Deal with command."""
        if cmd is None:
            return
        if isinstance(cmd, dict):
            self._deal_with_view_cmd(cmd)
        elif isinstance(cmd, EventReply):
            self._on_event(cmd)

    def _on_event(self, event):
        """
        Deal with different command event.

        Args:
            event (EventReply): Command Event.
        """
        if event.HasField('run_cmd'):
            self._deal_with_run_cmd(event)
        elif event.HasField('exit'):
            self._cache_store.clean()
            self._update_state(ServerStatus.PENDING)
            log.debug("Clean cache for exit cmd.")
        else:
            self._deal_with_set_cmd(event)
            log.debug("Deal with set cmd.")

    def _deal_with_view_cmd(self, event):
        """
        Deal with view cmd.

        Args:
            event (dict): View command params.

                - view_cmd (EventReply): EventReply with view command.
                - node_name (str): The center node name for view command.
                - tensor_name (str): The center tensor name for view command.
                - graph_name (str): The graph name of center node.
                - rank_id (int): The device id of the tensor.
        """
        view_cmd = event.pop('view_cmd', None).view_cmd
        node_info = event
        log.debug("Receive view cmd for node: %s.", event)
        if not (view_cmd and node_info):
            log.info("Invalid view command. Ignore it.")
            return
        # read tensor value by dbg_service
        rank_id = node_info.get('rank_id', 0)
        cur_step = self._metadata_stream.step
        # as DbgServices hasn't support -1 yet, put empty tensor value into cache.
        if cur_step <= 0:
            log.info("Offline debugger not support to read initial weights yet.")
            self._put_tensor_value_into_cache(cur_step, node_info, rank_id, view_cmd.tensors)
            return
        iteration_id = cur_step - 1
        root_graph_id = self.get_root_graph_id(rank_id=rank_id,
                                               graph_name=node_info.get('graph_name'),
                                               node_name=node_info.get('node_name'))
        tensor_protos = view_cmd.tensors
        tensor_infos = [
            self._dbg_services_module.TensorInfo(
                node_name=tensor_proto.node_name,
                slot=int(tensor_proto.slot),
                iteration=iteration_id - 1 if tensor_proto.iter == 'prev' else iteration_id,
                rank_id=rank_id,
                is_output=True,
                root_graph_id=root_graph_id
            ) for tensor_proto in tensor_protos]
        res = Manager().list()
        read_tensor_process = Process(target=self._read_tensor_work, args=(tensor_infos, res,))
        read_tensor_process.start()
        read_tensor_process.join()

        if len(tensor_protos) != len(res):
            log.error("Invalid view command. The result unmatched. %d/%d", len(tensor_protos), len(res))
        else:
            # put tensor into cache
            for tensor_proto, tensor_data in zip(tensor_protos, res):
                log.debug("Tensor name: %s:%s, tensor type: %s, tensor size: %s",
                          tensor_proto.node_name, tensor_proto.slot,
                          tensor_data.get('dtype'), tensor_data.get('data_size'))
                tensor_proto.tensor_content = tensor_data.get('data_ptr')
                tensor_proto.ClearField('dims')
                tensor_proto.dims.extend(tensor_data.get('shape'))
                tensor_proto.data_type = tensor_data.get('dtype')
        self._put_tensor_value_into_cache(cur_step, node_info, rank_id, tensor_protos)
        log.info("Put tensor value into cache.")

    def _read_tensor_work(self, tensor_infos, res):
        """The check WatchPoint function work in another process."""
        log.info("Start read tensor process.")
        tensor_data_res = self._dbg_service.read_tensors(tensor_infos)
        for tensor_data in tensor_data_res:
            tensor_data_dict = convert_tensor_data(tensor_data)
            res.append(tensor_data_dict)
        log.info("Reading tensor process is finished.")

    def get_root_graph_id(self, rank_id, graph_name, node_name=None):
        """Get root graph id."""
        graph_stream = self._cache_store.get_stream_handler(Streams.GRAPH).get_graph_handler_by_rank_id(rank_id)
        return graph_stream.get_root_graph_id(graph_name, node_name)

    def _put_tensor_value_into_cache(self, cur_step, node_info, rank_id, tensor_protos):
        """Put tensor value into tensor cache."""
        tensor_stream = self._cache_store.get_stream_handler(Streams.TENSOR). \
            get_tensor_handler_by_rank_id(rank_id)
        update_data_flag = False
        for tensor_proto in tensor_protos:
            if not tensor_proto.tensor_content:
                log.warning("Tensor %s:%s is empty.",
                            tensor_proto.node_name, tensor_proto.slot)
            try:
                load_info = node_info.get('load')
                if load_info is not None:
                    load_info['graph_name'] = node_info.get('graph_name')
                    load_info['node_name'] = node_info.get('node_name')
                    load_tensor(load_info=load_info, step=cur_step, request_iterator=iter([tensor_proto]),
                                cache_store=self._cache_store, rank_id=rank_id)
                oversize = len(tensor_proto.tensor_content) > MAX_SINGLE_TENSOR_CACHE
                value = {
                    'step': cur_step,
                    'tensor_proto': tensor_proto,
                    'tensor_contents': [tensor_proto.tensor_content] if not oversize else [],
                    'stats': node_info.get('stats', False),
                    'oversize': oversize,
                }
                has_update = tensor_stream.put(value)

            except ValueError as err:
                log.warning("Failed to put %s:%s into cache. Ignore it. %s",
                            tensor_proto.node_name, tensor_proto.slot, str(err))
                continue
            if has_update:
                update_data_flag = True
        if update_data_flag:
            # send message to frontend
            metadata = self._metadata_stream.get(['step', 'state'])
            ret = {'receive_tensor': node_info.copy()}
            ret.update(metadata)
            self._cache_store.put_data(ret)

    def _deal_with_run_cmd(self, event):
        """Deal with run cmd."""
        run_cmd = event.run_cmd
        parsed_run_cmd = self._get_parsed_run_cmd(run_cmd)
        if parsed_run_cmd.run_steps > 0:
            self._execute_one_step()
        elif run_cmd.run_level == RunLevel.RECHECK.value:
            log.info("Deal with recheck command.")
            self._check_watchpoint(self._metadata_stream.step)

    def _execute_one_step(self):
        """Execute on step."""
        new_step = self._metadata_stream.step + 1
        if new_step > self._metadata_stream.max_step_num:
            self._old_run_cmd.clear()
            log.info("The server is already at the last step. %s", self._metadata_stream.max_step_num)
            return
        log.info("Go to next step: %s.", new_step)
        self._cache_store.clean_data()
        self._check_watchpoint(new_step)
        self._metadata_stream.step = new_step
        self._cache_store.get_stream_handler(Streams.TENSOR).set_step(new_step)
        self._cache_store.put_data(self._metadata_stream.get(['step', 'state']))

    def _get_parsed_run_cmd(self, run_cmd):
        """Get parsed run command."""
        if run_cmd.run_level == RunLevel.STEP.value:
            # receive pause cmd
            if not run_cmd.run_steps:
                log.debug("Pause training and wait for next command.")
                self._old_run_cmd.clear()
                # update metadata state from sending to waiting
                self._update_state(ServerStatus.WAITING)
                return run_cmd
            # receive step cmd
            left_steps = run_cmd.run_steps - 1
            run_cmd.run_steps = 1
            if left_steps:
                self._old_run_cmd['left_step_count'] = left_steps if left_steps > 0 else -1
        elif run_cmd.node_name:
            self._old_run_cmd['node_name'] = run_cmd.node_name
            run_cmd.node_name = ''
        return run_cmd

    def _check_watchpoint(self, step):
        """
        Save watchpoint hits into cache.

        Args:
            step (int): The step number which starts from 1.
        """
        self._update_state(ServerStatus.RUNNING)
        # Clean watchpoint_hits in cache
        multi_card_hit_streams = self._cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        multi_card_hit_streams.clean()
        if step <= 0:
            log.info("Offline debugger does not support checking initial weights yet.")
            return
        if self._cache_store.get_stream_handler(Streams.WATCHPOINT).empty:
            log.debug("No watchpoint is set. Ignore checking watchpoint.")
            return
        # the iteration number in dump structure which starts from 0.
        iteration_id = step - 1
        hits = Manager().list()
        check_watchpoints_process = Process(target=self._check_watchpoint_work, args=(hits, iteration_id,))
        check_watchpoints_process.start()
        check_watchpoints_process.join()
        log.info("finish check watchpoint of %s", step)
        if hits:
            log.info("Received WatchpointHits. Left run cmd %s change to empty.", self._old_run_cmd)
            self._old_run_cmd.clear()
            self._update_state(ServerStatus.WAITING)
            self._save_watchpoint_hits(hits)

    def _save_watchpoint_hits(self, hits):
        """Save watchpoint hits."""
        multi_card_hit_streams = self._cache_store.get_stream_handler(Streams.WATCHPOINT_HIT)
        multi_card_graph_streams = self._cache_store.get_stream_handler(Streams.GRAPH)
        watchpoint_stream = self._cache_store.get_stream_handler(Streams.WATCHPOINT)

        watchpoint_hits = defaultdict(list)
        for hit in hits:
            log.info("Received hit\n: "
                     "name:%s, slot:%s, condition:%s, "
                     "watchpoint_id:%s"
                     "error_code:%s, rank_id:%s",
                     hit['name'], hit['slot'], hit['condition'],
                     hit['watchpoint_id'], hit['error_code'], hit['rank_id'])
            rank_id = hit['rank_id']
            watchpoint_hit = {}
            self._add_hit_node_info(watchpoint_hit, multi_card_graph_streams, rank_id, hit)
            if not watchpoint_hit:
                continue
            self._add_hit_watchpoint_info(watchpoint_hit, watchpoint_stream, hit)
            watchpoint_hit['error_code'] = hit['error_code']
            watchpoint_hits[rank_id].append(watchpoint_hit)
        # save hit info into cache
        multi_card_hit_streams.put(watchpoint_hits)
        self._cache_store.put_data({'receive_watchpoint_hits': True})
        log.debug("Send the watchpoint hits to DataQueue.")

    @staticmethod
    def _add_hit_node_info(watchpoint_hit, multi_card_graph_streams, rank_id, hit):
        """Add hit node info."""
        graph_stream = multi_card_graph_streams.get_graph_handler_by_rank_id(rank_id)
        node_full_name = hit['name']
        graph_name = graph_stream.get_graph_id_by_full_name(node_full_name)
        if not graph_name:
            log.warning("Cannot find node %s in graph. Skip it.", node_full_name)
            return
        ui_node_name = graph_stream.get_node_name_by_full_name(node_full_name, graph_name)
        log.debug("Receive watch point hit: %s:%s", node_full_name, hit['slot'])
        if not ui_node_name:
            log.info("Not support to show %s on graph.", node_full_name)
            return
        watchpoint_hit.update({
            'tensor_proto': TensorProto(node_name=node_full_name, slot=str(hit['slot'])),
            'node_name': ui_node_name,
            'graph_name': graph_name
        })

    @staticmethod
    def _add_hit_watchpoint_info(watchpoint_hit, watchpoint_stream, hit):
        """Add watchpoint hit info."""
        watchpoint = copy.deepcopy(watchpoint_stream.get_watchpoint_by_id(hit['watchpoint_id']))
        hit_params = {}
        # get hit actual value
        for param in hit['parameters']:
            if param['name'] not in (ParamNameEnum.RTOL.value, ParamNameEnum.RANGE_START_INCLUSIVE.value,
                                     ParamNameEnum.RANGE_END_INCLUSIVE.value) \
                    and hit['error_code'] == 0:
                hit_params[param['name']] = param['actual_value']
        # update actual value into watchpoint
        watchpoint_condition_params = watchpoint.condition['params']
        for i, param in enumerate(watchpoint_condition_params):
            name = param['name']
            if name in hit_params.keys():
                watchpoint_condition_params[i]['actual_value'] = hit_params[name]
            else:
                watchpoint_condition_params[i]['actual_value'] = None

        watchpoint_hit['watchpoint'] = watchpoint

    def _deal_with_set_cmd(self, event):
        """
        Deal with set cmd.

        Args:
            event (EventReply): User command event including set_cmd.
        """
        set_cmd = event.set_cmd
        set_cmd_id = set_cmd.id
        delete = set_cmd.delete
        if not delete:
            log.info("Add watchpoint by using dbg_server.")
            watch_condition = set_cmd.watch_condition
            param_list = []
            for param in watch_condition.params:
                param_list.append(
                    self._dbg_services_module.Parameter(param.name, param.disabled, param.value))
            watch_nodes = set_cmd.watch_nodes
            check_nodes = self._get_check_nodes(watch_nodes)
            log.debug("Watchpoint  %s, condition: %s, watch nodes: %s",
                      set_cmd_id, watch_condition.condition, check_nodes)
            self._dbg_service.add_watchpoint(set_cmd_id, watch_condition.condition, check_nodes, param_list)
        else:
            log.info("Remove watchpoint by using dbg_server.")
            self._dbg_service.remove_watchpoint(set_cmd_id)

    def _get_check_nodes(self, watch_nodes):
        """Get check nodes format."""
        check_nodes = {}
        for watch_node in watch_nodes:
            node_name = watch_node.node_name
            rank_id = watch_node.rank_id
            if node_name not in check_nodes:
                root_graph_id = self.get_root_graph_id(rank_id=rank_id,
                                                       graph_name=watch_node.graph_name,
                                                       node_name=node_name)
                check_nodes[node_name] = {
                    "rank_id": [rank_id],
                    "is_output": True,
                    "root_graph_id": [root_graph_id]
                }
            else:
                check_nodes[node_name]["rank_id"].append(rank_id)
        return check_nodes

    def _update_state(self, server_status):
        """
        Update state in metadata stream.

        Args:
            server_status (ServerStatus): The enum value in ServerStatus.
        """
        if self._metadata_stream.state != server_status.value:
            self._metadata_stream.state = server_status.value
            self._cache_store.clean_data()
            self._cache_store.put_data(self._metadata_stream.get())

    def _check_watchpoint_work(self, hits, step):
        """The check WatchPoint function work in another process."""
        log.info("Start checking WatchPointHit process.")
        res = self._dbg_service.check_watchpoints(step)
        for watchpoint_hit in res:
            hit_dict = convert_watchpointhit(watchpoint_hit)
            hits.append(hit_dict)
        log.info("Checking WatchPointHit process is finished.")


class CommandListener:
    """Event listener."""

    def __init__(self, cache_store):
        self._cache_store = cache_store
        self._metadata_stream = cache_store.get_stream_handler(Streams.METADATA)
        # the next position of command queue to be queried
        self._pos = '0'
        self._is_waiting = Event()

    def start(self):
        """Start event listener."""
        self._pos = '0'
        self._is_waiting.set()

    def stop(self):
        """Stop event listener."""
        # stop waiting for new user commands but can still get old commands.
        self._is_waiting.clear()

    def has_new_command(self):
        """Check if there is new command in command queue."""
        return self._cache_store.has_command(self._pos)

    def get_next_command(self):
        """Get next command."""
        event = None
        while event is None and self.has_new_command():
            self._pos, event = self._cache_store.get_command(self._pos)
            log.debug("Deal with old %s-th command:\n%s.", self._pos, event)
        if event is None:
            event = self._wait_for_next_command()
        return event

    def _wait_for_next_command(self):
        """
        Wait for next command.

        Returns:
            EventReply, the command event.
        """
        if not self._is_waiting.is_set():
            self._metadata_stream.state = ServerStatus.PENDING.value
            return None
        log.info("Start to wait for command.")
        if self._metadata_stream.state != ServerStatus.WAITING.value:
            self._metadata_stream.state = ServerStatus.WAITING.value
            self._cache_store.put_data(self._metadata_stream.get())
        log.debug("Wait for %s-th command", self._pos)
        event = None
        while event is None and self._is_waiting.is_set():
            self._pos, event = self._cache_store.get_command(self._pos)
        return event


def convert_watchpointhit(watchpointhit):
    """Convert watchpointhit object to dict."""
    parameters = watchpointhit.parameters
    param_list = []
    for param in parameters:
        param_dict = convert_param(param)
        param_list.append(param_dict)
    watchpointhit_dict = {'condition': watchpointhit.condition,
                          'rank_id': watchpointhit.rank_id,
                          'error_code': watchpointhit.error_code,
                          'name': watchpointhit.name,
                          'parameters': param_list,
                          'slot': watchpointhit.slot,
                          'watchpoint_id': watchpointhit.watchpoint_id}
    return watchpointhit_dict


def convert_tensor_data(tensor_data):
    """Convert tensor object to dict."""
    tensor_data_dict = {'dtype': tensor_data.dtype,
                        'shape': tensor_data.shape,
                        'data_size': tensor_data.data_size,
                        'data_ptr': tensor_data.data_ptr}
    return tensor_data_dict


def convert_param(param):
    """Convert parameter object to dict"""
    param_dict = {'actual_value': param.actual_value,
                  'disabled': param.disabled,
                  'hit': param.hit,
                  'name': param.name,
                  'value': param.value}
    return param_dict
