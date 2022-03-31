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
# ==============================================================================
"""DebuggerTensor."""
import re
from abc import ABC

import numpy as np

from mindinsight.debugger.common.log import LOGGER as log
from mindinsight.debugger.common.utils import NUMPY_TYPE_MAP
from mindinsight.debugger.stream_cache.data_loader import DumpTarget
from mindinsight.domain.graph.base import NodeType
from mindinsight.domain.graph.proto.ms_graph_pb2 import DataType


class DebuggerTensor(ABC):
    """
    The tensor with specific rank, iteration and debugging info.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        node (Node): The node that outputs this tensor.
        slot (int): The slot of the tensor on the node.
        iteration (int): The iteration of the tensor.

    Note:
        - Users should not instantiate this class manually.
        - The instances of this class is immutable.
        - A `DebuggerTensor` is always the output tensor of a node.
    """

    def __init__(self, node, slot, iteration):
        self._node = node
        self._slot = slot
        self._iteration = iteration

    @property
    def node(self):
        """
        Get the node that outputs this tensor.

        Returns:
            Node, the node that outputs this tensor.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = list(my_run.select_tensors("conv"))
                >>> print(tensors[0].node)
                rank: 0
                graph_name: kernel_graph_0
                node_name: conv1.weight
        """
        return self._node

    @property
    def slot(self):
        """
        The output of the node may have several tensors. The slot refer to the index of the tensor

        Returns:
            int, the slot of the tensor on the node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = list(my_run.select_tensors("conv"))
                >>> print(tensors[0].slot)
                0
        """
        return self._slot

    @property
    def iteration(self):
        """
        Get iteration of the tensor.

        Returns:
            int, the iteration of the tensor.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = list(my_run.select_tensors("conv"))
                >>> print(tensors[0].iteration)
                0
        """
        return self._iteration

    @property
    def rank(self):
        """
        The rank is the logical id of the device on which the tensor is generated.

        Returns:
            int, the rank for this tensor.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> tensors = list(my_run.select_tensors("conv"))
                >>> print(tensors[0].rank)
                0
        """
        return self._node.rank

    def value(self):
        """
        Get the value of the tensor.

        Returns:
            Union[numpy.array, None], The value could be None if failed to find data file
            in relative iteration.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>>
                >>> def test_debugger_tensor():
                ...     my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                ...     tensors = list(my_run.select_tensors("conv"))
                ...     # the tensors[0].value() maybe start the new process
                ...     value = tensors[0].value()
                ...     return value
                ...
                >>> if __name__ == "__main__":
                ...     test_debugger_tensor()
                ...
        """
        raise NotImplementedError

    def __str__(self):
        feature = f"rank: {self.rank}\n" \
                  f"graph_name: {self.node.graph_name}\n" \
                  f"node_name: {self.node.name}\n" \
                  f"slot: {self.slot}\n" \
                  f"iteration: {self.iteration}"
        return feature


class DebuggerTensorImpl(DebuggerTensor):
    """DebuggerTensor implementation."""

    @property
    def root_graph_id(self):
        """Get the root_graph_id for this tensor."""
        return self._node.root_graph_id

    def has_value(self):
        """Check if the tensor has value."""
        iteration = self.iteration
        if iteration is None:
            return False
        data_loader = self.node.debugger_engine.data_loader
        has_dump_output = bool(data_loader.dump_target in [DumpTarget.FULL, DumpTarget.OUTPUT_ONLY])
        if not has_dump_output:
            return False
        if self.node.node_type == NodeType.CONSTANT:
            iteration = 'Constant'
        iter_dirs = data_loader.get_step_iter(rank_id=self.rank, step=iteration)
        file_found = self._file_found(iter_dirs)
        return file_found

    def _file_found(self, iter_dirs):
        """Check if the tensor file found in specified directory."""
        node_name_without_scope = self.node.name.split('/')[-1]
        bin_pattern = node_name_without_scope + r".*.(\d+)$"
        npy_pattern = f"{node_name_without_scope}.*.output.{self.slot}.*.npy$"
        for iter_dir in iter_dirs:
            for tensor_path in iter_dir.iterdir():
                file_name = tensor_path.name
                if re.search(bin_pattern, file_name) or re.search(npy_pattern, file_name):
                    return True
        return False

    def value(self):
        if self.iteration is None:
            log.warning("The iteration of is not specified, no value returned.")
            return None
        base_node = self.node.base_node
        if hasattr(base_node, 'output') and hasattr(base_node.output, 'info'):
            info = base_node.output.info
            if isinstance(info, dict) and info.get("np_value") is not None:
                return info.get("np_value")
        debugger_engine = self.node.debugger_engine
        tensor_info = debugger_engine.dbg_services_module.TensorInfo(
            node_name=base_node.full_name if self.node.node_type == NodeType.CONSTANT else self.node.name,
            slot=self.slot,
            iteration=self.iteration,
            rank_id=self.rank,
            root_graph_id=self.root_graph_id,
            is_output=True)
        tensors = debugger_engine.dbg_service.read_tensors([tensor_info])
        return self._to_numpy(tensors[0])

    @staticmethod
    def _to_numpy(tensor_data):
        """Turn tensor data into Numpy."""
        if tensor_data.data_size == 0:
            return None
        dtype_str = DataType.Name(tensor_data.dtype)
        np_type = NUMPY_TYPE_MAP.get(dtype_str)
        data = np.frombuffer(tensor_data.data_ptr, dtype=np_type)
        data = data.reshape(tensor_data.shape)
        return data
