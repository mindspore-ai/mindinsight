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
"""Define the tensor stream handler."""
import os
import tempfile
import threading
import time
from collections import OrderedDict
from collections import namedtuple

import numpy as np

from mindinsight.conf import settings
from mindinsight.datavisual.data_transform.graph.node import NodeTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError, DebuggerDownloadOverQueue, \
    DebuggerDownloadTensorNotExist
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import MAX_CACHE_SPACE, MAX_SINGLE_TENSOR_CACHE
from mindinsight.debugger.stream_cache.tensor import OpTensor, ConstTensor, TensorStatusEnum, DownloadStatusEnum
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase
from mindinsight.domain.graph.proto.ms_graph_pb2 import DataType
from mindinsight.utils.tensor import TensorUtils, TensorComparison

TensorBasicInfo = namedtuple('tensor_basic_info', ['full_name', 'node_type', 'iter'])
FILE_MODE = 0o600
DIR_MODE = 0o700


class MemoryMgr:
    """The memory manager of tensors."""

    def __init__(self):
        self._memory_queue = OrderedDict()
        self._remaining_cache_space = MAX_CACHE_SPACE
        self._lock = threading.Lock()

    @property
    def remaining_cache_space(self):
        return self._remaining_cache_space

    def request(self, key, request_space, release_func):
        """Request for the memory space."""
        if self.check_space(request_space):
            release_func(True)
            return
        if request_space == 0:
            return
        with self._lock:
            if key in self._memory_queue:
                log.error("Key already exist error for memory queue.")
                raise ValueError("Key already exist error for memory queue.")
            self._remaining_cache_space -= request_space
        while self._remaining_cache_space <= 0:
            self.release()
        with self._lock:
            self._memory_queue[key] = (request_space, release_func)

    def release(self, key=None):
        """Release the memory space."""
        with self._lock:
            if key is not None:
                if key not in self._memory_queue:
                    return
                self._memory_queue.move_to_end(key, last=False)
            _, value = self._memory_queue.popitem(last=False)
            free_space, release_func = value
            release_func()
            self._remaining_cache_space += free_space
            log.debug("Update cache space.")

    @staticmethod
    def check_space(space):
        """Check if the space over allowed space."""
        return space >= MAX_SINGLE_TENSOR_CACHE


class DownloadMgr:
    """The download manager."""

    def __init__(self):
        """Download manager."""

        self._temp_base_dir = self.mk_temp_base_dir()
        self.tensor_info = None
        self.file_name = None
        self.file_path = None
        self.temp_dir = None
        self._lock = threading.Lock()
        self.status = DownloadStatusEnum.PENDING.value

    @property
    def temp_base_dir(self):
        return self._temp_base_dir

    def add(self, file_name, file_path, temp_dir, **tensor_info):
        """Add the temp file path."""
        with self._lock:
            if self.status != DownloadStatusEnum.SENDING.value:
                self.file_name = file_name
                self.file_path = file_path
                self.temp_dir = temp_dir
                self.tensor_info = tensor_info
                return
        log.error("There is already a tensor in download")
        raise DebuggerDownloadOverQueue()

    def get(self, **tensor_info):
        """Get the temp file path."""
        with self._lock:
            if self.tensor_info == tensor_info:
                self.status = DownloadStatusEnum.SENDING.value
                return self.file_name, self.file_path, self.clean
        log.error("No such tensor to download")
        raise DebuggerDownloadTensorNotExist()

    def check_status(self):
        """Check the download status."""
        if self.status == DownloadStatusEnum.SENDING.value:
            log.error("There is already a tensor in download")
            raise DebuggerDownloadOverQueue()

    @staticmethod
    def mk_temp_base_dir():
        workspace = settings.WORKSPACE
        temp_base_dir = os.path.join(workspace, 'tempdata')
        os.makedirs(temp_base_dir, DIR_MODE, exist_ok=True)
        return temp_base_dir

    def clean(self):
        """Clean cache."""
        with self._lock:
            if self.temp_dir:
                self.temp_dir.cleanup()
            self.temp_dir = None
            self.tensor_info = None
            self.file_name = None
            self.file_path = None
            self.status = DownloadStatusEnum.PENDING.value


class MultiCardTensorHandler:
    """Multi-card Tensor Handler."""
    def __init__(self):
        self._memory_mgr = MemoryMgr()
        self._download_mgr = DownloadMgr()
        self.tensor_handlers = {0: TensorHandler(self._memory_mgr, self._download_mgr, rank_id=0)}

    @property
    def download_mgr(self):
        return self._download_mgr

    def set_step(self, step_id):
        """Set step id."""
        for tensor_handler in self.tensor_handlers.values():
            tensor_handler.cur_step = step_id

    def get_tensor_handler_by_rank_id(self, rank_id=0, create_if_not_exit=False):
        """get handler by rank id"""
        if rank_id in self.tensor_handlers:
            return self.tensor_handlers.get(rank_id)
        if create_if_not_exit:
            tensor_handler = TensorHandler(self._memory_mgr, self._download_mgr, rank_id=rank_id)
            self.tensor_handlers[rank_id] = tensor_handler
            return tensor_handler
        log.error("There is no rank id %d in MultiCardTensorHandler.", rank_id)
        raise ValueError

    def put(self, value):
        """put graphs into graph_handlers"""
        for rank_id, tensor in value:
            if rank_id not in self.tensor_handlers:
                self.tensor_handlers[rank_id] = TensorHandler(self._memory_mgr, self._download_mgr, rank_id=rank_id)
            self.tensor_handlers[rank_id].put(tensor)

    def get(self, filter_condition=None, rank_id=0):
        """Get the graph of specific node for specific device."""
        if rank_id in self.tensor_handlers:
            return self.tensor_handlers.get(rank_id).get(filter_condition)
        log.error("There is no rank id %d.", rank_id)
        raise ValueError

    def clean(self):
        """Clean cache."""
        self.__init__()

    @staticmethod
    def tensor_basic_info(full_name, node_type, iter_step):
        return TensorBasicInfo(full_name=full_name, node_type=node_type, iter=iter_step)


class TensorHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self, memory_mgr, download_mgr, rank_id):
        # the collection of parameter full names
        self._param_names = set()
        # const value objects, the format is like: dict[<const name>, <OpTensor object>]
        self._const_vals = {}
        # tensor values, the format is like:
        # dict[<tensor full name>, dict[<step_num>, <OpTensor object>]]
        self._tensors = {}
        self._cur_step = 0
        self._memory_mgr = memory_mgr
        self.download_mgr = download_mgr
        self._rank_id = rank_id
        self._hold_value = {}

    @property
    def cur_step(self):
        """The property of current step."""
        return self._cur_step

    @cur_step.setter
    def cur_step(self, step_id):
        """The property of current step."""
        self._cur_step = step_id

    @property
    def prev_step(self):
        """The property of previous step."""
        return self._cur_step - 1

    def put(self, value):
        """
        Put value into tensor cache. Called by grpc server.

        Args:
            value (dict): The Tensor proto message.

                - step (int): The current step of tensor.
                - tensor_proto (TensorProto): The tensor proto.
                - tensor_contents (list[byte]): The list of tensor content values.

        Returns:
            bool, the tensor has updated successfully.
        """
        tensor = self._deal_with_tensor(value)
        tensor_info = value.get('load')
        if tensor_info is not None:
            self.load(tensor_info.get('tensor_name'), tensor_info.get('graph_name'), tensor_info.get('prev'),
                      tensor_info.get('node_type'), tensor=tensor)

        stats = None
        if value.get('stats', False) and tensor.status != TensorStatusEnum.EMPTY.value:
            tensor.calculate_stats()
            stats = tensor.stats

        flag = self._put_tensors(tensor)
        new_tensor = self._tensors.get(tensor.name).get(tensor.step)
        new_tensor.stats = stats
        log.info("Put tensor %s of step: %d, into cache. Flag: %s", tensor.name, tensor.step, flag)
        return flag

    @staticmethod
    def _deal_with_tensor(value):
        """Deal with tensor from tensor proto."""
        tensor_proto = value.get('tensor_proto')
        tensor_proto.ClearField('tensor_content')
        step = value.get('step', 0)
        if tensor_proto.iter and step > 0:
            log.debug("Received previous tensor.")
            step -= 1
        tensor_content = b''.join(value.get('tensor_contents'))
        tensor = OpTensor(tensor_proto, tensor_content, step)
        if value.get('oversize'):
            tensor.clean_tensor_value(oversize=True)
        return tensor

    def _put_tensors(self, tensor):
        """
        Put tensor into cache.

        Args:
            tensor (OpTensor): The tensor value.

        Returns:
            bool, the tensor has updated successfully.
        """
        step = tensor.step
        cache_tensor = self._tensors.get(tensor.name)
        if cache_tensor is None:
            cache_tensor = {}
            self._tensors[tensor.name] = cache_tensor

        if not self._hold_value.pop((tensor.name, tensor.step), False):
            tensor.clean_tensor_value(oversize=False)

        old_tensor = cache_tensor.get(step)
        if not old_tensor or (old_tensor.status == TensorStatusEnum.CACHED.value and self._is_value_diff(
                old_tensor.value, tensor.value)) or (old_tensor.status == TensorStatusEnum.UNCACHED.value):
            self._put_tensor_into_cache(cache_tensor, tensor)
            return True
        return False

    def _put_tensor_into_cache(self, cache_tensor, tensor):
        """Put tensor into cache."""
        step = tensor.step
        self._memory_mgr.release((self._rank_id, tensor.name, step))

        def release_func(over_size=False):
            cache_tensor.get(step).clean_tensor_value(over_size)

        self._memory_mgr.request((self._rank_id, tensor.name, step), tensor.nbytes, release_func)
        cache_tensor[step] = tensor
        log.debug("Put updated tensor value for %s of step %s.", tensor.name, step)

    @staticmethod
    def _is_value_diff(old_value, new_value):
        """Check tensor value if there are equal."""
        log.debug("old value type: %s, new_value type: %s", type(old_value), type(new_value))
        if old_value is None and new_value is None:
            return False
        flag = old_value != new_value
        if isinstance(flag, np.ndarray):
            return flag.any()
        return flag

    def put_const_vals(self, const_vals):
        """
        Put const value into tensor cache.

        Args:
            const_vals (list[NamedValueProto]): List of const values.
        """
        for const_val in const_vals:
            if not (const_val.value and const_val.key):
                continue
            if DataType.Name(const_val.value.dtype) == "DT_TENSOR":
                tensor_proto = const_val.value.tensor_val
                tensor_value = tensor_proto.tensor_content
                tensor_proto.ClearField('tensor_content')
                tensor_proto.node_name = const_val.key
                tensor_proto.slot = '0'
                const_tensor = OpTensor(tensor_proto, tensor_value)
            else:
                const_tensor = ConstTensor(const_val)
            self._const_vals[const_tensor.name] = const_tensor

    def record_parameter_names(self, names):
        """
        Record parameter names.

        Note:
            Parameter values could be changed during an iteration step. It must be cleaned after each node step.

        Args:
            names (list[str]): List of tensor full names.
        """
        self._param_names.update(names)
        log.debug("Record %d parameters in cache. Total parameter number: %d", len(names), len(self._param_names))

    def get(self, filter_condition=None):
        """
        Get full tensor value.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The full name of tensor.
                - node_type (str): The type of the node.
                - prev (bool): Whether to get previous tensor.

        Returns:
            dict, the tensor_value and whether need to send view_command.
        """
        name = filter_condition.get('name')
        node_type = filter_condition.get('node_type')
        shape = filter_condition.get('shape')
        if filter_condition.get('prev'):
            step = self.prev_step
        else:
            step = self.cur_step
        tensor = self._get_tensor(name, node_type, step)
        if not tensor:
            log.error("No tensor named %s at the step %s", name, step)
            raise DebuggerParamValueError("No tensor named {}".format(name))
        tensor_info = tensor.get_full_info(shape)
        self._update_has_prev_step_field(tensor_info, name, node_type, self.cur_step)
        res = {
            'tensor_value': tensor_info,
            'view_cmd': False
        }
        if tensor.status == TensorStatusEnum.UNCACHED.value:
            self._add_hold_value_tensors(name, step)
            res['view_cmd'] = True
        return res

    def _get_tensor(self, tensor_name, node_type=None, step=None):
        """
        Get tensor according to tensor name and node_type.

        Args:
            tensor_name (str): Tensor name, format like `node_name:slot`.
            node_type (str): Node type.
            step (int): The step of tensor info. Default: None.

        Returns:
            Union[OPTensor, ConstTensor], the tensor object.
        """
        if step is None:
            step = self._cur_step
        tensor = self._tensors.get(tensor_name, {}).get(step)
        if not tensor and node_type == NodeTypeEnum.CONST.value:
            const_name = tensor_name.rsplit('/', 1)[-1]
            tensor = self._const_vals.get(const_name)
            if tensor:
                self._tensors[tensor_name] = {step: tensor}

        return tensor

    def _get_basic_info(self, tensor_name, node_type, step):
        """Get the latest basic tensor info by tensor name."""
        tensor = self._get_tensor(tensor_name, node_type, step)
        if tensor:
            return tensor.get_basic_info()

        return None

    def update_tensor_history(self, tensor_history, step=None):
        """
        Add tensor basic info in tensor_history.

        Args:
            tensor_history (dict): Tensor history, including a list of tensor name and type.
            step (int): The step of tensor info. Default: None.

        Returns:
            list[dict], the list of tensor basic info cache.
        """
        missed_tensors = []
        for tensor_info in tensor_history.get('tensor_history'):
            tensor_name = tensor_info.get('full_name')
            node_type = tensor_info.get('node_type')
            basic_info = self._get_basic_info(tensor_name, node_type, step)
            # add `has_prev_step` field to tensor basic info.
            missing_tensors_info = self._update_has_prev_step_field(basic_info, tensor_name, node_type, step)
            if basic_info:
                tensor_info.update(basic_info)
            if missing_tensors_info:
                missed_tensors.extend(missing_tensors_info)

        return missed_tensors

    def _update_has_prev_step_field(self, tensor_info, tensor_name, node_type, step=None, check_cache=False,
                                    check_stats=False):
        """Update has_prev_step field in tensor info."""
        if step is None:
            step = self._cur_step
        missing_tensors_info = self.get_missing_tensor_info(tensor_name, node_type, step, check_cache=check_cache,
                                                            check_stats=check_stats)
        if not missing_tensors_info and node_type == NodeTypeEnum.PARAMETER.value and step > 0:
            tensor_info['has_prev_step'] = True
        return missing_tensors_info

    def get_missing_tensor_info(self, tensor_name, node_type, step=None, cur=True, prev=True, check_cache=False,
                                check_stats=False):
        """
        Get missing tensor infos.

        Args:
            tensor_name (str): The full name of Tensor.
            node_type (str): The type of the relative node.
            step (int): The step of tensor info. Default: None.
            check_cache (bool): Whether to check the tensor value. Default: False.
            check_stats (bool): Whether to check the tensor statistic. Default: False.
            cur (bool): Whether to get the current tensor info. Default: True.
            prev (bool): Whether to get the previous tensor info. Default: True.

        Returns:
            list, list of missing tensor basic information.
        """
        if step is None:
            step = self._cur_step
        missing_tensors_info = []
        # check the current step value is missing
        if self._is_tensor_value_missing(tensor_name, step, check_cache, check_stats) and cur:
            missing_tensors_info.append(TensorBasicInfo(full_name=tensor_name, node_type=node_type, iter=''))
            log.debug("Add current step view cmd for %s", tensor_name)
        # check the previous step value is missing
        if node_type == NodeTypeEnum.PARAMETER.value and \
                self._is_tensor_value_missing(tensor_name, step - 1, check_cache, check_stats) and prev:
            missing_tensors_info.append(TensorBasicInfo(full_name=tensor_name, node_type=node_type, iter='prev'))
            log.debug("Add previous view cmd for %s", tensor_name)
        return missing_tensors_info

    def _is_tensor_value_missing(self, tensor_name, step, check_cache=False, check_stats=False):
        """
        Get the status of tensor value of previous step.

        Args:
            tensor_name (str): Tensor name.
            step (int): The step of the tensor.
            check_cache (bool): Whether to check the tensor value. Default: False.

        Returns:
            Union[None, bool], the status of tensor value. If False, there is valid
                tensor value. If True, the tensor value should be queried from client.
                If None, ignore.
        """
        if step < 0:
            return None
        tensor = self._get_tensor(tensor_name, step=step)
        res = bool(not tensor or tensor.status == TensorStatusEnum.EMPTY.value)
        if check_cache:
            res = bool(res or tensor.status == TensorStatusEnum.UNCACHED.value)
        if check_stats:
            res = bool(res or tensor.stats is None)
        return res

    def get_valid_tensor_by_name(self, tensor_name, step, prev=False):
        """Get tensor value by name in numpy type."""
        target_step = step - 1 if prev else step
        if target_step < 0:
            log.warning("Step %d has no previous value for tensor: %s", target_step, tensor_name)
            return None
        tensor = self._get_tensor(tensor_name, step=target_step)
        return tensor

    def clean_tensors(self, cur_step):
        """Clean the tensor cache."""
        if cur_step != self._cur_step:
            self._cur_step = cur_step
            self._clean_expired_tensors(cur_step)
        self._clean_parameters()

    def _clean_expired_tensors(self, cur_step):
        """Clean expired tensors less than current steps."""
        expired_tensor = []
        for tensor_name, tensor in self._tensors.items():
            expired_step = [step for step in tensor.keys() if step <= cur_step - 2]
            for step in expired_step:
                self._memory_mgr.release((self._rank_id, tensor_name, step))
            if not tensor:
                expired_tensor.append(tensor_name)
        for tensor_name in expired_tensor:
            self._tensors.pop(tensor_name)

    def _clean_parameters(self):
        """Clean parameter cache."""
        for param in self._param_names:
            if param in self._tensors:
                params = self._tensors.pop(param)
                for step in params:
                    self._memory_mgr.release((self._rank_id, param, step))
                log.debug("Clean param %s in cache.", param)

    def get_tensors_diff(self, tensor_name, shape, tolerance=0, step=None):
        """
        Get tensor comparisons data for given name, detail, shape and tolerance.

        Args:
            tensor_name (str): The name of tensor for cache.
            shape (tuple): Specify concrete dimensions of shape.
            tolerance (str): Specify tolerance of difference between current step tensor and previous
                step tensor. Default value is 0. Its is a percentage. The boundary value is equal to
                max(abs(min),abs(max)) * tolerance. The function of min and max is being used to
                calculate the min value and max value of the result of the current step tensor subtract
                the previous step tensor. If the absolute value of result is less than or equal to
                boundary value, the result will set to be zero.
            step (int): The step of the tensor. Default: None.

        Raises:
            DebuggerParamValueError, If get current step node and previous step node failed or
                the type of tensor value is not numpy.ndarray."

        Returns:
            dict, the retrieved data.
        """
        curr_tensor = self.get_valid_tensor_by_name(tensor_name, step=step)
        prev_tensor = self.get_valid_tensor_by_name(tensor_name, prev=True, step=step)
        if not (curr_tensor and prev_tensor) or self._check_no_comparison_status(
                curr_tensor) or self._check_no_comparison_status(prev_tensor):
            log.error("Get current step and previous step for this tensor name %s failed.", tensor_name)
            raise DebuggerParamValueError(f"Get current step and previous step for this tensor name "
                                          f"{tensor_name} failed.")
        if self._check_not_cached_status(curr_tensor) or self._check_not_cached_status(prev_tensor):
            self._add_hold_value_tensors(tensor_name, step)
            return {'view_cmd': True}
        curr_tensor_slice = curr_tensor.get_tensor_value_by_shape(shape)
        prev_tensor_slice = prev_tensor.get_tensor_value_by_shape(shape)
        # get tensor comparison basic info
        tensor_info = curr_tensor.get_basic_info()
        tensor_info.pop('has_prev_step')
        tensor_info.pop('value')
        # calculate tensor comparison object
        tensor_comparison = curr_tensor.tensor_comparison
        if not tensor_comparison or tensor_comparison.tolerance != tolerance:
            if curr_tensor.value.shape != prev_tensor.value.shape:
                raise DebuggerParamValueError("The shape of these two step tensors is not the same.")
            tensor_diff = TensorUtils.calc_diff_between_two_tensor(curr_tensor.value, prev_tensor.value, tolerance)
            stats = TensorUtils.get_statistics_from_tensor(tensor_diff)
            tensor_comparison = TensorComparison(tolerance, stats, tensor_diff)
            curr_tensor.update_tensor_comparisons(tensor_comparison)
        # calculate diff value
        # the type of curr_tensor_slice is one of np.ndarray or str
        if isinstance(curr_tensor_slice, np.ndarray) and isinstance(prev_tensor_slice, np.ndarray):
            if not shape:
                tensor_diff_slice = tensor_comparison.value
            else:
                tensor_diff_slice = tensor_comparison.value[shape]
            result = np.stack([prev_tensor_slice, curr_tensor_slice, tensor_diff_slice], axis=-1)
            tensor_info['diff'] = result.tolist()
        elif isinstance(curr_tensor_slice, str):
            tensor_info['diff'] = curr_tensor_slice
        # add comparison statistics
        tensor_info.update(self._get_comparison_statistics(curr_tensor, prev_tensor))
        reply = {'tensor_value': tensor_info}
        return reply

    def _add_hold_value_tensors(self, tensor_name, step):
        """Add tensors which hold tensor values."""
        self._hold_value[(tensor_name, step)] = True
        # if the current step > 1, the last step will be also recorded
        if step - 1 >= 0:
            self._hold_value[(tensor_name, step - 1)] = True

    @staticmethod
    def _check_no_comparison_status(tensor):
        """Check the status that have no comparison."""
        return tensor.status == TensorStatusEnum.EMPTY.value or tensor.status == TensorStatusEnum.OVERSIZE.value

    @staticmethod
    def _check_not_cached_status(tensor):
        """Check the tensor with not cached status."""
        return tensor.status == TensorStatusEnum.UNCACHED.value

    @staticmethod
    def _get_comparison_statistics(curr_tensor, prev_tensor):
        """Get comparison statistics."""
        stats_info = {}
        diff_tensor_stats = curr_tensor.tensor_comparison.stats
        curr_tensor_stats = TensorUtils.get_statistics_from_tensor(curr_tensor.value)
        prev_tensor_stats = TensorUtils.get_statistics_from_tensor(prev_tensor.value)
        stats_info['curr_step_statistics'] = TensorUtils.get_overall_statistic_dict(overall_stats=curr_tensor_stats)
        stats_info['prev_step_statistics'] = TensorUtils.get_overall_statistic_dict(overall_stats=prev_tensor_stats)
        stats_info['statistics'] = TensorUtils.get_overall_statistic_dict(overall_stats=diff_tensor_stats)
        return stats_info

    def get_tensor_info_for_tensor_graph(self, tensor_name, node_type, step):
        """
        Get Tensor info for tensor graphs.

        Args:
            tensor_name (str): Tensor name, format like `node_name:slot`.
            node_type (str): Node type.
            step (int): The step of tensor info.

        Returns:
            dict, tensor infos, including overall statistics, tensor shape and has_prev_step info.
            list, list of missing tensor basic information.
        """
        res = {}
        tensor = self._get_tensor(tensor_name, node_type, step)
        if tensor and (not tensor.empty or tensor.stats):
            res['statistics'] = tensor.get_tensor_statistics()
            res['shape'] = tensor.shape
        missing_tensors = self._update_has_prev_step_field(res, tensor_name, node_type, step)
        return res, missing_tensors

    def load(self, tensor_name, graph_name, prev, node_type, tensor=None):
        """Load the tensor."""
        self.download_mgr.check_status()
        step = self._cur_step
        if prev:
            step -= 1
        tensor = self._get_tensor(tensor_name, node_type, step) if tensor is None else tensor
        if not tensor or tensor.status == TensorStatusEnum.EMPTY.value:
            log.error("No tensor named %s at the step %s", tensor_name, step)
            raise DebuggerParamValueError("No tensor named {}".format(tensor_name))
        if tensor.download_size > MAX_CACHE_SPACE:
            log.error("Tensor named %s at the step %s is too large to download.", tensor_name, step)
            raise DebuggerParamValueError(
                "Tensor named {} at the step {} is too large to download.".format(tensor_name, step))
        if tensor.status == TensorStatusEnum.CACHED.value:
            temp_dir = tempfile.TemporaryDirectory(dir=self.download_mgr.temp_base_dir)
            os.chmod(temp_dir.name, DIR_MODE)
            node_name, slot = tensor_name.rsplit(':', 1)
            _, node_name = node_name.rsplit('/', 1)
            file_name = "{}.{}.0.0.{}.output.{}.NONE.npy".format(node_type, node_name, round(time.time() * 100),
                                                                 slot)
            file_path = os.path.join(temp_dir.name, file_name)
            np.save(file_path, tensor.value)
            os.chmod(file_path, FILE_MODE)
            tensor_info = {
                "tensor_name": tensor_name,
                "graph_name": graph_name,
                "step": step,
                "rank_id": self._rank_id
            }
            self.download_mgr.add(file_name, file_path, temp_dir, **tensor_info)
            return {'in_memory': True}
        return {'in_memory': False}
