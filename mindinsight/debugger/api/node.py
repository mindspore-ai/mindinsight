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
"""Node in the computational graph."""
import collections
from abc import ABC

from mindinsight.debugger.api.debugger_tensor import DebuggerTensorImpl
from mindinsight.debugger.common.exceptions.exceptions import DebuggerParamValueError
from mindinsight.debugger.common.utils import validate_slots, parse_param_to_iterable_obj
from mindinsight.domain.graph.base import NodeType

NodeFeature = collections.namedtuple('NodeFeature', ['name', 'rank', 'stack',
                                                     'graph_name', 'root_graph_id'])
NodeUniqueId = collections.namedtuple('NodeUniqueId', ['name', 'rank', 'graph_name'])


class Node(ABC):
    """
    Node in the computational graph.

    .. warning::
        All APIs in this class are experimental prototypes that are subject to
        change or deletion.

    Args:
        node_feature (namedtuple): The node feature, including the following information:

            - name (str): The node name.
            - rank (int): The rank id.
            - stack (iterable[dict]): The stack information. The format of each item is like:

              .. code-block::

                  {
                      'file_path': str,
                      'line_no': int,
                      'code_line': str
                  }

            - graph_name (str): The graph name.
            - root_graph_id (int): The root graph id.

    Note:
        - Users should not instantiate this class manually.
        - The instances of this class is immutable.
    """

    def __init__(self, node_feature):
        self._node_feature = node_feature

    @property
    def name(self):
        """
        Get the full name of this node.

        Returns:
            str, the full name of the node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node = list(my_run.select_nodes("conv"))[0]
                >>> print(node.name)
                conv1.weight
        """
        return self._node_feature.name

    @property
    def stack(self):
        """
        Get stack info of the node.

        Returns:
            iterable[dict], each item format as follows,

            .. code-block::

                {
                    'file_path': str,
                    'line_no': int,
                    'code_line': str
                }

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node = list(my_run.select_nodes("Conv2D-op13"))[0]
                >>> # print(node.stack)
                >>> # the print result is as follows
                >>> # [{'file_path': '/path', 'line_no': 266, 'code_line': 'output = self.conv2d(x, self.weight)',
                >>> # 'has_substack': False},
                >>> # {'file_path': '/path', 'line_no': 55, 'code_line': 'x = self.conv2(x), 'has_substack': False}]
        """
        return self._node_feature.stack

    @property
    def rank(self) -> int:
        """
        Get rank info.

        Returns:
            int, the rank id to which the node belong.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node = list(my_run.select_nodes("conv"))[0]
                >>> print(node.rank)
                0
        """
        return self._node_feature.rank

    @property
    def root_graph_id(self) -> int:
        """
        Get the root graph id to which the dumped tensor of current node will belong.

        Returns:
            int, the root graph id.
        """
        return self._node_feature.root_graph_id

    @property
    def graph_name(self) -> str:
        """
        Get graph name of current node.

        Returns:
            str, the graph name.
        """
        return self._node_feature.graph_name

    def get_input_tensors(
            self,
            iterations=None,
            slots=None):
        """
        Get the input tensors of the node.

        Args:
            iterations (Iterable[int], optional): The iterations to which the returned
                tensor should belong. ``None`` means all available iterations will be considered.
                Default: ``None``.
            slots (Iterable[int], optional): The slots in which the returned tensors
                should be. ``None`` means all available slots will be considered. Default: ``None``.

        Returns:
            Iterable[DebuggerTensor], the input tensors of the node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node = list(my_run.select_nodes("Conv2D-op13"))[0]
                >>> input_tensors = node.get_input_tensors(iterations=[0], slots=[0])
        """

    def get_output_tensors(
            self,
            iterations=None,
            slots=None):
        """
        Get the output tensors of this node.

        Args:
            iterations (Iterable[int], optional): The iterations to which the returned
                tensor should belong. ``None`` means all available iterations will be considered.
                Default: ``None``.
            slots (Iterable[int], optional): The slots in which the returned tensors
                should be. ``None`` means all available slots will be considered. Default: ``None``.

        Returns:
            Iterable[DebuggerTensor], the output tensors of the node.

        Examples:
                >>> from mindinsight.debugger import DumpAnalyzer
                >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
                >>> node = list(my_run.select_nodes("Conv2D-op13"))[0]
                >>> output_tensors = node.get_output_tensors(iterations=[0], slots=[0])
        """

    def __str__(self):
        feature = f"rank: {self.rank}\n" \
                  f"graph_name: {self.graph_name}\n" \
                  f"node_name: {self.name}"
        return feature


class NodeImpl(Node):
    """Node implementation."""

    def __init__(self, base_node, node_type):
        self._base_node = base_node
        self._node_type = node_type
        node_feature = self._get_node_feature()
        super(NodeImpl, self).__init__(node_feature)
        self.debugger_engine = None
        self.input_nodes = []
        self.downstream = []

    @property
    def name(self):
        """
        Get the full name of this node.

        Returns:
            str, the full name of the node.

        Examples:
            >>> from mindinsight.debugger import DumpAnalyzer
            >>> my_run = DumpAnalyzer(dump_dir="/path/to/your/dump_dir_with_dump_data")
            >>> node = list(my_run.select_nodes("conv"))[0]
            >>> print(node.name)
            conv1.weight
        """
        if hasattr(self._base_node, 'type') and (self._base_node.type == "Load" or "Summary" in self._base_node.type):
            name = self._base_node.name.split('/')[-1]
            node_id = name.split('op')[-1]
            name = f'{self._base_node.type}-op{node_id}'
            return f'{self._base_node.scope}/{name}'
        return self._node_feature.name

    @property
    def node_type(self):
        """Get the node type."""
        return self._node_type

    @property
    def base_node(self):
        """Get the base node."""
        return self._base_node

    @property
    def output_slot_size(self):
        """Get the base node."""
        return self._base_node.output.slot_size

    @property
    def full_name_with_graph(self):
        """Return node name startswith graph name."""
        return f"{self.graph_name}/{self.name}"

    @property
    def unique_id(self):
        """Get the unique id of the node."""
        return NodeUniqueId(self.name, self.rank, self.graph_name)

    def _get_node_feature(self):
        """Get node feature."""
        node = self._base_node
        if self._node_type in (NodeType.CONSTANT, NodeType.PARAMETER):
            feature = NodeFeature(name=node.name,
                                  rank=node.rank_id,
                                  stack=[],
                                  graph_name=node.graph_name,
                                  root_graph_id=node.root_graph_id)
        elif self._node_type == NodeType.OPERATOR:
            feature = NodeFeature(name=node.full_name,
                                  rank=node.rank_id,
                                  stack=node.stack,
                                  graph_name=node.graph_name,
                                  root_graph_id=node.root_graph_id)
        else:
            raise DebuggerParamValueError(f"Invalid node_type, got {self._node_type}")
        return feature

    def get_input_tensors(
            self,
            iterations=None,
            slots=None):
        """
        Get the input tensors of the node.

        Args:
            iterations (Iterable[int], optional): The iterations to which the returned
                tensor should belong. ``None`` means all available iterations will be considered.
                Default: ``None``.
            slots (Iterable[int], optional): The slots in which the returned tensors
                should be. ``None`` means all available slots will be considered. Default: ``None``.

        Returns:
            Iterable[DebuggerTensor], the input tensors of the node.
        """
        validate_slots(slots)
        iterations = self._get_iterable_iterations(iterations)
        current_index = 0
        res = []
        for node in self.input_nodes:
            if slots is not None:
                query_slots = [slot for slot in range(node.output_slot_size) if slot + current_index in slots]
            else:
                query_slots = None
            res.extend(node.get_output_tensors(iterations, query_slots))
            current_index += node.output_slot_size
        return res

    def get_output_tensors(
            self,
            iterations=None,
            slots=None):
        """
        Get the output tensors of this node.

        Args:
            iterations (Iterable[int]): The iterations to which the returned
                tensor should belong. Default: ``None``.
            slots (Iterable[int]): The slots in which the returned tensors
                should be. Default: ``None``.

        Returns:
            Iterable[DebuggerTensor], the output tensors of the node.
        """
        validate_slots(slots)
        iterations = self._get_iterable_iterations(iterations)
        output_slots = list(range(self.output_slot_size))
        if slots is None:
            query_slots = output_slots
        else:
            query_slots = [slot for slot in output_slots if slot in slots]
        res = []
        for slot in query_slots:
            for iteration in iterations:
                res.append(DebuggerTensorImpl(self.copy(), slot, iteration))
        return res

    def _get_iterable_iterations(self, iterations):
        """
        Validate input and return iterable iterations.

        Args:
           iterations (Union[int, list[int], None], optional): The specified iterations.

        Returns:
            list[int], list of iteration.
        """
        data_loader = self.debugger_engine.data_loader
        total_dumped_steps = data_loader.load_dumped_step(self.rank)
        dumped_iterations = total_dumped_steps.get(self.rank, {}).get(self.root_graph_id, [])
        iterations = parse_param_to_iterable_obj(iterations, 'iterations', dumped_iterations, False)
        return iterations

    def copy(self):
        """Copy Node."""
        node = NodeImpl(self._base_node, self._node_type)
        node.debugger_engine = self.debugger_engine
        node.input_nodes = self.input_nodes.copy()
        node.downstream = self.downstream.copy()
        return node
