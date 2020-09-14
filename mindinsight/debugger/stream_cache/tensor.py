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
"""The definition of tensor stream."""
from abc import abstractmethod, ABC

import numpy as np

from mindinsight.utils.tensor import TensorUtils
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import logger as log
from mindinsight.debugger.common.utils import NUMPY_TYPE_MAP
from mindinsight.debugger.proto.ms_graph_pb2 import DataType


class BaseTensor(ABC):
    """Tensor data structure."""

    def __init__(self, step=0):
        self._step = step

    @property
    @abstractmethod
    def name(self):
        """The property of tensor name."""

    @property
    @abstractmethod
    def dtype(self):
        """The property of tensor dtype."""

    @property
    @abstractmethod
    def shape(self):
        """The property of tensor shape."""

    @property
    @abstractmethod
    def value(self):
        """The property of tensor shape."""

    @abstractmethod
    def get_tensor_value_by_shape(self, shape=None):
        """Get tensor value by shape."""

    def _to_dict(self):
        """Get tensor info in dict format."""
        res = {
            'full_name': self.name,
            'step': self._step,
            'dtype': self.dtype,
            'shape': self.shape,
            'has_prev_step': False
        }
        return res

    def get_basic_info(self):
        """Return basic info about tensor info."""
        if not self.shape:
            value = self.value
        else:
            value = 'click to view'
        res = self._to_dict()
        res['value'] = value
        return res

    def get_full_info(self, shape=None):
        """Get tensor info with value."""
        res = self._to_dict()
        value_info = self.get_tensor_serializable_value_by_shape(shape)
        res.update(value_info)
        return res


class OpTensor(BaseTensor):
    """Tensor data structure for operator Node."""
    max_number_data_show_on_ui = 100000

    def __init__(self, tensor_proto, step=0):
        # the type of tensor_proto is TensorProto
        super(OpTensor, self).__init__(step)
        self._tensor_proto = tensor_proto
        self._value = self.generate_value(tensor_proto)

    @property
    def name(self):
        """The property of tensor name."""
        node_name = self._tensor_proto.node_name
        slot = self._tensor_proto.slot
        return ':'.join([node_name, slot])

    @property
    def dtype(self):
        """The property of tensor dtype."""
        tensor_type = DataType.Name(self._tensor_proto.data_type)

        return tensor_type

    @property
    def shape(self):
        """The property of tensor shape."""
        return list(self._tensor_proto.dims)

    @property
    def value(self):
        """The property of tensor value."""
        tensor_value = None
        if self._value is not None:
            tensor_value = self._value.tolist()

        return tensor_value

    @property
    def numpy_value(self):
        """The property of tensor value in numpy type."""
        return self._value

    def generate_value(self, tensor_proto):
        """Generate tensor value from proto."""
        tensor_value = None
        if tensor_proto.tensor_content:
            tensor_value = tensor_proto.tensor_content
            np_type = NUMPY_TYPE_MAP.get(self.dtype)
            tensor_value = np.frombuffer(tensor_value, dtype=np_type)
            tensor_value = tensor_value.reshape(self.shape)
        return tensor_value

    def get_tensor_serializable_value_by_shape(self, shape=None):
        """
        Get tensor value info by shape.

        Args:
            shape (tuple): The specified range of tensor value.

        Returns:
            dict, the specified tensor value and value statistics.
        """
        tensor_value = self.get_tensor_value_by_shape(shape)
        res = {}
        if isinstance(tensor_value, np.ndarray):
            statistics = TensorUtils.get_statistics_from_tensor(tensor_value)
            res['statistics'] = TensorUtils.get_statistics_dict(statistics)
            res['value'] = tensor_value.tolist()
        elif isinstance(tensor_value, str):
            res['value'] = tensor_value

        return res

    def get_tensor_value_by_shape(self, shape=None):
        """
        Get tensor value by shape.

        Args:
            shape (tuple): The specified shape.

        Returns:
            Union[None, str, numpy.ndarray], the sub-tensor.
        """
        if self._value is None:
            log.warning("%s has no value yet.", self.name)
            return None
        if shape is None or not isinstance(shape, tuple):
            log.info("Get the whole tensor value with shape is %s", shape)
            return self._value
        if len(shape) != len(self.shape):
            log.error("Invalid shape. Received: %s, tensor shape: %s", shape, self.shape)
            raise DebuggerParamValueError("Invalid shape. Shape unmatched.")
        try:
            value = self._value[shape]
        except IndexError as err:
            log.error("Invalid shape. Received: %s, tensor shape: %s", shape, self.shape)
            log.exception(err)
            raise DebuggerParamValueError("Invalid shape. Shape unmatched.")
        if isinstance(value, np.ndarray):
            if value.size > self.max_number_data_show_on_ui:
                value = "Too large to show."
                log.info("The tensor size is %s, which is too large to show on UI.")
        else:
            value = np.asarray(value)
        return value


class ConstTensor(BaseTensor):
    """Tensor data structure for Const Node."""

    def __init__(self, const_proto):
        # the type of const_proto is NamedValueProto
        super(ConstTensor, self).__init__()
        self._const_proto = const_proto

    def set_step(self, step):
        """Set step value."""
        self._step = step

    @property
    def name(self):
        """The property of tensor name."""
        return self._const_proto.key + ':0'

    @property
    def dtype(self):
        """The property of tensor dtype."""
        return DataType.Name(self._const_proto.value.dtype)

    @property
    def shape(self):
        """The property of tensor shape."""
        return []

    @property
    def value(self):
        """The property of tensor shape."""
        fields = self._const_proto.value.ListFields()
        if len(fields) != 2:
            log.warning("Unexpected const proto <%s>.\n Please check offline.", self._const_proto)
        for field_name, field_value in fields:
            if field_name != 'dtype':
                return field_value
        return None

    def get_tensor_value_by_shape(self, shape=None):
        """Get tensor info with value."""
        if shape is not None:
            log.warning("Invalid shape for const value.")
        return self.value
