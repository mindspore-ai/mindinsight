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
"""Define the utils."""
import enum

import numpy as np

from mindinsight.datavisual.data_transform.graph import NodeTypeEnum
from mindinsight.debugger.proto.debug_grpc_pb2 import EventReply

# translate the MindSpore type to numpy type.
NUMPY_TYPE_MAP = {
    'DT_BOOL': np.bool,

    'DT_INT8': np.int8,
    'DT_INT16': np.int16,
    'DT_INT32': np.int32,
    'DT_INT64': np.int64,

    'DT_UINT8': np.uint8,
    'DT_UINT16': np.uint16,
    'DT_UINT32': np.uint32,
    'DT_UINT64': np.uint64,

    'DT_FLOAT16': np.float16,
    'DT_FLOAT32': np.float32,
    'DT_FLOAT64': np.float64,

    'DT_STRING': np.str
}


@enum.unique
class ReplyStates(enum.Enum):
    """Define the status of reply."""
    SUCCESS = 0
    FAILED = -1


@enum.unique
class ServerStatus(enum.Enum):
    """The status of debugger server."""
    PENDING = 'pending'  # no client session has been connected
    RECEIVE_GRAPH = 'receive graph'  # the client session has sent the graph
    WAITING = 'waiting'  # the client session is ready
    RUNNING = 'running'  # the client session is running a script
    MISMATCH = 'mismatch'  # the version of Mindspore and Mindinsight is not matched
    SENDING = 'sending'  # the request is in cache but not be sent to client


@enum.unique
class Streams(enum.Enum):
    """Define the enable streams to be deal with."""

    COMMAND = "command"
    DATA = "data"
    METADATA = "metadata"
    GRAPH = 'node'
    TENSOR = 'tensor'
    WATCHPOINT = 'watchpoint'
    WATCHPOINT_HIT = 'watchpoint_hit'


class RunLevel(enum.Enum):
    """Run Level enum, it depends on whether the program is executed node by node,
    step by step, or in recheck phase"""
    NODE = "node"
    STEP = "step"
    RECHECK = "recheck"


def get_ack_reply(state=0):
    """The the ack EventReply."""
    reply = EventReply()
    state_mapping = {
        0: EventReply.Status.OK,
        1: EventReply.Status.FAILED,
        2: EventReply.Status.PENDING
    }
    reply.status = state_mapping[state]

    return reply


def wrap_reply_response(error_code=None, error_message=None):
    """
    Wrap reply response.

    Args:
        error_code (str): Error code. Default: None.
        error_message (str): Error message. Default: None.

    Returns:
        str, serialized response.
    """
    if error_code is None:
        reply = {'state': ReplyStates.SUCCESS.value}
    else:
        reply = {
            'state': ReplyStates.FAILED.value,
            'error_code': error_code,
            'error_message': error_message
        }

    return reply


def create_view_event_from_tensor_basic_info(tensors_info):
    """
    Create view event reply according to tensor names.

    Args:
        tensors_info (list[TensorBasicInfo]): The list of TensorBasicInfo. Each element has keys:
            `full_name`, `node_type`, `iter`.

    Returns:
        EventReply, the event reply with view cmd.
    """
    view_event = get_ack_reply()
    for tensor_info in tensors_info:
        node_type = tensor_info.node_type
        if node_type == NodeTypeEnum.CONST.value:
            continue
        truncate_tag = node_type == NodeTypeEnum.PARAMETER.value
        tensor_name = tensor_info.full_name
        # create view command
        ms_tensor = view_event.view_cmd.tensors.add()
        ms_tensor.node_name, ms_tensor.slot = tensor_name.rsplit(':', 1)
        ms_tensor.truncate = truncate_tag
        ms_tensor.iter = tensor_info.iter

    return view_event


def is_scope_type(node_type):
    """Judge whether the type is scope type."""
    return node_type.endswith('scope')


def is_cst_type(node_type):
    """Judge whether the type is const type."""
    return node_type == NodeTypeEnum.CONST.value
