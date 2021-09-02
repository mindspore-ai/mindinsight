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
"""The definition of tensor stream."""
from abc import abstractmethod, ABC
from enum import Enum

import numpy as np

from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import NUMPY_TYPE_MAP, MAX_SINGLE_TENSOR_CACHE_BYTES
from mindinsight.domain.graph.proto.ms_graph_pb2 import DataType
from mindinsight.utils.tensor import TensorUtils

NPY_HEADER_LENGTH = 128


class TensorStatusEnum(Enum):
    """Tensor status."""
    CACHED = "cached"
    UNCACHED = "uncached"
    EMPTY = 'empty'
    OVERSIZE = "oversize"


class DownloadStatusEnum(Enum):
    """Tensor status."""
    PENDING = "pending"
    SENDING = "sending"


class BaseTensor(ABC):
    """Tensor data structure."""

    def __init__(self, step=0):
        self._step = step
        self._stats = None

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
        """The property of tensor value."""

    @property
    @abstractmethod
    def download_size(self):
        """The property of download size."""

    @property
    @abstractmethod
    def status(self):
        """The property of tensor status."""

    @property
    def empty(self):
        """If the tensor value is valid."""
        return self.value is None

    @property
    def stats(self):
        """The property of tensor stats."""
        return self._stats

    @stats.setter
    def stats(self, stats):
        """
        Update tensor stats.

        Args:
            stats (Statistics): Instance of Statistics.
        """
        self._stats = stats

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
        # the type of tensor_value is one of None, np.ndarray or str
        if isinstance(tensor_value, np.ndarray):
            res['value'] = tensor_value.tolist()
        else:
            res['value'] = tensor_value
        res['statistics'] = self.get_tensor_statistics()
        return res

    @abstractmethod
    def get_tensor_value_by_shape(self, shape=None):
        """Abstract method."""

    @abstractmethod
    def get_tensor_statistics(self):
        """Abstract method."""

    def _to_dict(self):
        """Get tensor info in dict format."""
        res = {
            'full_name': self.name,
            'step': self._step,
            'dtype': self.dtype,
            'shape': self.shape,
            'bytes': self.download_size,
            'tensor_status': self.status,
            'has_prev_step': False
        }
        return res

    def get_basic_info(self):
        """Return basic info about tensor info."""
        if self.status == TensorStatusEnum.EMPTY.value:
            value = None
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
    """
    Tensor data structure for operator Node.

    Args:
        tensor_proto (TensorProto): Tensor proto contains tensor basic info.
        tensor_content (byte): Tensor content value in byte format.
        step (int): The step of the tensor.
    """
    max_number_data_show_on_ui = 100000

    def __init__(self, name, tensor_base=None, tensor_stats=None, tensor_content=None, step=0):
        # the type of tensor_proto is TensorProto
        super(OpTensor, self).__init__(step)
        self._name = name
        self._tensor_base = tensor_base
        self._shape = tensor_base.get('shape') if tensor_base else []
        self._value = self.to_numpy(tensor_content)
        self._download_size = tensor_base.get('data_size') + NPY_HEADER_LENGTH if tensor_base else 0
        self._stats = tensor_stats
        self._tensor_comparison = None
        self._status = self.get_status()

    @property
    def name(self):
        """The property of tensor name."""
        return self._name

    @property
    def tensor_base(self):
        """The property of tensor base."""
        return self._tensor_base

    @property
    def step(self):
        """The step of the tensor value."""
        return self._step

    @property
    def dtype(self):
        """The property of tensor dtype."""
        return DataType.Name(self._tensor_base.get('dtype') if self._tensor_base else 0)

    @property
    def shape(self):
        """The property of tensor shape."""
        dims = list(self._shape)
        if dims == [0]:
            dims = []
        return dims

    @property
    def value(self):
        """The property of tensor value."""
        return self._value

    @property
    def nbytes(self):
        """The property of tensor value."""
        return self._value.nbytes if self._value is not None else 0

    @property
    def download_size(self):
        """The property of download size."""
        return self._download_size

    @property
    def status(self):
        """The property of tensor status."""
        return self._status

    @property
    def tensor_comparison(self):
        """The property of tensor_comparison."""
        return self._tensor_comparison

    def get_status(self):
        """Set the tensor status."""
        res = TensorStatusEnum.EMPTY.value if self.tensor_base is None or self.tensor_base.get(
            'data_size') == 0 else TensorStatusEnum.OVERSIZE.value if self.tensor_base.get(
                'data_size') >= MAX_SINGLE_TENSOR_CACHE_BYTES else TensorStatusEnum.UNCACHED.value
        return res if self.value is None else TensorStatusEnum.CACHED.value

    def calculate_stats(self):
        """Calculate the tensor statistics."""
        self._stats = TensorUtils.get_statistics_from_tensor(self._value)

    def clean_tensor_value(self, oversize=True, remain_scalar=False):
        """Clean the tensor."""
        if oversize:
            self._status = TensorStatusEnum.OVERSIZE.value
        if remain_scalar and not self.shape and self._status != TensorStatusEnum.EMPTY.value:
            return
        self._value = None
        if self._status == TensorStatusEnum.CACHED.value:
            self._status = TensorStatusEnum.UNCACHED.value

    def to_numpy(self, tensor_content):
        """
        Construct tensor content from byte to numpy.

        Args:
            tensor_content (byte): The tensor content.

        Returns:
            Union[None, np.ndarray], the value of the tensor.
        """
        tensor_value = None
        if tensor_content:
            np_type = NUMPY_TYPE_MAP.get(self.dtype)
            tensor_value = np.frombuffer(tensor_content, dtype=np_type)
            tensor_value = tensor_value.reshape(self.shape)
        return tensor_value

    def get_tensor_statistics(self):
        """
        Get Tensor statistics.

        Returns:
            dict, overall statistics.
        """
        if self.stats:
            return TensorUtils.get_overall_statistic_dict(self.stats)
        if self.empty:
            return {}
        self.stats = TensorUtils.get_statistics_from_tensor(self.value)
        return TensorUtils.get_overall_statistic_dict(self.stats)

    def update_tensor_comparisons(self, tensor_comparison):
        """
        Update tensor comparison for tensor.

        Args:
            tensor_comparison (TensorComparison) instance of TensorComparison.

        """
        self._tensor_comparison = tensor_comparison

    def get_tensor_value_by_shape(self, shape=None):
        """
        Get tensor value by shape.

        Args:
            shape (tuple): The specified shape.

        Returns:
            Union[None, str, numpy.ndarray], the value of parsed tensor.
        """
        if self._status == TensorStatusEnum.OVERSIZE.value:
            log.info("%s is too large to show on UI.", self.name)
            return "Too large to show on UI."
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
                log.info("The tensor size is %d, which is too large to show on UI.", value.size)
                value = "Too large to show."
        else:
            value = np.asarray(value)
        return value


class ConstTensor(BaseTensor):
    """Tensor data structure for Const Node."""
    _STRING_TYPE = 'DT_STRING'
    _DT_TYPE = 'DT_TYPE'

    def __init__(self, const_proto):
        # the type of const_proto is NamedValueProto
        super(ConstTensor, self).__init__()
        self._const_proto = const_proto
        self._value = self.generate_value_from_proto(const_proto.value)
        self._status = TensorStatusEnum.CACHED.value if self._value is not None else TensorStatusEnum.EMPTY.value
        self._stats = None
        self.tensor_base = None

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
        return self._value

    @property
    def status(self):
        """The property of tensor status."""
        return self._status

    @property
    def download_size(self):
        """The property of download size."""
        # cannot download the const value, so the the download size is 0
        return 0

    def generate_value_from_proto(self, tensor_proto):
        """
        Generate tensor value from proto.

        Args:
            tensor_proto (TensorProto): The tensor proto.

        Returns:
            Union[None, str, np.ndarray], the value of the tensor.
        """
        fields = tensor_proto.ListFields()
        if len(fields) != 2:
            log.warning("Unexpected const proto <%s>.\n Please check offline.", tensor_proto)
        tensor_value = None
        for field_obj, field_value in fields:
            if field_obj.name != 'dtype':
                if tensor_proto.dtype == DataType.DT_TUPLE:
                    tensor_values = []
                    for field_value_element in field_value:
                        value_element = self.generate_value_from_proto(field_value_element)
                        tensor_values.append(value_element)
                    tensor_value = tensor_values
                elif tensor_proto.dtype == DataType.DT_TYPE:
                    tensor_value = DataType.Name(field_value.data_type)
                else:
                    tensor_value = field_value
                break
        if tensor_value is not None and tensor_proto.dtype != self._STRING_TYPE:
            tensor_value = np.array(tensor_value, dtype=NUMPY_TYPE_MAP.get(tensor_proto.dtype))
        return tensor_value

    def get_tensor_value_by_shape(self, shape=None):
        """
        Get tensor value by shape.

        Args:
            shape (tuple): The specified shape.

        Returns:
            Union[None, str, int, float], the value of parsed tensor.
        """
        if shape:
            log.warning("Invalid shape for const value.")
        return self._value

    def calculate_stats(self):
        """Calculate the tensor statistics."""
        if not (self.empty or self.dtype == self._STRING_TYPE or self.dtype == self._DT_TYPE):
            self._stats = TensorUtils.get_statistics_from_tensor(self._value)

    def get_tensor_statistics(self):
        """
        Get Tensor statistics.

        Returns:
            dict, overall statistics.
        """
        self.calculate_stats()
        if self.empty or self.dtype == self._STRING_TYPE or self.dtype == self._DT_TYPE:
            log.debug("The tensor dtype is: %s, skip getting statistics.", self.dtype)
            return {}
        statistics = TensorUtils.get_overall_statistic_dict(self._stats)
        return statistics
