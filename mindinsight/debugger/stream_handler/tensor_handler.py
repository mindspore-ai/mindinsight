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
import numpy as np

from mindinsight.datavisual.data_transform.graph.node import NodeTypeEnum
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.proto.ms_graph_pb2 import DataType
from mindinsight.debugger.stream_cache.tensor import OpTensor, ConstTensor
from mindinsight.debugger.stream_handler.base_handler import StreamHandlerBase
from mindinsight.utils.tensor import TensorUtils, TensorComparison


class TensorHandler(StreamHandlerBase):
    """Metadata Handler."""

    def __init__(self):
        self._const_vals = {}
        self._tensors = {}
        self._cur_step = 0

    def put(self, value):
        """
        Put value into tensor cache. Called by grpc server.

        Args:
            value (dict): The Tensor proto message.

                - step (int): The current step of tensor.

                - tensor_protos (list[TensorProto]): The tensor proto.

        Returns:
            bool, the tensor has updated successfully.
        """
        tensor_protos = value.get('tensor_protos')
        merged_tensor = self._get_merged_tensor(tensor_protos)
        step = value.get('step', 0)
        if merged_tensor.iter and step > 0:
            log.debug("Received previous tensor.")
            step -= 1
        tensor = OpTensor(merged_tensor, step)
        flag = self._put_tensor_into_cache(tensor, step)
        log.info("Put tensor %s of step: %d, into cache. Flag: %s", tensor.name, step, flag)
        return flag

    @staticmethod
    def _get_merged_tensor(tensor_protos):
        """
        Merged list of parsed tensor value into one.

        Args:
            tensor_protos (list[TensorProto]): List of tensor proto.

        Returns:
            TensorProto, merged tensor proto.
        """
        merged_tensor = tensor_protos[-1]
        if len(tensor_protos) > 1:
            tensor_value = bytes()
            for tensor_proto in tensor_protos:
                if not tensor_proto.tensor_content:
                    log.warning("Doesn't find tensor value for %s:%s",
                                tensor_proto.node_name, tensor_proto.slot)
                    break
                tensor_value += tensor_proto.tensor_content
            merged_tensor.tensor_content = tensor_value
            log.debug("Merge multi tensor values into one.")
        return merged_tensor

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
        if old_tensor and not self.is_value_diff(old_tensor.value, tensor.value):
            log.debug("Tensor %s of step %s has no change. Ignore it.")
            return False
        cache_tensor[step] = tensor
        log.debug("Put updated tensor value for %s of step %s.", tensor.name, step)
        return True

    @staticmethod
    def is_value_diff(old_value, new_value):
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
                tensor_proto.node_name = const_val.key
                tensor_proto.slot = '0'
                const_tensor = OpTensor(tensor_proto)
            else:
                const_tensor = ConstTensor(const_val)
            self._const_vals[const_tensor.name] = const_tensor

    def get(self, filter_condition=None):
        """
        Get full tensor value.

        Args:
            filter_condition (dict): Filter condition.

                - name (str): The name of tensor.

                - node_type (str): The type of the node.

        Returns:
            dict, the tensor_value.
        """
        name = filter_condition.get('name')
        node_type = filter_condition.get('node_type')
        shape = filter_condition.get('shape')
        tensor = self._get_tensor(name, node_type)
        if not tensor:
            log.error("No tensor named %s", name)
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
            step (int): The step of tensor info. Default: None. Noe

        Returns:
            Union[OPTensor, ConstTensor], the tensor object.
        """
        if step is None:
            step = self._cur_step
        tensor = self._tensors.get(tensor_name, {}).get(step)
        if not tensor and node_type == NodeTypeEnum.CONST.value:
            const_name = tensor_name.rsplit('/', 1)[-1]
            tensor = self._const_vals.get(const_name)
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
            flag = self._update_has_prev_step_field(basic_info, tensor_name, node_type)
            if flag is False:
                missed_tensor = tensor_info.copy()
                missed_tensor['iter'] = 'prev'
                missed_tensors.append(missed_tensor)
                log.debug("Add previous view cmd for %s", tensor_name)
            # add `has_prev_step` field to tensor basic info.
            if basic_info:
                tensor_info.update(basic_info)
                if not basic_info.get('value'):
                    missed_tensors.append(tensor_info)
                    log.debug("Add view cmd for %s", tensor_name)
            else:
                missed_tensors.append(tensor_info)
                log.debug("Add view cmd for %s", tensor_name)

        return missed_tensors

    def _update_has_prev_step_field(self, tensor_info, tensor_name, node_type):
        """Update has_prev_step field in tensor info."""
        flag = None
        if node_type == NodeTypeEnum.PARAMETER.value:
            flag = self._get_prev_tensor_value_status(tensor_name)
            if flag and tensor_info:
                tensor_info['has_prev_step'] = True
        return flag

    def _get_prev_tensor_value_status(self, tensor_name):
        """
        Get the status of tensor value of previous step.

        Args:
            tensor_name (str): Tensor name.

        Returns:
            Union[None, bool], the status of previous tensor value. If True, there is valid previous
                tensor value. If False, the tensor value should be queried from client.
                If None, ignore.
        """
        flag = None
        # check if the tensor has previous step value.
        prev_step = self._cur_step - 1
        if prev_step < 0:
            return flag
        tensor = self._get_tensor(tensor_name, step=prev_step)
        return bool(tensor and not tensor.empty)

    def get_tensor_value_by_name(self, tensor_name, prev=False):
        """Get tensor value by name in numpy type."""
        cur_step = self._cur_step
        step = cur_step - 1 if prev else cur_step
        if step < 0:
            log.warning("%d step has no previous value for tensor: %s", cur_step, tensor_name)
            return None
        tensor = self._get_tensor(tensor_name, step=step)

        return tensor

    def clean_tensors(self, cur_step):
        """Clean the tensor cache."""
        self._cur_step = cur_step
        expired_tensor = []
        for tensor_name, tensor in self._tensors.items():
            expired_step = [step for step in tensor.keys() if step <= cur_step - 2]
            for step in expired_step:
                tensor.pop(step)
            if not tensor:
                expired_tensor.append(tensor_name)
        for tensor_name in expired_tensor:
            self._tensors.pop(tensor_name)

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
        curr_tensor = self.get_tensor_value_by_name(tensor_name)
        prev_tensor = self.get_tensor_value_by_name(tensor_name, prev=True)
        if not (curr_tensor and prev_tensor):
            log.error("Get current step and previous step for this tensor name %s failed.", tensor_name)
            raise DebuggerParamValueError(f"Get current step and previous step for this tensor name "
                                          f"{tensor_name} failed.")
        curr_tensor_slice = curr_tensor.get_tensor_value_by_shape(shape)
        prev_tensor_slice = prev_tensor.get_tensor_value_by_shape(shape)
        tensor_info = curr_tensor.get_basic_info()
        if isinstance(tensor_info, dict):
            tensor_info.pop('has_prev_step')
            tensor_info.pop('value')

        tensor_comparison = curr_tensor.tensor_comparison
        if not tensor_comparison or tensor_comparison.tolerance != tolerance:
            if isinstance(curr_tensor.value, np.ndarray) and isinstance(prev_tensor.value, np.ndarray):
                tensor_diff = TensorUtils.calc_diff_between_two_tensor(curr_tensor.value, prev_tensor.value, tolerance)
                if not tensor_comparison:
                    stats = TensorUtils.get_statistics_from_tensor(tensor_diff)
                    tensor_comparison = TensorComparison(tolerance, stats, tensor_diff)
                    curr_tensor.update_tensor_comparisons(tensor_comparison)
                else:
                    tensor_comparison.update(tolerance=tolerance, value=tensor_diff)
            else:
                raise DebuggerParamValueError("The type of tensor value should be numpy.ndarray.")

        # the type of curr_tensor_slice is one of None, np.ndarray or str
        if isinstance(curr_tensor_slice, np.ndarray) and isinstance(prev_tensor_slice, np.ndarray):
            if not shape:
                tensor_diff_slice = tensor_comparison.value
            else:
                tensor_diff_slice = tensor_comparison.value[shape]
            result = np.stack([prev_tensor_slice, curr_tensor_slice, tensor_diff_slice], axis=-1)
            tensor_info['diff'] = result.tolist()
            stats = TensorUtils.get_statistics_from_tensor(tensor_diff_slice)
            tensor_info['statistics'] = TensorUtils.get_statistics_dict(stats=stats,
                                                                        overall_stats=tensor_comparison.stats)
        elif isinstance(curr_tensor_slice, str):
            tensor_info['diff'] = curr_tensor_slice
        reply = {'tensor_value': tensor_info}
        return reply
