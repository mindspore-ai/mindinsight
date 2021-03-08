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
"""Define a struct for module converted and save all required information here."""

import copy
from collections import OrderedDict

from mindinsight.mindconverter.graph_based_converter.generator.node_struct import NodeStruct
from mindinsight.mindconverter.graph_based_converter.generator.scope_utils import Scope
from mindinsight.mindconverter.graph_based_converter.common.utils import get_dict_key_by_value
from mindinsight.mindconverter.graph_based_converter.generator.args_translator import ArgsTranslation
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.common.name_mgr import LocalVarNameMgr


class ModuleStruct:
    """
    Define a module struct which stores all info. to generate statement.

    Args:
        nd_struct_list (list): A list of node structs.
        init_as_parent (bool): Control init method if the ModuleStruct be init as a parent module struct.
        parent_base (ModuleStruct): The base ModuleStruct the current ModuleStruct to be init as.
    """
    def __init__(self, nd_struct_list, init_as_parent=False, parent_base=None):
        """Init. a module by NodeStructs."""
        self.pattern_id = -1  # pattern num, -1 as Main module
        self.pattern_uid = -1  # unique module id for this pattern
        self.parent_id = None  # parent's pattern num
        self.parent_uid = None  # parent's pattern module unique id
        self.initialized = False
        self.identifier = None
        self.module_name = None
        self.scope_depth = None
        self.head_nd_struct = None
        self.head_nd_struct_index = None
        self.tail_nd_struct = None
        self.tail_nd_struct_index = None
        self._node_structs = list()
        self._module_structs = list()

        self._fragment = None
        self._args_translator = None
        self._parent_module_struct = None
        # only store original formal args name, not global
        self._nodes_structs_formal_args_list = list()

        # define other settings here
        self._node_args_translation_list = list()
        self._var_name_mgr = LocalVarNameMgr()
        self.construct_header_x = OrderedDict()  # key is header x, value is precursors onnx name
        self.inputs_in_construct_header = OrderedDict()  # key is precursors onnx name, value is x in parent construct

        # key is node's onnx name(output provider), value is (provider_succ_name, opt_var_name)
        self.outputs_collection = dict()
        self.matched_inputs = list()  # Matched inputs will can be directly used by code line generation

        # key is ext. succ node onnx name, value is local opt_var
        self.external_successor_local_returns_map = OrderedDict()

        # Define outputs manager, note this will be assigned later by Generator.
        self.outputs_manager = None

        self._global_context = GlobalContext()

        # Define a dict to store the reference for quick searching
        self.rapid_reference = dict()

        # new vars for matcher
        self.inputs_register = OrderedDict() # reg by sub
        self.outputs_register = OrderedDict() # reg by sub
        self.internal_outputs_collection = dict() # reg by sub

        # new vars for shared weights
        self.shared_weights_collection = dict() # reg by sub
        self.shared_weights_counter = 0 # updated by sub

        if init_as_parent and (parent_base is not None):
            self.reset_as_parent_passed_in(parent_base)
        else:
            # start initialization
            if not self.initialized:
                self._init_module(nd_struct_list)
            else:
                self._update_module(nd_struct_list)

            # assign this module reference to node
            for (_, nd_struct) in nd_struct_list:
                nd_struct.parent_module_struct = self

    def reset_as_parent_passed_in(self, parent_base):
        """
        Reset all attributes and filled as a parent module of the module passed in.

        Args:
            parent_base(ModuleStruct): The base ModuleStruct to be passed in for ModuleStruct init.

        Note:
            This function must be called only if the new ModuleStruct is a parent of parent_base.
        """
        self.identifier = copy.deepcopy(parent_base.identifier)[:-1]
        self.scope_depth = copy.deepcopy(parent_base.scope_depth) - 1
        self.module_name = Scope.scope_to_module_name(self.identifier)
        self.head_nd_struct = parent_base.head_nd_struct
        self.head_nd_struct_index = parent_base.head_nd_struct_index
        self.tail_nd_struct = parent_base.tail_nd_struct
        self.tail_nd_struct_index = parent_base.tail_nd_struct_index
        self._node_structs = list()
        self._module_structs = list()
        self._fragment = None
        self._args_translator = None
        self.initialized = True
        self._set_pattern_id()
        self._find_parent_module()
        self.init_args_translator()
        self._parent_module_struct = None
        self._nodes_structs_formal_args_list = list()
        self._node_args_translation_list = list()

    def _set_pattern_id(self):
        """Set pattern id which matches the module fragment pattern."""
        if not self.initialized:
            return
        if self.scope_depth < 1:
            self.pattern_id = -1
            self.pattern_uid = -1
            return
        self.pattern_id = self.identifier[-1][0]
        self.pattern_uid = self.identifier[-1][1]

    def _init_module(self, nd_struct_list):
        """Init this ModuleStruct by a list of Nodes."""
        (nd_topo_idx, nd_struct) = nd_struct_list[0]
        self.identifier = nd_struct.scope.path
        self.module_name = nd_struct.scope.to_str
        self.scope_depth = nd_struct.scope.depth
        self.head_nd_struct = nd_struct
        self.head_nd_struct_index = nd_topo_idx
        self.tail_nd_struct = nd_struct_list[-1][1]
        self.tail_nd_struct_index = nd_struct_list[-1][0]
        self._node_structs = nd_struct_list
        self.initialized = True
        self._set_pattern_id()
        self._find_parent_module()
        self.init_args_translator()

    def _update_module(self, nd_struct_list):
        """Update the ModuleStruct attributes from a list of Nodes."""
        (nd_topo_idx_head, nd_struct_head) = nd_struct_list[0]
        (nd_topo_idx_tail, nd_struct_tail) = nd_struct_list[-1]
        if self.identifier != nd_struct_head.scope.path:
            raise ValueError("Unable to update this module struct {} due to different identifier {}".format(
                self.identifier, nd_struct_head.scope.path))
        if nd_topo_idx_head < self.head_nd_struct_index:
            self.head_nd_struct_index = nd_topo_idx_head
            self.head_nd_struct = nd_struct_head
        if nd_topo_idx_tail > self.tail_nd_struct_index:
            self.tail_nd_struct_index = nd_topo_idx_tail
            self.tail_nd_struct = nd_struct_tail
        self._node_structs += nd_struct_list

    def _find_parent_module(self):
        """Set the parent's module pattern and uid."""
        if not self.initialized:
            return
        if self.scope_depth == 0:  # is Main Module
            pass
        elif self.scope_depth == 1:  # parent pattern is Main module
            self.parent_id = -1
            self.parent_uid = -1
        else:  # this is a submodule in a module
            (self.parent_id, self.parent_uid) = Scope.get_parent_module_num_and_uid(
                self.identifier)

    def __repr__(self):
        return str({
            "address": hex(id(self)),
            "identifier": self.identifier,
            "parent": (self.parent_id, self.parent_uid),
            "name": self.module_name,
            "pattern": self.pattern_id,
            "scope_depth": self.scope_depth,
            "nd_idx_range": "{} -> {}".format(self.head_nd_struct_index, self.tail_nd_struct_index),
            "initialized": self.initialized
        })

    def init_args_translator(self):
        """Initialize the Args Translator for the module."""
        var_name = self.ms_var_name
        self._args_translator = ArgsTranslation(None, var_name, None)

    def update_module_fragment(self):
        """Update this module's fragment."""
        if self._fragment is None:
            return

        # update input output shape
        self._fragment.input_shape = self.head_nd_struct.fragment.input_shape
        self._fragment.output_shape = self.tail_nd_struct.fragment.output_shape

        # update formal args
        self._fragment.formal_args.update(self._args_translator.formal_args)
        self._fragment.formal_args_value.update(self._args_translator.formal_args_values)
        # update actual args
        self._fragment.actual_args.update(self._args_translator.actual_args)
        # update others..

    def add_submodule(self, md_structs):
        """
        Add another module struct(s) to this ModuleStruct.

        Args:
            md_structs ([ModuleStruct, list]): a (list) ModuleStruct to be added in this ModuleStruct.
        """
        tail_md = md_structs
        if isinstance(md_structs, ModuleStruct):
            md_structs.args_translator.take_formal_args_from_nodes_and_submodules(md_structs.get_all_sub_translators())
            self._module_structs.append(md_structs)
            md_structs.parent_module_struct = self
        elif isinstance(md_structs, list):
            for md_s in md_structs:
                md_s.args_translator.take_formal_args_from_nodes_and_submodules(md_s.get_all_sub_translators())
                md_s.parent_module_struct = self
            self._module_structs += md_structs
            tail_md = md_structs[-1]
        else:
            raise TypeError("ModuleStruct cannot add an unsupported Type {} to module_structs list.".format(
                type(md_structs)))
        # update tail node and index
        if self.tail_nd_struct_index < tail_md.tail_nd_struct_index:
            self.tail_nd_struct = tail_md.tail_nd_struct
            self.tail_nd_struct_index = tail_md.tail_nd_struct_index

    def _update_formal_args_for_all_nd_structs(self):
        """
        Init nodes' args translator and find formal args.
        And collect nodes' formal args.
        """
        if len(self._node_args_translation_list) != len(self._node_structs):
            raise ValueError(
                "ModuleStruct cannot update nodes' formal args due to length inconsistent.")
        for idx, (_, nd_struct) in enumerate(self._node_structs):
            formal_arg_of_this_node = self._node_args_translation_list[idx]
            # update var_name to ensure all node names' are unique in a module.
            nd_struct.update_var_name(idx)
            nd_struct.init_args_translator(formal_arg_of_this_node)
            if nd_struct.args_translator is not None:
                self._nodes_structs_formal_args_list.append(
                    nd_struct.args_translator.formal_args_values)
            else:
                self._nodes_structs_formal_args_list.append(None)

    def update_args_translation_list(self, formal_args):
        """
        Receive a list of args name to be changed to formal args, and change them.

        Args:
            formal_args (list[str]): a list of args name to be changed to formal args.
        """
        self._node_args_translation_list = formal_args
        self._update_formal_args_for_all_nd_structs()

    def get_all_sub_translators(self):
        """
        Return a list of args_translators of submodules / nodes affiliated to this module.

        Note:
            The order of returned list is followed by the actual topological order.

        Returns:
            list, a list of args_translators.
        """
        ret = []
        for (_, struct) in self.get_generate_order():
            if struct.args_translator is not None:
                ret.append(struct.args_translator)
        return ret

    def get_generate_order(self):
        """
        Return the order of generated code by index.

        Return:
            list, a list of reference of node_struct or module_struct.
        """
        ret = list()
        if not self._module_structs:
            return self._node_structs
        # Generate a list of tuple (idx, module_structs)
        for md_struct in self._module_structs:
            ret.append((md_struct.head_nd_struct_index, md_struct))
        if self.node_structs:
            ret += self.node_structs
        ret.sort(key=lambda x: x[0])
        return ret

    def _code_line_init_statement_shared_weights_args(self):
        """Generate the args for shared weights where calling this module."""
        args_list = list()
        for passthrough_w_onnx_name, passthrough_w_var_name in self.shared_weights_collection.items():
            passthrough_w_var_name_in_parent = \
                self.parent_module_struct.shared_weights_collection.get(passthrough_w_onnx_name)
            if self.parent_module_struct.identifier == []: # now only consider declaration in main model
                args_list.append(f"{passthrough_w_var_name}=self.{passthrough_w_var_name_in_parent}")
            else:
                args_list.append(f"{passthrough_w_var_name}={passthrough_w_var_name_in_parent}")
        return args_list

    def _code_line_init_generate_shared_w_declaration_for_repeated(self):
        """Force to repeat sub nodes init code line for fulfillment of shared weight declaration in main model."""
        for _, nd_struct in self._node_structs:
            nd_struct.code_line_in_init()

    def code_line_in_init(self):
        """Initialization line of code in module init block."""
        self._code_line_init_generate_shared_w_declaration_for_repeated()
        left = "self.{}".format(self.ms_var_name)
        args_list = list()
        # Load args in init statement.
        if self._args_translator is not None:  # from args_translator
            if self._args_translator.actual_args:  # load actual args
                args_list += self._args_translator.actual_args_to_str_list
            elif self._args_translator.actual_args_backup and self.parent_id == -1:
                # For modules repeated in multiple levels, the module under main model should
                # not use formal args as it is unnecessary -> load from actual args backup
                args_list += self._args_translator.actual_args_backup_to_str_list
            args_list += self._args_translator.formal_args_to_str_list  # load from formal args
        else:
            args_list += self._fragment.actual_args
        args_list += self._code_line_init_statement_shared_weights_args()
        right = f"{self.class_name}({', '.join(args_list)})"
        return left, right

    def code_line_in_construct(self, inputs=None):
        """Construct line of code in module construct block."""
        outputs_edges = list(self.outputs_register.keys())
        num_output = len(outputs_edges)

        # Allocate opt_var_name
        if num_output == 1:  # single output
            left = [f"{self.ms_opt_var_name}"]
        else:
            left = [f"{self.ms_opt_var_name}_{num}" for num in range(num_output)]

        inputs = []
        # Update self's outputs mgr
        for idx, edge in enumerate(outputs_edges):
            base_out = self.outputs_manager.get_base_out(edge)
            if base_out.opt_var_name is None:
                print(f"ModuleStruct {self.identifier} has an output {base_out.onnx_edge_name} not has opt_var_name")
                base_out.opt_var_name = left[idx]
            self.parent_module_struct.internal_outputs_collection[base_out.onnx_edge_name] = base_out.opt_var_name

        # Take inputs from parent & previous
        for input_edge in self.inputs_register:
            if input_edge in self.parent_module_struct.inputs_register:
                inputs.append(self.parent_module_struct.inputs_register.get(input_edge))
            elif input_edge in self.parent_module_struct.internal_outputs_collection:
                inputs.append(self.parent_module_struct.internal_outputs_collection.get(input_edge))

        right = f"self.{self.ms_var_name}({', '.join(inputs)})"
        left = ", ".join(left)
        return (left, right)

    @property
    def node_structs(self):
        """Return all node structs in this module."""
        return self._node_structs

    @property
    def module_structs(self):
        """Return all module structs in this module."""
        return self._module_structs

    @property
    def parent_module_struct(self):
        """Return this module's parent module struct."""
        return self._parent_module_struct

    @parent_module_struct.setter
    def parent_module_struct(self, ref):
        """Set this modu;e's parent module struct."""
        self._parent_module_struct = ref

    @property
    def args_translator(self):
        """Return the args translator."""
        return self._args_translator

    @property
    def head_nd_struct_precursor_nodes_names(self) -> list:
        """Return head node's precursor nodes names."""
        return self.head_nd_struct.precursor_nodes_names

    @property
    def head_nd_struct_precursor_nodes_structs(self) -> list:
        """Return head node's precursor nodes structs."""
        return self.head_nd_struct.precursor_nodes_structs

    @property
    def tail_nd_struct_successor_nodes_names(self) -> list:
        """Return tail node's successor nodes names."""
        return self.tail_nd_struct.successor_nodes_names

    @property
    def tail_nd_struct_successor_nodes_structs(self) -> list:
        """Return tail node's successor nodes structs."""
        return self.tail_nd_struct.successor_nodes_structs

    @property
    def onnx_names_from_nodes(self) -> list:
        """Return all nodes onnx names in this module."""
        if self._global_context.build_struct_finished and "_onnx_names_from_nodes" in self.rapid_reference:
            return self.rapid_reference["_onnx_names_from_nodes"]
        ret = [node.onnx_name for (_, node) in self.node_structs]
        if self._global_context.build_struct_finished:
            self.rapid_reference["_onnx_names_from_nodes"] = ret
        return ret

    @property
    def onnx_names_from_submodules(self) -> list:
        """Return all nodes onnx names in submodules of this module."""
        if self._global_context.build_struct_finished and "_onnx_names_from_submodules" in self.rapid_reference:
            return self.rapid_reference["_onnx_names_from_submodules"]

        ret = []
        for md_struct in self.module_structs:
            ret += md_struct.onnx_names
        if self._global_context.build_struct_finished:
            self.rapid_reference["_onnx_names_from_submodules"] = ret

        return ret

    @property
    def onnx_names(self) -> list:
        """Return all nodes' onnx names which contained by this module."""
        if self._global_context.build_struct_finished and "_onnx_names" in self.rapid_reference:
            return self.rapid_reference["_onnx_names"]
        ret = self.onnx_names_from_nodes + self.onnx_names_from_submodules
        if self._global_context.build_struct_finished:
            self.rapid_reference["_onnx_names"] = ret
        return ret

    @property
    def external_precursor_nodes_names(self) -> list:
        """Return all precursors nodes names not in this module."""
        ret = []
        for _, struct in self.get_generate_order():
            if isinstance(struct, NodeStruct):
                precursor_nodes_names = struct.precursor_nodes_names

            if isinstance(struct, ModuleStruct):
                precursor_nodes_names = struct.external_precursor_nodes_names

            for p_name in precursor_nodes_names:
                if p_name in self.onnx_names:
                    continue
                ret.append(p_name)
        return ret

    @property
    def external_successor_nodes_names(self) -> list:
        """Return all successor nodes names not in this module."""
        ret = []
        for _, struct in self.get_generate_order():
            if isinstance(struct, NodeStruct):
                successor_nodes_names = struct.successor_nodes_names

            if isinstance(struct, ModuleStruct):
                successor_nodes_names = struct.external_successor_nodes_names

            for s_name in successor_nodes_names:
                if s_name in self.onnx_names:
                    continue
                ret.append(s_name)
        return ret

    @property
    def class_name(self) -> str:
        """Return the class name for generating code of this module."""
        if self.pattern_id == -1:
            return "Model"
        if self._global_context.known_module_name.get("Module{}".format(self.pattern_id)) is not None:
            class_name = self._global_context.known_module_name.get("Module{}".format(self.pattern_id))
        else:
            class_name = "Module{}".format(self.pattern_id)
        return class_name

    @property
    def ms_var_name(self) -> str:
        """Return the variable name for generated code statement of this module."""
        if self.pattern_id == -1:
            return "Model"
        return f"{self.class_name}_{self.pattern_uid}".lower()

    @property
    def ms_opt_var_name(self) -> str:
        """Return the variable name for generated code statement of the output of this module."""
        return "{}_opt".format(self.ms_var_name).lower()

    # The following part will be resetting nodes' external inputs for supporting multi-in/out
    # and should be called after generator.recursive_form_modules()

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
            raise ValueError("The input from {} has already registered. Check this Module \
                {} has duplicate inputs or not.".format(onnx_precursor_node_name, self.identifier))
        self.inputs_in_construct_header[onnx_precursor_node_name] = header_x

    def allocate_construct_header_x(self, force_x=None):
        """
        Allocate the x in construct header for each external input.

        Args:
            force_x (str): Force the arg name to customized.
        """
        local_x_name = 'x'
        if force_x:  # name of x indicated by external
            local_x_name = force_x

        # set construct_header_x for current module
        allocated = set()
        for prec_name in self.external_precursor_nodes_names:
            if prec_name in allocated:
                continue
            x_name_in_construct_header = self._var_name_mgr.get_name(local_x_name)
            self.construct_header_x[x_name_in_construct_header] = prec_name
            allocated.add(prec_name)

        # Assign these inputs to nodes and submodules
        for _, struct in self.get_generate_order():
            if isinstance(struct, NodeStruct):  # register node's ext input
                self.reset_node_external_input_to_local(struct)
                self.register_node_output_to_module(struct)
            if isinstance(struct, ModuleStruct):  # reg module's ext input
                if not struct.construct_header_x:
                    struct.allocate_construct_header_x()
                self.reset_submodule_external_input_to_local(struct)
                self.register_submodule_output_to_module(struct)

        # remove parent module's ext. map if ext nodes in this module (no need return)
        for user_name in self.external_successor_local_returns_map.copy().keys():
            if user_name in self.onnx_names:
                self.external_successor_local_returns_map.pop(user_name)

    def _match_node_inputs(self, struct):
        """Match node's inputs with its precursor nodes."""
        for output_provider in struct.precursor_nodes_names:
            output_list = self.outputs_collection.get(output_provider)
            if output_list is None:
                # not in this module, check construct header
                for (self_x_name, self_output_provider) in self.construct_header_x.items():
                    if self_output_provider == output_provider:
                        struct.matched_inputs.append(self_x_name)
                continue
            for output in output_list:
                (provider_succ, provider_closet_opt_var) = output
                if provider_closet_opt_var in struct.matched_inputs:
                    continue  # skip repeat
                if provider_succ == struct.onnx_name:
                    struct.matched_inputs.append(provider_closet_opt_var)

    def _match_sub_modules_inputs(self):
        """
        Match current module's submodules' inputs with corresponding outputs registered in current module.

        Description:
            The function matches these inputs by the following steps:
            1. For each submodule in the current module, take submodule's construct header
            2. Check submodule's construct header element requires an input from current module's
                construct header or outputs from other submodules.
            3. If from current module's construct header, assign corresponding x to the submodule.
                If from other submodules, assign required submodule output name to the submodule.
        """
        if not self.outputs_collection:
            return  # skip first node
        for (_, struct) in self.get_generate_order():
            if isinstance(struct, NodeStruct):
                self._match_node_inputs(struct)
                continue  # skip node
            sub_construct_header = struct.construct_header_x
            for (_, output_provider) in sub_construct_header.items():
                # check from outputs collection
                output_list = self.outputs_collection.get(output_provider)
                if output_list is None:
                    # not in this module, need from current module construct header
                    for (self_x_name, self_output_provider) in self.construct_header_x.items():
                        if self_output_provider == output_provider:
                            struct.matched_inputs.append(self_x_name)
                    continue
                for output in output_list:
                    (provider_succ, provider_closet_opt_var) = output
                    if provider_closet_opt_var in struct.matched_inputs:
                        continue  # skip repeat
                    if provider_succ in struct.onnx_names:
                        struct.matched_inputs.append(provider_closet_opt_var)

    def _append_to_outputs_collection(self, provider_name, val):
        """
        Helper function to add a nodes or submodules outputs to current module return statement.

        Args:
            provider_name (str): The onnx name of the output provider.
            val (list[tuple]): A list of tuple which contains
                the output provider's successor name and its opt_var_name.
        """
        exist_output = self.outputs_collection.get(provider_name)
        if isinstance(val, tuple):
            val = [val]
        if exist_output is None:  # add new entry
            exist_output = list()
        exist_output += (val)
        self.outputs_collection[provider_name] = exist_output

    def collect_returns(self):
        """
        Collect all nodes and submodules' returns in the module.

        Note:
            The logic is to collect the return from nodes and submodules by the order
            of topological index.

            For returns from a node, it will check if the return will be used externally.
            If external (external means the successor a.k.a the return user has different scope with the node),
            add this return to current module's outputs_collection, where
            key is this node's original onnx_name, and value is a list of
            tuple(successor_name, this node's opt_var_name)

            For returns from a submodule, it will check if the submodule has already collected returns,
            If not, do it and then continue the following procedures.
            Now we will check each element in submodule's outputs_collection. Note that we DO NOT check submodule's
            returns should be continued returning, but just return them.
            All these returns from submodules will be changes their original nodes output (a.k.a outputs provider)
            `opt_var_name` to submodules' `opt_var_name`.

            Finally, we match the outputs and inputs in the current module level.
        """
        for (_, struct) in self.get_generate_order():
            if isinstance(struct, NodeStruct):
                outputs_list = []
                # add these successor nodes name to collection for future use
                for succ in struct.successor_nodes_names:
                    outputs_list.append((succ, struct.ms_opt_var_name))
                if outputs_list:
                    self._append_to_outputs_collection(struct.onnx_name, outputs_list)
            if isinstance(struct, ModuleStruct):
                # Remove unnecessary returns, succ are all inside current
                if not struct.outputs_collection:
                    struct.collect_returns()
                sub_outputs_collection = struct.outputs_collection
                # check each returns in sub
                for provider_name, outputs_list in sub_outputs_collection.items():
                    for output in outputs_list:
                        (succ, _) = output  # (succ, provider_opt_var_name) in output
                        new_output = (succ, struct.ms_opt_var_name)
                        self._append_to_outputs_collection(provider_name, new_output)
        self._match_sub_modules_inputs()

    def get_returned_opt_var_name(self) -> list:
        """Return a list of returned output var of this module."""
        idx = 0
        added_to_return = set()
        ret = []
        for ext_successor_requested, opt_var_name_in_this_module in self.external_successor_local_returns_map.items():
            if ext_successor_requested in added_to_return:
                continue
            ret.append((ext_successor_requested, opt_var_name_in_this_module, idx))
            added_to_return.add(ext_successor_requested)
        return ret

    def reset_node_external_input_to_local(self, nd_struct):
        """
        Reset node's input to module's construct args
        """
        for prec_node_name in nd_struct.precursor_nodes_names_external:
            if prec_node_name in self.onnx_names:  # prec node in current module's.
                continue
            if prec_node_name in self.construct_header_x.values():
                # prec node assigned to construct header to passed in.
                local_x = get_dict_key_by_value(prec_node_name, self.construct_header_x)
                nd_struct.set_inputs_in_construct_header(local_x, prec_node_name)
            else:  # Extra precursor nodes, raise error
                raise ValueError("Found external inputs of the Node but the module does not have it.")

    def reset_submodule_external_input_to_local(self, md_struct):
        """
        Reset submodule's external input to current module.

        Args:
            md_struct (ModuleStruct): The submodule in the current module.
        """
        # check submodule's input
        for _, submodule_precursor in md_struct.construct_header_x.items():
            if submodule_precursor in self.onnx_names:  # if internal, match with local nodes/submodules return
                # but do nothing here
                continue
            # if external, match with current module construct header x
            if submodule_precursor in self.construct_header_x.values():
                local_x = get_dict_key_by_value(submodule_precursor, self.construct_header_x)
                md_struct.set_inputs_in_construct_header(local_x, submodule_precursor)
            else:  # Extra precursor nodes, raise error
                raise ValueError("Found external inputs of the submodule but the module does not have it.")

    def register_node_output_to_module(self, nd_struct):
        """Register nodes outputs to this module's return."""
        for succ_node_name in nd_struct.successor_nodes_names_external:
            self.external_successor_local_returns_map[succ_node_name] = nd_struct.ms_opt_var_name

    def register_submodule_output_to_module(self, md_struct):
        """Register submodule outputs to this module's return."""
        submodule_returns = md_struct.get_returned_opt_var_name()
        submodule_opt_var_name = md_struct.ms_opt_var_name
        for (submodule_ext_succ, _, ith_output) in submodule_returns:
            self.external_successor_local_returns_map[submodule_ext_succ] = (submodule_opt_var_name, ith_output)

    # The following funcs are designated to be invoked by matcher.
    def add_inputs_edge(self, edge_name: str):
        construct_header_length = len(self.inputs_register.values())
        default_x_str = "x"
        if not edge_name in self.inputs_register:
            self.inputs_register[edge_name] = "".join([default_x_str, str(construct_header_length-1)]) \
                if construct_header_length > 0 else default_x_str

    def add_outputs_edge(self, edge_name: str):
        if edge_name in self.outputs_register:
            return        # to be filled during code generation, should from sub's opt_var_name
        self.outputs_register[edge_name] = "<placeholder>"

    def fill_outputs_edge(self, edge_name: str, opt_var_name: str):
        # FILL the outputs edge once you got a opt_var_name of corresponding node!!!
        if not edge_name in self.outputs_register:
            raise ValueError(f"ModuleStruct {self.identifier} does not have edge "\
                             f"{edge_name} and unable to fill its output var name.")
        if self.outputs_register[edge_name] != "<placeholder>":
            raise ValueError(f"The edge has been already filled as {self.outputs_register[edge_name]}" \
                             f" instead of your {opt_var_name}")
        self.outputs_register[edge_name] = opt_var_name
