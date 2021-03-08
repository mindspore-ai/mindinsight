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
from mindinsight.mindconverter.graph_based_converter.generator.scope_utils import Scope
from mindinsight.mindconverter.graph_based_converter.generator.args_translator import ArgsTranslation
from mindinsight.mindconverter.graph_based_converter.third_party_graph.onnx_graph_node import OnnxGraphNode
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.common.exceptions import GeneratorError


class NodeStruct:
    """
    Define a node struct which stores all info. to generate statement.

    Args:
        args (Union[PyTorchGraphNode, OnnxGraphNode, dict]): Node related obj.

    Note:
        You can pass as many args as possible and the Node Struct will update
        by arguments order.
    """
    def __init__(self, args):
        # define attributes here
        self.global_context_mgr = GlobalContext()
        self._identifier = None
        self._fragment = None
        self._args_translator = None
        self._parent_module_struct = None
        self._global_context = GlobalContext()
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
        return self._global_context.onnx_node_name_to_topo_idx.get(ori_name)

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
            idx = self._global_context.latest_node_struct_count
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
        self._global_context.onnx_node_name_to_node_struct_map[self.onnx_name] = self

    @property
    def fragment(self):
        """Return the fragment of the node."""
        return self._fragment

    @fragment.setter
    def fragment(self, frag):
        """
        Set the Node fragment.

        Args:
            frag (NodeFragment): The node identifier string.
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
        return self._global_context.onnx_nodes_collection.get(self.onnx_name)

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
            nd_struct = self._global_context.onnx_node_name_to_node_struct_map.get(pre_node_name)
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
            nd_struct = self._global_context.onnx_node_name_to_node_struct_map.get(pre_node_name)
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

    @property
    def inputs_edges_names(self):
        """Return the inputs edges of this node."""
        # Consider moving this process to metadata.
        ret = []
        for edge in self.fragment.metadata.get('inputs'):
            if not self._global_context.get_onnx_tensor(edge):
                ret.append(edge)
        return ret

    @property
    def shared_weights(self):
        """Return the shared weights in this node."""
        shared_weight_names = []
        for shared_weight_name, repeated_node_list in self._global_context.repeated_weights.items():
            if self.onnx_name in repeated_node_list:
                shared_weight_names.append(shared_weight_name)
        return shared_weight_names

    # Code Generation funcs below

    def _get_shared_weight_var_names_from_parent(self, onnx_name=None):
        """
        Get shared weight var name in the parent module.

        Args:
            onnx_name (str): The onnx name of this weight. Default None.

        Returns:
            [List, str], a list of all shared weights the node has or the specific name provided.
        """
        if onnx_name is None:
            shared_weights_var_name_in_module = []
            for shared_w in self.shared_weights:
                for passthrough_w, passthrough_w_var_name in \
                self._parent_module_struct.shared_weights_collection.items():
                    if shared_w == passthrough_w:
                        shared_weights_var_name_in_module.append(passthrough_w_var_name)
            return shared_weights_var_name_in_module
        if isinstance(onnx_name, str):
            return self._parent_module_struct.shared_weights_collection.get(onnx_name)

        return []


    def code_line_in_init(self):
        """Initialization line of code in module init block."""
        if self._args_translator is not None:
            self.fragment.default_var['args'] = {**self._args_translator.actual_args,
                                                 **self._args_translator.formal_args}

        # create a parameter for shared weight scenario
        trainable_params = self.fragment.default_var.get("trainable_params")
        if trainable_params and self.fragment.default_var.get("parameters"):
            # if trainable params and the mappers accept the param declaration rewritten.
            for trainable_param_postfix, data_dict in trainable_params.items():
                onnx_name = data_dict.get('onnx_name')
                nparray = data_dict.get('data')
                try:
                    shape = nparray.shape
                    dtype = nparray.dtype
                except Exception:
                    raise ValueError("Parameters has inconsistent data type.")
                # set declare statement
                declare_statement = self.fragment.fragment.create_parameter(shape, dtype)
                if onnx_name not in self._global_context.repeated_weights.keys():
                    # if the weight is not a shared weight, set to actual declaration.
                    if not self.fragment.default_var["parameters"].get(trainable_param_postfix):
                        self.fragment.default_var["parameters"][trainable_param_postfix] = declare_statement
                    continue # not a shared weight, skip the rest

                if onnx_name not in self._global_context.repeated_weights_declaration.keys():
                    self._global_context.repeated_weights_declaration[onnx_name] = declare_statement

                # set template to mapper parameter rewritten.
                shared_w_var_in_parent = self._get_shared_weight_var_names_from_parent(onnx_name=onnx_name)
                # add self for node node under public parent module
                if self.parent_module_struct.identifier == []:
                    #now only consider declaration in the main model
                    shared_w_var_in_parent = f"self.{shared_w_var_in_parent}"
                self.fragment.default_var["parameters"][trainable_param_postfix] = shared_w_var_in_parent

    def code_line_in_construct(self, inputs=None):
        """Construct line of code in module construct block. """
        left = self.ms_opt_var_name

        inputs = []

        # Bind current node opt_var_name & register to parent
        self.outputs_manager.bind_opt_var_names(self.fragment.fragment)
        for base_out in self.outputs_manager.outputs:
            opt_var = base_out.opt_var_name
            self.parent_module_struct.internal_outputs_collection[base_out.onnx_edge_name] = opt_var

        # Take inputs from parents module
        for input_edge in self.inputs_edges_names:
            if input_edge in self.parent_module_struct.inputs_register:
                inputs.append(self.parent_module_struct.inputs_register.get(input_edge))
            elif input_edge in self.parent_module_struct.internal_outputs_collection:
                inputs.append(self.parent_module_struct.internal_outputs_collection.get(input_edge))

        self.fragment.default_var['inputs'] = inputs
        return left

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
        target_nd_struct = self._global_context.node_struct_collections.get(name) \
            or self._global_context.onnx_node_name_to_node_struct_map.get(name)
        if target_nd_struct is None and self.topo_idx == 0:  # First node always has external input
            return False

        if target_nd_struct is None and (name in self._global_context.onnx_graph_info.get('graph_inputs')):
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
