# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Define graph entity."""
import abc
from collections import OrderedDict

from typing import List

from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.graph_based_converter.constant import InputType
from mindinsight.mindconverter.common.exceptions import NodeInputTypeNotSupportError


class GraphParser(metaclass=abc.ABCMeta):
    """Graph parser."""

    @classmethod
    @abc.abstractmethod
    def parse(cls, model_path: str, **kwargs):
        """Parse graph into readable format."""


class BaseGraph(metaclass=abc.ABCMeta):
    """Define basic graph."""
    _REQUIRED_PARAM_OF_MODEL = "model"

    @abc.abstractmethod
    def build(self):
        """Build graph."""

    @abc.abstractmethod
    def sub_graph_merging(self):
        """Merge split nodes into one."""

    @staticmethod
    @abc.abstractmethod
    def load_checkpoint(ckpt_path: str) -> dict:
        """Load checkpoint file."""

    @staticmethod
    @abc.abstractmethod
    def load_metadata(**kwargs):
        """Load graph metadata."""

    @staticmethod
    @abc.abstractmethod
    def load_graph(graph_path: str, **kwargs):
        """Load graph file."""

    @classmethod
    @abc.abstractmethod
    def load(cls, model_path: str, **kwargs):
        """Factory method to initialize an graph object."""

    def __new__(cls, *args, **kwargs):
        """Control the create action of graph."""
        model_param = args[0] if args else kwargs.get(
            cls._REQUIRED_PARAM_OF_MODEL)
        if not model_param:
            error = ValueError(f"`{cls._REQUIRED_PARAM_OF_MODEL}` "
                               f"can not be None.")
            log.error(str(error))
            log.exception(error)
            raise error

        return super(BaseGraph, cls).__new__(cls)


class Graph(BaseGraph, abc.ABC):
    """
    Define Factory method to create Graph sub-class.

    Args:
        model (Union[torch.nn.Module, Any]): Graph file.
        checkpoint (dict): Checkpoint path.

    """

    sorted = False

    def __init__(self, model, **kwargs):
        super(Graph, self).__init__()
        self.model = model
        self._raw_input_nodes = kwargs.get("input_nodes")
        self._raw_output_nodes = kwargs.get("output_nodes")
        self._nodes_collection = OrderedDict()
        self._nodes_record = dict()
        self._shape_dict = dict()
        self._input_nodes = []
        self._output_nodes = []
        self._topological_order = []
        self._input_shape = dict()
        self._is_multi_opt_graph = False

    @property
    def user_provided_input_nodes(self) -> List[str]:
        """User provided input_nodes in CLI."""
        return list(self._raw_input_nodes.keys())

    def get_input_shape(self, name):
        """
        Get node input shape.

        Args:
            name (str): Node name.

        Returns:
            Union[list, int], shape.
        """
        return self._input_shape.get(name)

    def get_output_shape(self, name):
        """
        Get node output shape.

        Args:
            name (str): Node name.

        Returns:
            Union[list, int],
        """
        return self._shape_dict.get(name)

    def get_input_shape_from_input(self, name):
        """
        Get node input shape.

        Returns:
            list, shape.
        """
        return self._input_shape.get(name)

    @property
    def nodes_in_topological_order(self):
        """
        Return nodes in topological order.

        Returns:
            List[GraphNode], nodes.
        """
        if not self.sorted:
            self._topological_sort()
        return self._topological_order

    def _reset_topological_order(self):
        """
        Reset topological order queue.
        """
        self._topological_order = self._input_nodes[:]
        self.sorted = False

    def get_node(self, node_name):
        """
        Get node reference.

        Args:
            node_name (str): Node name.

        Returns:
            GraphNode, node instance.
        """
        prefix = node_name.split(":")[0]
        if prefix not in self._nodes_collection:
            return None
        return self._nodes_collection[prefix]

    def build(self):
        """Build graph."""
        # Collect input nodes and output nodes.
        self._collect_ipt_and_opt_nodes()
        # Use topological sort to solve nodes order.
        self._topological_sort()

    def _collect_ipt_and_opt_nodes(self):
        """
        Collect input and output nodes in model.
        """
        for name, node in self._nodes_collection.items():
            if node.in_degree == 0:
                self._input_nodes.append(name)

            if node.out_degree == 0:
                self._output_nodes.append(name)

    def _topological_sort(self):
        """Topological sort to arrange nodes order."""
        self._reset_topological_order()

        def is_connected(src, dst):
            """Judge two node whether are connected."""
            for precursor in dst.precursor_nodes:
                if src == precursor.split(":")[0]:
                    return 1
            return 0

        idx = 0
        while idx < len(self._topological_order):
            cur_node_name = self._topological_order[idx]
            cur_node = self.get_node(cur_node_name)
            # `scsr` is abbreviation for `successor`.
            for scsr_name in cur_node.successor_nodes:
                scsr_node = self.get_node(scsr_name)
                scsr_node.cur_in_degree -= is_connected(cur_node_name,
                                                        scsr_node)
                if scsr_node.cur_in_degree == 0:
                    self._topological_order.append(scsr_name)
            idx += 1
        self.sorted = True

    def sub_graph_merging(self):
        raise NotImplementedError

    @staticmethod
    def load_checkpoint(ckpt_path: str) -> dict:
        raise NotImplementedError

    @staticmethod
    def load_metadata(**kwargs):
        raise NotImplementedError

    @staticmethod
    def load_graph(graph_path: str, **kwargs):
        raise NotImplementedError

    @classmethod
    def load(cls, model_path: str, **kwargs) -> BaseGraph:
        """
        Load third party graph.

        Args:
            model_path (str): Graph or model file path.

        Returns:
            cls, graph instance.
        """
        src_graph = cls.load_graph(graph_path=model_path, **kwargs)
        return cls(src_graph, **kwargs)


class GraphNode(abc.ABC):
    """
    Graph node.

    Args:
        node (torch._C.Node): PyTorch node.

    """
    transformed = False

    def __init__(self, node):
        # Store the edge from precursor.
        self.precursor_nodes = []
        # Store the edge to successor.
        self.successor_nodes = []
        # Control dependency.
        self._deleted_in_edge = 0
        # Source node in ONNX.
        self._src_node = node if node else None
        # Original operation name in ONNX.
        self._op_name = None
        self._op_params = dict()
        self._scope_name = None
        self._op_shape = None
        # Node type of current node, e.g. class, module, operation.
        self._node_type = None
        # Function, class or operation needed args.
        self._args_in_code = dict()
        # Unique key of node.
        self._hash_key = None
        # Input shape of current op.
        self._ipt_shape = None
        # Output shape of current op.
        self._opt_shape = None
        # Weight of current op.
        self._weight = None
        # Input variable names.
        self._ipt_var_names = list()
        # Output variable names.
        self._opt_var_names = list()
        # Is in multi output graph.
        self._is_in_multi_opt_graph = False

    @property
    def ir_node_name(self):
        """Getter of ir node's name."""
        return self._src_node.name

    @property
    def ir_node_operation(self):
        """Getter of ir node's operation."""
        return self._src_node.op_type

    @property
    def ir_node_inputs(self):
        """Getter of ir node's inputs."""
        return list(self._src_node.input_name_list)

    @property
    def ir_node_outputs(self):
        """Getter of ir node's outputs."""
        return list(self._src_node.output_name_list)

    @property
    def ir_node_precursor(self):
        """Getter of ir node's precursor."""
        return [
            v.name for _, v in self._src_node.precursor_onnx_node_dict.items()
        ]

    @property
    def ir_node_successor(self):
        """Getter of ir node's successor."""
        return [
            v.name for _, v in self._src_node.successor_onnx_node_dict.items()
        ]

    @property
    def weight(self):
        return self._weight

    @property
    def ipt_var_names(self):
        return self._ipt_var_names

    @ipt_var_names.setter
    def ipt_var_names(self, var_names):
        self._ipt_var_names = var_names

    @property
    def opt_var_names(self):
        return self._opt_var_names

    @opt_var_names.setter
    def opt_var_names(self, var_names):
        self._opt_var_names = var_names

    @staticmethod
    def get_opt_var_name(variable_name):
        """
        Output variable name.

        Returns:
            str, variable name.
        """
        return f"{variable_name}_opt"

    @property
    def args_in_code(self):
        """
        Args in code.

        Returns:
            dict, args.
        """
        return self._args_in_code

    @args_in_code.setter
    def args_in_code(self, args):
        """
        Setter for args_in_code.

        Args:
            args (dict): Args.

        """
        self._args_in_code = args

    @property
    def input_shape(self):
        """
        Input tensor shape of current node.

        Returns:
            tuple, tensor shape of input.
        """
        return self._ipt_shape

    @property
    def output_shape(self):
        """
        Output tensor shape.

        Returns:
            tuple, output tensor shape.
        """
        return self._opt_shape

    def is_empty(self):
        """
        Whether is empty.

        Returns:
            bool, true or false.
        """
        return not self._src_node

    @property
    def node_type(self):
        """Get node type (ONNX op type)."""
        return self._node_type

    @node_type.setter
    def node_type(self, m):
        """
        Setter of node_type.

        Args:
            m (str): Node type.

        """
        self._node_type = m

    @property
    def scope_name(self):
        """
        Scope name.

        Returns:
            str, scope name.
        """
        return self._scope_name

    @scope_name.setter
    def scope_name(self, name):
        """
        Setter of scope name.

        Args:
            name(str): Scope name.

        """
        self._scope_name = name

    @property
    def node_params(self):
        """Get node params (ONNX op params)."""
        return self._op_params

    @property
    def cur_in_degree(self):
        """
        Current in-degree.

        Returns:
            int, current in-degree.
        """
        return self.in_degree - self._deleted_in_edge

    @cur_in_degree.setter
    def cur_in_degree(self, e):
        """
        Setter of cur_in_degree.

        Args:
            e (int): To be update value.

        """
        self._deleted_in_edge += self.cur_in_degree - e

    @property
    def in_degree(self):
        """
        Define in-degree.

        Returns:
            int, in-degree.
        """
        return len(self.precursor_nodes)

    @property
    def out_degree(self):
        """
        Define out-degree.

        Returns:
            int, out-degree.
        """
        return len(self.successor_nodes)

    @property
    @abc.abstractmethod
    def hash_key(self):
        """
        Generate unique hash key for each node.

        Use topological order as key.
        """

    @abc.abstractmethod
    def _get_raw_params(self, node):
        """Get params in onnx."""

    @property
    @abc.abstractmethod
    def op_name(self):
        """Return op_name."""

    @abc.abstractmethod
    def replace_with_arg(self, src_arg, tgt_arg):
        """Replace actual parameter with formal parameter."""

    @abc.abstractmethod
    def _get_arg_name(self, arg, variable_name):
        """Get arg name for func or class."""

    @abc.abstractmethod
    def clear_args_of_declaration(self):
        """Clear `_args_in_code`."""

    @property
    @abc.abstractmethod
    def real_name(self):
        """Getter of `real_name`."""

    @real_name.setter
    @abc.abstractmethod
    def real_name(self, **kwargs):
        """Setter of `real_name`."""

    @abc.abstractmethod
    def to_code(self, ipt_args_in_construct: str, variable_name: str, output_var: str, code_fragment):
        """Graph node to MindSpore code."""

    @abc.abstractmethod
    def to_ir(self):
        """Graph node to ir node."""

    @abc.abstractmethod
    def add_input_and_output_shape(self, input_shape, output_shape):
        """Add the node input shape."""

    @staticmethod
    def _generate_ipt_args_settings_in_construct(ipt_args_in_construct, settings):
        """
        Generate input with args and settings in construct.

        Args:
            ipt_args_in_construct (str): Input args in construct.
            settings (Setting): Settings in operator.

        Returns:
            str, args of each node in generated construct statement.
        """
        if settings and settings.op_ipt_type:
            input_type = settings.op_ipt_type
            if input_type == InputType.TENSOR.value:
                ipt_args_settings_in_construct = ipt_args_in_construct
            elif input_type == InputType.LIST.value:
                ipt_args_settings_in_construct = f"({ipt_args_in_construct},)"
            else:
                raise NodeInputTypeNotSupportError(f"Input type[{input_type}] is not supported now.")
        else:
            ipt_args_settings_in_construct = ipt_args_in_construct

        if settings and settings.op_extra_input:
            settings_value = settings.op_extra_input
            if settings_value:
                settings_in_construct = ', '.join([f"{setting_val}" for _, setting_val in settings_value.items()])
                ipt_args_settings_in_construct = ', '.join((ipt_args_settings_in_construct, settings_in_construct))

        return ipt_args_settings_in_construct
