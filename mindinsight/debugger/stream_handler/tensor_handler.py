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
"""Define the tensor stream handler."""
from collections import namedtuple

import numpy as np

from mindinsight.datavisual.data_transform.graph.node import NodeTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.proto.ms_graph_pb2 import DataType
from mindinsight.debugger.stream_cache.tensor import OpTensor, ConstTensor
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase
from mindinsight.utils.tensor import TensorUtils, TensorComparison

TensorBasicInfo = namedtuple('tensor_basic_info', ['full_name', 'node_type', 'iter'])


class TensorHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        # the collection of parameter full names
        self._param_names = set()
        # const value objects, the format is like: dict[<const name>, <OpTensor object>]
        self._const_vals = {}
        # tensor values, the format is like:
        # dict[<tensor full name>, dict[<step_num>, <OpTensor object>]]
        self._tensors = {}
        self._cur_step = 0

    @property
    def cur_step(self):
        """The property of current step."""
        return self._cur_step

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
        tensor_proto = value.get('tensor_proto')
        tensor_proto.ClearField('tensor_content')
        step = value.get('step', 0)
        if tensor_proto.iter and step > 0:
            log.debug("Received previous tensor.")
            step -= 1
        tensor_content = b''.join(value.get('tensor_contents'))
        tensor = OpTensor(tensor_proto, tensor_content, step)
        flag = self._put_tensor_into_cache(tensor, step)
        log.info("Put tensor %s of step: %d, into cache. Flag: %s", tensor.name, step, flag)
        return flag

    def _put_tensor_into_cache(self, tensor, step):
        """
        Put tensor into cache.

        Args:
            tensor (OpTensor): The tensor value.
            step (int): The step of tensor.

        Returns:
            bool, the tensor has updated successfully.
        """
        cache_tensor = self._tensors.get(tensor.name)
        if cache_tensor is None:
            cache_tensor = {}
            self._tensors[tensor.name] = cache_tensor

        old_tensor = cache_tensor.get(step)
        if old_tensor and not self._is_value_diff(old_tensor.value, tensor.value):
            log.debug("Tensor %s of step %s has no change. Ignore it.", tensor.name, step)
            return False
        cache_tensor[step] = tensor
        log.debug("Put updated tensor value for %s of step %s.", tensor.name, step)
        return True

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
            dict, the tensor_value.
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
        self._update_has_prev_step_field(tensor_info, name, node_type)
        return {'tensor_value': tensor_info}

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

    def _get_basic_info(self, tensor_name, node_type=None):
        """Get the latest basic tensor info by tensor name."""
        tensor = self._get_tensor(tensor_name, node_type)
        if tensor:
            return tensor.get_basic_info()

        return None

    def update_tensor_history(self, tensor_history):
        """
        Add tensor basic info in tensor_history.

        Args:
            tensor_history (dict): Tensor history, including a list of tensor name and type.

        Returns:
            list[dict], the list of tensor basic info cache.
        """
        missed_tensors = []
        for tensor_info in tensor_history.get('tensor_history'):
            tensor_name = tensor_info.get('full_name')
            node_type = tensor_info.get('node_type')
            basic_info = self._get_basic_info(tensor_name, node_type)
            # add `has_prev_step` field to tensor basic info.
            missing_tensors_info = self._update_has_prev_step_field(basic_info, tensor_name, node_type)
            if basic_info:
                tensor_info.update(basic_info)
            if missing_tensors_info:
                missed_tensors.extend(missing_tensors_info)

        return missed_tensors

    def _update_has_prev_step_field(self, tensor_info, tensor_name, node_type):
        """Update has_prev_step field in tensor info."""
        missing_tensors_info = self._get_missing_tensor_info(tensor_name, node_type)
        if not missing_tensors_info and node_type == NodeTypeEnum.PARAMETER.value and self.cur_step > 0:
            tensor_info['has_prev_step'] = True
        return missing_tensors_info

    def _get_missing_tensor_info(self, tensor_name, node_type):
        """
        Get missing tensor infos.

        Args:
            tensor_name (str): The full name of Tensor.
            node_type (str): The type of the relative node.

        Returns:
            list, list of missing tensor basic information.
        """
        step = self.cur_step
        missing_tensors_info = []
        # check the current step value is missing
        if self._is_tensor_value_missing(tensor_name, step):
            missing_tensors_info.append(TensorBasicInfo(full_name=tensor_name, node_type=node_type, iter=''))
            log.debug("Add current step view cmd for %s", tensor_name)
        # check the previous step value is missing
        if node_type == NodeTypeEnum.PARAMETER.value and self._is_tensor_value_missing(tensor_name, step - 1):
            missing_tensors_info.append(TensorBasicInfo(full_name=tensor_name, node_type=node_type, iter='prev'))
            log.debug("Add previous view cmd for %s", tensor_name)
        return missing_tensors_info

    def _is_tensor_value_missing(self, tensor_name, step):
        """
        Get the status of tensor value of previous step.

        Args:
            tensor_name (str): Tensor name.
            step (int): The step of the tensor.

        Returns:
            Union[None, bool], the status of tensor value. If False, there is valid
                tensor value. If True, the tensor value should be queried from client.
                If None, ignore.
        """
        if step < 0:
            return None
        tensor = self._get_tensor(tensor_name, step=step)
        return bool(not tensor or tensor.empty)

    def get_valid_tensor_by_name(self, tensor_name, prev=False):
        """Get tensor value by name in numpy type."""
        step = self.prev_step if prev else self.cur_step
        if step < 0:
            log.warning("%d step has no previous value for tensor: %s", self.cur_step, tensor_name)
            return None
        tensor = self._get_tensor(tensor_name, step=step)
        if tensor and tensor.empty:
            log.warning("%s has empty value.", tensor_name)
            return None
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
                tensor.pop(step)
            if not tensor:
                expired_tensor.append(tensor_name)
        for tensor_name in expired_tensor:
            self._tensors.pop(tensor_name)

    def _clean_parameters(self):
        """Clean parameter cache."""
        for param in self._param_names:
            if param in self._tensors:
                self._tensors.pop(param)
                log.debug("Clean param %s in cache.", param)

    def get_tensors_diff(self, tensor_name, shape, tolerance=0):
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

        Raises:
            DebuggerParamValueError, If get current step node and previous step node failed or
                the type of tensor value is not numpy.ndarray."

        Returns:
            dict, the retrieved data.
        """
        curr_tensor = self.get_valid_tensor_by_name(tensor_name)
        prev_tensor = self.get_valid_tensor_by_name(tensor_name, prev=True)
        if not (curr_tensor and prev_tensor):
            log.error("Get current step and previous step for this tensor name %s failed.", tensor_name)
            raise DebuggerParamValueError(f"Get current step and previous step for this tensor name "
                                          f"{tensor_name} failed.")
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

    def get_tensor_info_for_tensor_graph(self, tensor_name, node_type):
        """
        Get Tensor info for tensor graphs.

        Args:
            tensor_name (str): Tensor name, format like `node_name:slot`.
            node_type (str): Node type.

        Returns:
            dict, tensor infos, including overall statistics, tensor shape and has_prev_step info.
            list, list of missing tensor basic information.
        """
        res = {}
        tensor = self._get_tensor(tensor_name, node_type)
        if tensor and not tensor.empty:
            res['statistics'] = tensor.get_tensor_statistics()
            res['shape'] = tensor.shape
        missing_tensors = self._update_has_prev_step_field(res, tensor_name, node_type)
        return res, missing_tensors
