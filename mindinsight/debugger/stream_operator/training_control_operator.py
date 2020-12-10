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
"""This module is aimed to deal with controlling commands."""
import enum

from mindinsight.debugger.common.exceptions.exceptions import DebuggerContinueError, DebuggerParamValueError, \
    DebuggerPauseError, DebuggerRecheckError, DebuggerStepNumError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import Streams, get_ack_reply, ServerStatus, RunLevel, is_scope_type
from mindinsight.debugger.proto.debug_grpc_pb2 import RunCMD
from mindinsight.utils.exceptions import MindInsightException


@enum.unique
class ControlTypeEnum(enum.Enum):
    """Control Type."""
    CONTINUE = 'continue'  # continue to run training
    PAUSE = 'pause'  # suspend training
    TERMINATE = 'terminate'  # terminate training


class TrainingControlOperator:
    """Control training operator."""
    # max step number should be less than int32
    _MAX_STEP_NUM = 2 ** 31 - 1

    def __init__(self, cache_store):
        self._cache_store = cache_store
        self._watchpoint_stream = cache_store.get_stream_handler(Streams.WATCHPOINT)
        self._graph_stream = cache_store.get_stream_handler(Streams.GRAPH)
        self._metadata_stream = cache_store.get_stream_handler(Streams.METADATA)

    @staticmethod
    def validate_mode(mode):
        """Validate mode."""
        enum_members = [item.value for item in ControlTypeEnum]
        if mode not in enum_members:
            log.error("Invalid control mode %s", mode)
            raise DebuggerParamValueError("Invalid control mode.")

    def control(self, mode, params):
        """
        Control the training process.

        Args:
            mode (str): Acceptable control command, including `continue`,
                    `pause` and `terminate`.
            params (dict): The control params.

                - level (str): The control granularity, `node` level or `step` level.
                    Default: `step`.
                - steps (int): Specify the steps that training should run.
                    Used when `level` is `step`.
                - name (str): Specify the name of the node. Used when `level` is `node`.
                - graph_name (str): The graph name.

        Returns:
            dict, the response.
        """
        if mode == ControlTypeEnum.CONTINUE.value:
            reply = self.continue_training(params)
        else:
            mode_mapping = {
                ControlTypeEnum.PAUSE.value: self.pause_training,
                ControlTypeEnum.TERMINATE.value: self.terminate_training
            }
            reply = mode_mapping.get(mode)()
        return reply

    def continue_training(self, params):
        """
        Send RunCMD to MindSpore.

        Args:
            params (dict): The control params.

        Returns:
            dict, metadata info.
        """
        metadata_stream = self._metadata_stream
        if metadata_stream.state != ServerStatus.WAITING.value:
            log.error("MindSpore is not ready to run. Current state is: %s", metadata_stream.state)
            raise DebuggerContinueError(
                "MindSpore is not ready to run or is running currently."
            )
        metadata_stream.state = ServerStatus.SENDING.value
        try:
            self._validate_continue_params(params)
            event = self._construct_run_event(params)
            # whether need to send recheck before continue, especially for initialization watchpoint
            recheck_flag = bool(self._metadata_stream.step == 0 and self._watchpoint_stream.is_recheckable())
            self._send_watchpoints()
            if recheck_flag:
                self._cache_store.put_command(self._construct_run_event({'level': 'recheck'}))
                log.info("Send recheck command for initialization watchpoints before continue command.")
            self._cache_store.put_command(event)
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
            DebuggerStepNumError: Step number are invalid.
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

    def _validate_continue_node_name(self, node_name, graph_name):
        """Validate if the node is a leaf node."""
        if not node_name:
            return
        node_type = self._graph_stream.get_node_type(node_name, graph_name)
        if is_scope_type(node_type):
            log.error("Scope type node has no tensor history.")
            raise DebuggerParamValueError("Invalid leaf node name.")

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
                name = self._cache_store.get_stream_handler(Streams.GRAPH).get_full_name(name, graph_name)
            run_cmd = RunCMD(run_level='node', node_name=name)
        else:
            run_cmd = RunCMD(run_level='recheck')

        event.run_cmd.CopyFrom(run_cmd)
        log.debug("Construct run event. %s", event)
        return event

    def _send_watchpoints(self):
        """Send watchpoints to client."""
        set_commands = self._watchpoint_stream.get_pending_commands(self._graph_stream)
        if not set_commands:
            return
        for set_cmd in set_commands:
            event = get_ack_reply()
            event.set_cmd.CopyFrom(set_cmd)
            self._cache_store.put_command(event)
            log.debug("Send SetCMD to MindSpore. %s", event)

    def pause_training(self):
        """
        Pause the training.

        Returns:
            dict, metadata info.
        """
        metadata_stream = self._metadata_stream
        if metadata_stream.state != ServerStatus.RUNNING.value:
            log.error("The MindSpore is not running.")
            raise DebuggerPauseError("The MindSpore is not running.")
        metadata_stream.state = ServerStatus.SENDING.value
        event = get_ack_reply()
        event.run_cmd.CopyFrom(RunCMD(run_level='step', run_steps=0))
        self._cache_store.clean_command()
        self._cache_store.put_command(event)
        metadata_stream.enable_recheck = False
        log.debug("Send the Pause command")
        return metadata_stream.get(['state', 'enable_recheck'])

    def terminate_training(self):
        """
        Terminate the training.

        Returns:
            dict, metadata info.
        """
        metadata_stream = self._metadata_stream
        metadata_stream.state = ServerStatus.SENDING.value
        self._cache_store.clean_data()
        self._cache_store.clean_command()
        event = get_ack_reply()
        event.exit = True
        self._cache_store.put_command(event)
        metadata_stream.enable_recheck = False
        log.debug("Send the ExitCMD.")
        return metadata_stream.get(['state', 'enable_recheck'])

    def recheck(self):
        """
        Recheck all watchpoints.

        Returns:
            dict, metadata info.
        """
        metadata_stream = self._metadata_stream
        # validate backend status is able to recheck watchpoint
        if not metadata_stream.enable_recheck:
            log.error("Recheck is not available.")
            raise DebuggerRecheckError("Recheck is not available.")
        metadata_stream.state = ServerStatus.SENDING.value
        metadata_stream.enable_recheck = False
        # send updated watchpoint and recheck command
        try:
            event = self._construct_run_event({'level': 'recheck'})
            self._send_watchpoints()
            self._cache_store.put_command(event)
        except MindInsightException as err:
            log.error("Failed to send recheck event.")
            log.exception(err)
            metadata_stream.state = ServerStatus.WAITING.value
            metadata_stream.enable_recheck = True
            raise DebuggerContinueError("Failed to send recheck command.")
        else:
            log.debug("Send the recheck to command queue.")
        return metadata_stream.get(['state', 'enable_recheck'])
