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
"""Define the NodeStruct which stores all info. of a node."""
from collections import OrderedDict

from mindinsight.mindconverter.graph_based_converter.common.code_fragment import NewFragment
from mindinsight.mindconverter.graph_based_converter.generator.fragment_utils import FragmentHandler
from .scope_utils import Scope
from .args_translator import ArgsTranslation
from ..third_party_graph.onnx_graph_node import OnnxGraphNode
from ..common.global_context import GlobalContext
from ...common.exceptions import GeneratorError

class NodeStruct:
    """
    Define a node struct which stores all info. to generate statement.

    Args:
        args (Union[PyTorchGraphNode, OnnxGraphNode, dict]): Node related obj.

    Note:
        You can pass as many args as possible and the Node Struct will update
        by arguments order.
    """
    GLOBAL_CONTEXT_MGR = GlobalContext()

    def __init__(self, args):
        # define attributes here
        self._identifier = None
        self._fragment = None
        self._args_translator = None
        self._parent_module_struct = None
        self.topo_idx = None
        self.onnx_name = None
        self.graph_node_ref = None
        self.scope_name = None
        self.ready_to_generate = False

        # Defined Scope class
        self.scope = None

        # Define attributes used for code generation

        # key is prec_node_name, value is x; For code line use
        self.inputs_in_construct_header = OrderedDict()

        # Matched inputs will can be directly used by code line generation
        self.matched_inputs = list()

        # initialize funcs.
        for arg in args:
            self.update(arg)

    def __repr__(self):
        return str({
            "address": hex(id(self)),
            "idx": self.topo_idx,
            "identifier": self.identifier
        })

    def ori_topo_idx(self):
        """Get the original topological index in the onnx graph."""
        ori_name = self._fragment.metadata.get('source')
        self.onnx_name = ori_name
        return self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_topo_idx.get(ori_name)

    def update_var_name(self, idx=None):
        """
        Update the var_name of each node.

        Args:
            idx (int): The index of the node in this module.
        """
        def _remove_op_header(op_name):
            """Remove op header which indicating their sources of op set."""
            op_name = op_name.replace('nn.', '')
            op_name = op_name.replace('P.', '')
            op_name = op_name.replace('onnx.', '')
            return op_name

        if idx is not None:
            self.ms_var_name = "{}_{}".format(_remove_op_header(self.ms_op), str(idx)).lower()
        elif self.topo_idx is not None:
            self.ms_var_name = "{}_{}".format(_remove_op_header(self.ms_op), str(self.topo_idx)).lower()
        else:
            raise ValueError("Unable to update var name when topo_idx is None.")
        self.fragment.default_var['variable_name'] = self.ms_var_name

    def _update_basics_from_gn(self, gn):
        """Update basic info from GraphNode."""
        self.graph_node_ref = gn
        self.scope_name = gn.scope_name

    def _update_from_onnx_gn(self, gn: OnnxGraphNode):
        """Update basic info from OnnxGraphNode."""
        self._update_basics_from_gn(gn)

    def _update_from_fragment(self, frag: NewFragment):
        """Update info from CodeFragment."""
        self._fragment = FragmentHandler(frag)

        if self.ms_op:
            idx = self.GLOBAL_CONTEXT_MGR.latest_node_struct_count
            self.update_var_name(idx=idx)

    def _set_scope_from_identifier(self):
        """Set the Node scope from identifier."""
        parsed_scope = Scope.parse_scope_from_node_identifier(self.identifier)
        self.scope = Scope(parsed_scope)

    @GeneratorError.check_except("Generator occurs an error when initializing node's args translator.")
    def init_args_translator(self, translated_args: list):
        """
        Initialize the ArgsTranslator for each Node.

        Args:
            translated_args (list): The list of args should be translated to formal args.
        """
        if not self._fragment:
            raise ValueError("Initialize argument translator failed.")
        if self._fragment.converted and self._fragment.default_var["args"] and translated_args:
            self._args_translator = ArgsTranslation(self._fragment.default_var["args"],
                                                    self.ms_var_name,
                                                    translated_args)

    @GeneratorError.check_except("Generator occurs an error when creating node struct.")
    def update(self, arg):
        """
        Pass Node info. to generator NodeStruct.

        Args:
            arg (Union[PyTorchGraphNode, OnnxGraphNode, dict]): Node related obj.
            force_ready (bool): Force this NodeStruct is ready to generate.
        """

        if isinstance(arg, OnnxGraphNode):
            self._update_from_onnx_gn(arg)
        elif isinstance(arg, NewFragment):
            self._update_from_fragment(arg)
        else:
            raise TypeError("NodeStruct received an unsupported initializing argument.")

    @property
    def identifier(self):
        """Return the identifier of the node."""
        return self._identifier

    @identifier.setter
    def identifier(self, s):
        """
        Set the Node identifier, and update the scope.

        Args:
            s (str): The node identifier string.
        """
        self._identifier = s
        self._set_scope_from_identifier()
        self.topo_idx = self.ori_topo_idx()
        self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map[self.onnx_name] = self

    @property
    def fragment(self):
        """Return the fragment of the node."""
        return self._fragment

    @fragment.setter
    def fragment(self, frag):
        """
        Set the Node fragment.

        Args:
            s (NodeFragment): The node identifier string.
        """
        self._fragment = frag

    @property
    def graph_node(self):
        """Return the GraphNode reference."""
        return self.graph_node_ref

    @graph_node.setter
    def graph_node(self, graphnode):
        """Set the GraphNode reference."""
        self.graph_node_ref = graphnode

    @property
    def onnx_node(self):
        """Return the original onnx node reference."""
        return self.GLOBAL_CONTEXT_MGR.onnx_nodes_collection.get(self.onnx_name)

    @property
    def ms_op(self):
        """Return the operation name in MindSpore."""
        return self._fragment.default_var.get('operation')

    @ms_op.setter
    def ms_op(self, ms_op_name: str):
        """Set the operation name in MindSpore."""
        self._fragment.default_var['operation'] = ms_op_name

    @property
    def ms_var_name(self):
        """Return the variable name of this Node in the MindSpore script."""
        return self._fragment.default_var.get('variable_name')

    @ms_var_name.setter
    def ms_var_name(self, ms_var_name: str):
        """Set the variable name of this Node in the MindSpore script."""
        self._fragment.default_var['variable_name'] = ms_var_name

    @property
    def ms_opt_var_name(self):
        """Return the output variable name of current node."""
        return self.fragment.fragment.get_outputs_by_idx(0)

    @property
    def args_translator(self):
        """Return the args translator of this Node."""
        return self._args_translator

    @property
    def precursor_nodes_names(self) -> list:
        """Return the names of precursor nodes."""
        return self.graph_node_ref.precursor_nodes

    @property
    def precursor_nodes_structs(self) -> list:
        """Return the node struct instances of precursor nodes."""
        ret = []
        precursor_nodes_names = self.precursor_nodes_names
        for pre_node_name in precursor_nodes_names:
            nd_struct = self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map.get(pre_node_name)
            ret.append(nd_struct)
        return ret

    @property
    def successor_nodes_names(self) -> list:
        """Return the names of successor nodes."""
        return self.graph_node_ref.successor_nodes

    @property
    def successor_nodes_structs(self) -> list:
        """Return the node struct instances of successor nodes."""
        ret = []
        for pre_node_name in self.successor_nodes_names:
            nd_struct = self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map.get(pre_node_name)
            ret.append(nd_struct)
        return ret

    @property
    def parent_module_struct(self):
        """Return the parent struct of this node."""
        return self._parent_module_struct

    @parent_module_struct.setter
    def parent_module_struct(self, ref):
        self._parent_module_struct = ref

    @property
    def outputs_manager(self):
        """Return the outputs manager instance."""
        return self.fragment.outputs_manager

    @property
    def outputs_in_construct(self):
        """Return the outputs var(s) in construct statement."""
        return self.fragment.fragment.outputs()

    # Code Generation funcs below

    def code_line_in_init(self):
        """Initialization line of code in module init block."""
        left = "self.{}".format(self.ms_var_name)
        args_list = list()
        if self._args_translator is not None:
            self.fragment.default_var['args'] = {**self._args_translator.actual_args,
                                                 **self._args_translator.formal_args}
            args_list += self._args_translator.actual_args_to_str_list
            args_list += self._args_translator.formal_args_to_str_list
        else:
            actual_args_str = ArgsTranslation.dict_data_to_args_str_list(self._fragment.default_var['args'])
            args_list += actual_args_str

        if not self._fragment.converted:
            args_list.append('='.join(["input_shape", str(self._fragment.input_shape)]))
            args_list.append('='.join(["output_shape", str(self._fragment.output_shape)]))
            right = f"{self.ms_op.replace('::', '.')}({', '.join(args_list)})"
        else:
            right = f"{self.ms_op}({', '.join(args_list)})"
        return left, right

    def code_line_in_construct(self, inputs=None):
        """Construct line of code in module construct block. """
        left = self.ms_opt_var_name

        if not self.matched_inputs and inputs is None:
            raise ValueError("Unable to generate the code construct statement due to empty inputs.")

        if self.matched_inputs:
            inputs = self.matched_inputs

        # Check original onnx node's input to ensure double inputs are not ignored
        original_inputs = self.GLOBAL_CONTEXT_MGR.onnx_node_inputs.get(self.onnx_name)
        new_inputs = []
        for idx, prec_node in enumerate(self.precursor_nodes_names):
            occurence = original_inputs.count(prec_node)
            for _ in range(occurence):
                new_inputs.append(inputs[idx])
        inputs = new_inputs

        if isinstance(inputs, str):
            inputs = [inputs]

        self.fragment.default_var['inputs'] = inputs
        right = f"self.{self.ms_var_name}({', '.join(inputs)})"
        return left, right

    def add_extra_tensor(self):
        """ Add extra tensor."""
        left = "self.{}_w".format(self.ms_var_name)
        shape = self._fragment.code_setting.op_extra_tensor.shape
        right = f"Tensor(np.random.uniform(0, 1, {shape}), mindspore.float32)"
        return left, right

    # The following functions are specified for multiple in/out support.
    # and should be called only after generator._recursive_form_modules()

    def set_inputs_in_construct_header(self, header_x, onnx_precursor_node_name):
        """
        Mark the registered external inputs for code generation.

        Note:
            This function to be called by its parent (ModuleStruct).

        Args:
            header_x (str): The `x` in module construct header.
            onnx_precursor_node_name (str): The original onnx node name.
        """
        if self.inputs_in_construct_header.get(onnx_precursor_node_name) is not None:
            raise ValueError("The input from {} has already registered. Check this node \
                {} has duplicate inputs or not.".format(onnx_precursor_node_name, self.identifier))
        self.inputs_in_construct_header[onnx_precursor_node_name] = header_x

    def check_target_node_internal(self, name: str) -> bool:
        """
        Check given node under the same scope.

        Args:
            name (str): Can accept both node identifier or original onnx node name.
        """
        target_nd_struct = self.GLOBAL_CONTEXT_MGR.node_struct_collections.get(name) \
            or self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map.get(name)
        if target_nd_struct is None and self.topo_idx == 0:  # First node always has external input
            return False

        if target_nd_struct is None and (name in self.GLOBAL_CONTEXT_MGR.onnx_graph_info.get('graph_inputs')):
            return False

        if target_nd_struct is None:
            raise ValueError("Unable to find the NodeStruct of given target node {}.".format(name))
        return target_nd_struct.scope.path == self.scope.path

    @property
    def has_successor_node_external(self) -> bool:
        """Check if any successor_node is in external module."""
        for name in self.successor_nodes_names:
            if not self.check_target_node_internal(name):
                return False

        return True

    @property
    def precursor_nodes_names_external(self) -> list:
        """Return a list of external precursor nodes names."""
        return [name for name in self.precursor_nodes_names
                if not self.check_target_node_internal(name)]

    @property
    def successor_nodes_names_external(self) -> list:
        """Return a list of external successor nodes names."""
        return [name for name in self.successor_nodes_names
                if not self.check_target_node_internal(name)]
