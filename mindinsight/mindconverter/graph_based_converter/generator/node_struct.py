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
"""Define the NodeStruct which stores all info. of a node."""
from collections import OrderedDict

from .scope_utils import Scope
from .args_translator import ArgsTranslation
from ..common.code_fragment import CodeFragment
from ..third_party_graph.pytorch_graph_node import PyTorchGraphNode
from ..third_party_graph.onnx_graph_node import OnnxGraphNode
from ..common.global_context import GlobalContext
from ..constant import InputType
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
        self.node_type = None
        self.onnx_name = None
        self.onnx_op = None
        self.graph_node_ref = None
        self.scope_name = None
        self.ms_var_name = None
        self.ms_op = None
        self.ready_to_generate = False

        # Define attributes converted from mapper
        self.ms_params = dict()
        self.ms_settings = dict()
        self.ms_weights = dict()
        self.ms_inputs = OrderedDict()

        # Defined Scope class
        self.scope = None

        # Define attributes used for code generation

        # key is prec_node_name, value is x; For code line use
        self.inputs_in_construct_header = OrderedDict()

        # key is prec_node_name, value is its closet opt_var_name
        self.inputs_in_parent_module = OrderedDict()

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
        ori_name = self.identifier.replace('$', '').split('/')[-1].replace("::", '/')
        self.onnx_name = ori_name
        return self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_topo_idx.get(ori_name)

    def update_var_name(self, idx=None):
        """
        Update the var_name of each node.

        Args:
            idx (int): The index of the node in this module.
        """
        if idx is not None:
            self.ms_var_name = self.ms_op.replace('nn.', '').replace('P.', '').lower() + '_' + str(idx)
        elif self.topo_idx is not None:
            self.ms_var_name = self.ms_op.replace('nn.', '').replace('P.', '').lower() + '_' + str(self.topo_idx)
        else:
            raise ValueError("Unable to update var name when topo_idx is None.")

    def _update_basics_from_gn(self, gn):
        """Update basic info from GraphNode."""
        self.graph_node_ref = gn
        self.scope_name = gn.scope_name

    def _update_from_pytorch_gn(self, gn: PyTorchGraphNode):
        """Update basic info from PyTorchGraphNode."""
        self.node_type = "PyTorchGraphNode"
        self._update_basics_from_gn(gn)

    def _update_from_onnx_gn(self, gn: OnnxGraphNode):
        """Update basic info from OnnxGraphNode."""
        self.node_type = "OnnxGraphNode"
        self._update_basics_from_gn(gn)

    def _update_from_mapper(self, d):
        """Update info from mapper."""
        if d.get('op_name'):
            self.ms_op = d.get('op_name')
        if d.get('params'):
            self.ms_params = d.get('params')
        if d.get('settings'):
            self.ms_settings = d.get('settings')
        if d.get('weights'):
            self.ms_weights = d.get('weights')

    def _update_from_fragment(self, frag: CodeFragment):
        """Update info from CodeFragment."""
        self._fragment = frag
        if frag.operation:
            self.ms_op = frag.operation
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
        if self._fragment.actual_args and translated_args:
            self._args_translator = ArgsTranslation(self._fragment.actual_args, self.ms_var_name, translated_args)

    def check_if_generate_ready(self):
        """Check if the NodeStruct is able to generate code."""
        # check essential params exists
        if all([self.identifier,
                self.node_type,
                self.scope_name,
                self.ms_var_name,
                self.ms_opt_var_name,
                self.ms_op]):
            self.ready_to_generate = True

    @GeneratorError.check_except("Generator occurs an error when creating node struct.")
    def update(self, arg, force_ready=False):
        """
        Pass Node info. to generator NodeStruct.

        Args:
            arg (Union[PyTorchGraphNode, OnnxGraphNode, dict]): Node related obj.
            force_ready (bool): Force this NodeStruct is ready to generate.
        """
        if isinstance(arg, PyTorchGraphNode):
            self._update_from_pytorch_gn(arg)
        elif isinstance(arg, OnnxGraphNode):
            self._update_from_onnx_gn(arg)
        elif isinstance(arg, (dict, OrderedDict)):
            self._update_from_mapper(arg)
        elif isinstance(arg, CodeFragment):
            self._update_from_fragment(arg)
        else:
            raise TypeError("NodeStruct received an unsupported initializing argument.")

        if force_ready:
            self.ready_to_generate = True
        else:
            self.check_if_generate_ready()

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
    def ms_opt_var_name(self):
        """Return the output variable name of current node."""
        return "{}_opt".format(self.ms_var_name).lower()


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

    # Code Generation funcs below

    def code_line_in_init(self):
        """Initialization line of code in module init block."""
        unconverted = False
        if "onnx::" in self.ms_var_name:
            unconverted = True
            self.ms_var_name = self.ms_var_name.replace("onnx::", "")
        left = "self.{}".format(self.ms_var_name)

        args_list = list()
        if self._args_translator is not None:
            args_list += self._args_translator.actual_args_to_str_list
            args_list += self._args_translator.formal_args_to_str_list
        else:
            actual_args_str = ArgsTranslation.dict_data_to_args_str_list(self._fragment.actual_args)
            args_list += actual_args_str

        if unconverted:
            args_list.append('='.join(["input_shape", str(self._fragment.input_shape)]))
            args_list.append('='.join(["output_shape", str(self._fragment.output_shape)]))
            right = f"{self.ms_op.replace('::', '.')}({', '.join(args_list)})"
        else:
            right = f"{self.ms_op}({', '.join(args_list)})"
        return left, right

    def _get_correct_in_module_returns(self, prec_node, in_module_return):
        """
        Find the correct precursor node name in return statement of its parent module.

        Args:
            prec_node (str): The onnx name of the precursor node given.
            in_module_return (list[tuple]): The list of outputs which contains parent module identifier
                and module opt_var_name.

        Return:
            str, correct opt_var_name to be passed in current node.
        """
        found_return = False
        for ret in in_module_return:
            (md_identifier, input_name_to_use) = ret
            p_node_struct = self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map.get(prec_node)
            # recursive check the p node parent
            parent = p_node_struct
            while not found_return:
                parent = parent.parent_module_struct
                if parent is None:
                    break
                if parent.identifier == md_identifier:
                    return input_name_to_use
        return None

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

        if self._fragment.code_setting and self._fragment.code_setting.op_ipt_type == InputType.LIST.value:
            inputs = [str(tuple(inputs)).replace("\'", "")]

        if self._fragment.code_setting and self._fragment.code_setting.op_extra_input:
            for _, val in self._fragment.code_setting.op_extra_input.items():
                inputs.append(str(val))

        if self._fragment.code_setting and self._fragment.code_setting.op_extra_tensor:
            inputs.append(f"self.{self.ms_var_name}_w")
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

    def _check_target_node_internal(self, name: str) -> bool:
        """
        Check given node under the same scope.

        Args:
            name (str): Can accept both node identifier or original onnx node name.
        """
        target_nd_struct = self.GLOBAL_CONTEXT_MGR.node_struct_collections.get(name) \
            or self.GLOBAL_CONTEXT_MGR.onnx_node_name_to_node_struct_map.get(name)
        if target_nd_struct is None and self.topo_idx == 0:  # First node always has external input
            return False

        if target_nd_struct is None:
            raise ValueError("Unable to find the NodeStruct of given target node {}.".format(name))
        return target_nd_struct.scope.path == self.scope.path

    @property
    def has_successor_node_external(self) -> bool:
        """Check if any successor_node is in external module."""
        for name in self.successor_nodes_names:
            if not self._check_target_node_internal(name):
                return False

        return True

    @property
    def precursor_nodes_names_external(self) -> list:
        """Return a list of external precursor nodes names."""
        return [name for name in self.precursor_nodes_names
                if not self._check_target_node_internal(name)]

    @property
    def successor_nodes_names_external(self) -> list:
        """Return a list of external successor nodes names."""
        return [name for name in self.successor_nodes_names
                if not self._check_target_node_internal(name)]
