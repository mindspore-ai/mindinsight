# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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

from mindinsight.mindconverter.common.log import logger as log
from ..constant import SEPARATOR_IN_ONNX_OP
from ..mapper.base import Mapper


class GraphParser(metaclass=abc.ABCMeta):
    """Graph parser."""

    @classmethod
    @abc.abstractmethod
    def parse(cls, model_path: str):
        """Parse graph into readable format."""


class BaseGraph(metaclass=abc.ABCMeta):
    """Define basic graph."""
    _REQUIRED_PARAM_OF_MODEL = "model"

    @abc.abstractmethod
    def build(self, input_shape: tuple):
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
    def load_graph(graph_path: str):
        """Load graph file."""

    @classmethod
    @abc.abstractmethod
    def load(cls, model_path: str, sample_shape: tuple = None,
             checkpoint: str = None):
        """Factory method to initialize an graph object."""

    def __new__(cls, *args, **kwargs):
        """Control the create action of graph."""
        model_param = args[0] if args else kwargs.get(cls._REQUIRED_PARAM_OF_MODEL)
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
        self.checkpoint = kwargs.get("checkpoint", None)
        self._nodes_collection = OrderedDict()
        self._nodes_record = dict()
        self._shape_dict = dict()
        self._input_nodes = []
        self._output_nodes = []
        self._topological_order = []
        self._input_shape = dict()

    def get_input_shape(self, name):
        """
        Get node input shape.

        Args:
            name (str): Node name.

        Returns:
            list, shape.
        """
        return self._input_shape.get(name)

    def get_output_shape(self, name):
        """
        Get node output shape.

        Args:
            name (str): Node name.

        Returns:
            list, shape.
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

    def build(self, input_shape: tuple):
        """
        Build graph.

        Args:
            input_shape (tuple): Input shape of model.

        """
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
                # NOTICE: what's usage of `scope`?
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
    def load_graph(graph_path: str):
        raise NotImplementedError

    @classmethod
    def load(cls, model_path: str, sample_shape: tuple = None,
             checkpoint: str = None) -> BaseGraph:
        """
        Load third party graph, metadata and checkpoint.

        Notes:
            `checkpoint` is optional, and it can not be supported currently.

        Args:
            model_path (str): Graph or model file path.
            sample_shape (tuple): Input shape of the model.
            checkpoint (str): Checkpoint file path.

        Returns:
            cls, graph instance.
        """
        src_graph = cls.load_graph(graph_path=model_path)
        ckpt = cls.load_checkpoint(ckpt_path=checkpoint) if checkpoint else None

        if ckpt is not None:
            # Create an instance of TensorflowGraph.
            return cls(model=src_graph, sample_shape=sample_shape,
                       checkpoint=ckpt)

        # Create an instance of PyTorchGraph.
        return cls(model=src_graph, sample_shape=sample_shape)


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
        # Source node in pytorch.
        self._src_node = str(node) if node else None
        # Original operation name in pytorch.
        self._op_name = None
        self._op_params = dict()
        self._scope_name = None
        self._op_shape = None
        # Operation in mindspore.
        self._op_in_ms = None
        # Params in mindspore.
        self._params_in_ms = dict()
        # Node type of current node, e.g. class, module, operation.
        self._node_type = None
        # Tag name on tree.
        self._tag_on_tree = None
        # Function, class or operation needed args.
        self._args_in_code = dict()
        # Variable name declared in init block.
        self._variable_name = None
        # Output variable name declared in construct block.
        self._opt_var_name = None
        # Function or class name in code.
        self._module_name = None
        # Unique key of node.
        self._hash_key = None
        # Input shape of current op.
        self._ipt_shape = None
        # Output shape of current op.
        self._opt_shape = None
        # Weight of current op.
        self._weight = None

    @property
    def opt_var_name(self):
        """
        Output variable name.

        Returns:
            str, variable name.
        """
        return f"{self.variable_name}_opt"

    @opt_var_name.setter
    def opt_var_name(self, v):
        """
        Set variable name.

        Args:
            v (str): Name.

        """
        self._opt_var_name = v

    @property
    def op_in_ms(self):
        """
        Operation in mindspore.

        Returns:
            str, operation name.
        """
        if self._op_in_ms and SEPARATOR_IN_ONNX_OP in self._op_in_ms:
            return self._op_in_ms.replace(SEPARATOR_IN_ONNX_OP, ".")
        return self._op_in_ms

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

    @property
    def tag(self):
        """Tag on hierarchical tree."""
        return self._tag_on_tree

    @tag.setter
    def tag(self, t):
        """Tag on hierarchical tree."""
        self._tag_on_tree = t

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
    def _get_arg_name(self, arg):
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

    @property
    @abc.abstractmethod
    def variable_name(self):
        """Getter of `variable_name`."""

    @abc.abstractmethod
    def to_code(self, ipt_args_in_construct: str, output_var: str):
        """Graph node to MindSpore code."""

    @abc.abstractmethod
    def to_ir(self):
        """Graph node to ir node."""

    @abc.abstractmethod
    def add_input_and_output_shape(self, input_shape, output_shape):
        """Add the node input shape."""

    @abc.abstractmethod
    def froze_node_type_and_module_name(self, node_type, module_name):
        """Make node_type can not be changed."""

    @abc.abstractmethod
    def convert_successful(self):
        """Whether convert successful."""

    def param_transform(self, mapper: Mapper):
        """
        Transform param in pytorch operation into mindspore.

        Args:
            mapper (ONNXToMindSporeMapper): Mapper between onnx operation
                and mindspore.

        Returns:
            dict, transformed params.
        """
        import copy
        params = copy.deepcopy(self._op_params)
        params.update({"input_shape": self.input_shape,
                       "output_shape": self.output_shape})

        op_name_in_mindspore, ms_params = mapper.convert(op_name=self.op_name,
                                                         params=params,
                                                         weights=self._weight)
        if op_name_in_mindspore:
            self._op_in_ms = op_name_in_mindspore
            self._params_in_ms = ms_params
        else:
            self._op_in_ms = self._op_name
            self._params_in_ms = self._op_params

        return self._op_in_ms, self._params_in_ms
