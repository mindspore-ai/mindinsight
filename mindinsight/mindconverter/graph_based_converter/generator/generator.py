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
"""Main Generator module."""
import copy
from collections import OrderedDict
from importlib import import_module

import numpy as np
from yapf.yapflib.yapf_api import FormatCode

from mindinsight.mindconverter.common.exceptions import GeneratorError
from mindinsight.mindconverter.graph_based_converter.generator.scope_utils import Scope
from mindinsight.mindconverter.graph_based_converter.generator.node_struct import NodeStruct
from mindinsight.mindconverter.graph_based_converter.generator.module_struct import ModuleStruct
from mindinsight.mindconverter.graph_based_converter.generator.args_translator import ArgsTranslationHelper
from mindinsight.mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindinsight.mindconverter.graph_based_converter.common.outputs import BaseOutput, ModuleOutputManager
from mindinsight.mindconverter.graph_based_converter.common.yapf_config import mindspore_yapf_config
from mindinsight.mindconverter.graph_based_converter.common.name_mgr import GlobalVarNameMgr
from mindinsight.mindconverter.graph_based_converter.constant import NEW_LINE, SECOND_LEVEL_INDENT, \
    FIRST_LEVEL_INDENT, get_imported_module, SEPARATOR_BTW_NAME_AND_ID, WeightType, LINK_IN_WEIGHT_NAME
from mindinsight.mindconverter.graph_based_converter.report_generator import ReportGenerator
from mindinsight.mindconverter.graph_based_converter.common.utils import replace_string_in_list
from mindinsight.mindconverter.graph_based_converter.generator.matcher import MatcherLauncher
from mindinsight.mindconverter.graph_based_converter.generator.shared_weights import SharedWeightHelper


class CodeStruct:
    """
    Define the Code template for each module generated in the final output.
    Each module has only one CodeStruct to its pattern.
    """
    NOT_IN_SCOPE_OPT = dict()

    def __init__(self, struct, repeated_submodules=None):
        """Initialize the CodeStruct."""
        self.code_line_list = list()  # list of code line, a item is a line.
        self._global_var_mgr = GlobalVarNameMgr()  # var name procs within same module

        if isinstance(struct, ModuleStruct):
            self._generate_from_module_struct(struct, repeated_submodules)

    def _add_line(self, s):
        """Add line of code."""
        self.code_line_list.append(s)

    @property
    def new_line(self):
        """Return last generated line."""
        try:
            return self.code_line_list[-1]
        except IndexError:
            return ""

    @new_line.setter
    def new_line(self, s):
        """Make a new line."""
        self._add_line(s)

    def _generate_from_module_struct(self, md_struct, repeated_submodules):
        """
        Generate the code of current Module Struct, collecting data from submodules.

        Args:
            md_struct (ModuleStruct): The ModuleStruct which generates codes.
            repeated_submodules (dict): The dict contains all submodules which use repeatedly.
                Can get this dict from generator.
        """

        # Define Module header code line below
        class_name = md_struct.class_name
        # define a class declaration
        self.new_line = f"class {class_name}(nn.Cell):"

        # Get all formal args from nodes
        module_def_args = ['self']
        if md_struct.args_translator.actual_args:
            for actual in md_struct.args_translator.actual_args.keys():
                module_def_args.append(actual)
        if md_struct.args_translator.formal_args:
            for formal in md_struct.args_translator.formal_args.keys():
                module_def_args.append(formal)

        # set passthrough weights for shared weights, no need for main model
        if md_struct.identifier != []:
            module_def_args = SharedWeightHelper.add_shared_weights_in_init_statement(md_struct, module_def_args)

        # For code line in init  & construct blocks
        init_lines = list()
        cons_lines = list()
        for (_, struct) in md_struct.get_generate_order():
            if isinstance(struct, NodeStruct):  # Generate code line for Node.
                _ = struct.code_line_in_init()
                _ = struct.code_line_in_construct()

                init_str, cons_str = struct.fragment.fragment()
                init_str = [f"{SECOND_LEVEL_INDENT}{x}" for x in init_str]
                cons_str = [f"{SECOND_LEVEL_INDENT}{x}" for x in cons_str]
                code_line_construct = cons_str
                init_lines += init_str
                cons_lines += cons_str

            else: # is ModuleStruct
                # check if this instance generated CodeStruct
                if GlobalContext().code_structs.get(struct.pattern_id) is None:
                    CodeStruct(struct, repeated_submodules)

                code_line_init = struct.code_line_in_init()
                code_line_construct = struct.code_line_in_construct(inputs=struct.matched_inputs)
                init_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_init)}")
                cons_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_construct)}")

        # define header of init block
        self.new_line = f"{FIRST_LEVEL_INDENT}def __init__({', '.join(module_def_args)}):"
        self.new_line = f"{SECOND_LEVEL_INDENT}super({class_name}, self).__init__()"

        #add shared weights declaration in init code part
        if md_struct.identifier == []:
            passthrough_w_declaration = SharedWeightHelper.public_module_shared_weight_statement_generation(md_struct)
            for s in passthrough_w_declaration:
                self.new_line = f"{SECOND_LEVEL_INDENT}{s}"

        # add init code lines to code line list.
        self.code_line_list += init_lines
        self.new_line = f"{NEW_LINE * 2}"

        # define header of construct block
        inputs = ['self'] + list(md_struct.inputs_register.values())
        self.new_line = f"{FIRST_LEVEL_INDENT}def construct({', '.join(inputs)}):"
        # add construct code lines to code line list.
        self.code_line_list += cons_lines
        # define returns
        returns = []

        # take opt_var_name to return_list
        for output_edge in md_struct.outputs_register.keys():
            opt_var_name = md_struct.internal_outputs_collection.get(output_edge)
            if opt_var_name is None:
                raise ValueError(f"Module {md_struct.identifier} has an output {output_edge} has unknown opt_var_name.")
            returns.append(opt_var_name)

        self.new_line = f"{SECOND_LEVEL_INDENT}return {', '.join(returns)}"
        self.new_line = f"{NEW_LINE * 2}"
        GlobalContext().code_structs[md_struct.pattern_id] = self


class Generator:
    """The generator controls all routines of code generation."""

    def __init__(self):
        """Init the generator."""
        # define MUST have params
        self._node_struct_collections = OrderedDict()
        self._module_struct_collections = OrderedDict()
        self._module_depth_max = 0
        self._module_depth_min = 0

        # define intermediate var. during conversion
        self._module_map = OrderedDict()
        self._global_context = GlobalContext()
        self._global_context.node_struct_collections = self._node_struct_collections
        self._repeated_submodules = set()

    @GeneratorError.check_except("Generator occurs an error when forming base submodules.")
    def _form_bottom_submodule(self):
        """Form the basic submodules, which only contains nodes."""
        # Form module map
        curr_scope_path = None
        nd_struct_list_in_submodule = []
        for nd_struct in self.node_structs.values():
            idx = nd_struct.topo_idx
            if curr_scope_path is None:
                curr_scope_path = nd_struct.scope.path
                nd_struct_list_in_submodule.append((idx, nd_struct))
            elif curr_scope_path == nd_struct.scope.path:
                nd_struct_list_in_submodule.append((idx, nd_struct))
            else:  # curr_scope_path changed
                # save this submodule
                if self._module_map.get(str(curr_scope_path)) is not None:
                    self._module_map[str(curr_scope_path)] += nd_struct_list_in_submodule
                else:
                    self._module_map[str(curr_scope_path)] = nd_struct_list_in_submodule

                # create a new one
                curr_scope_path = nd_struct.scope.path
                nd_struct_list_in_submodule = [(idx, nd_struct)]

        # save last submodule
        if self._module_map.get(str(curr_scope_path)) is not None:
            self._module_map[str(curr_scope_path)] += nd_struct_list_in_submodule
        else:
            self._module_map[str(curr_scope_path)] = nd_struct_list_in_submodule

        # Form bottom modules' ModuleStruct
        for scope_path_str, nd_struct_list in self._module_map.items():
            self._module_struct_collections[scope_path_str] = ModuleStruct(nd_struct_list)

    def _list_repeated_submodules(self) -> OrderedDict:
        """
        Return the repeated submodules by its depth and num.
        For example, "Model/Module3_3" will return {1:(3)}

        Return:
            OrderedDict, a dict contains collections of repeated submodules.
        """
        ret = OrderedDict()
        for depth_control in range(self._module_depth_max, 0, -1):
            repeated_submodules_at_this_depth = set()
            for scope_path in self._module_map.keys():
                path = Scope.path_str_to_list(scope_path)
                if len(path) < depth_control:
                    continue
                # depth control within path length.
                module_num = path[depth_control - 1][0]
                repeated_submodules_at_this_depth.add(module_num)
            ret[depth_control] = repeated_submodules_at_this_depth

        self._repeated_submodules = ret
        return ret

    def _compare_with_base_parameters(self, nd_struct_list):
        """
        Compare the parameter to check if it should be a formal args.

        Args:
            nd_struct_list (list): A list of NodeStructs which contains
                                    all same nodes in repeated submodules.

        Return:
            set, a set of all formal args in this node.
        """

        formal_args = set()
        if len(nd_struct_list) < 2:
            return formal_args
        (_, base_nd_struct) = nd_struct_list[0]
        for (base_parameter, base_value) in base_nd_struct.fragment.default_var["args"].items():  # for each param
            for (_, nd_struct) in nd_struct_list[1:]:
                compared_value = nd_struct.fragment.default_var["args"].get(base_parameter)
                if compared_value == base_value:
                    continue
                formal_args.add(base_parameter)
                break

        return formal_args

    @staticmethod
    def _set_translated_args_for_unshared_weights(t_param_postfix, nd_struct_list):
        """Set the weight with given param postfix to args translation."""
        for _, nd_struct in nd_struct_list:
            nparr = nd_struct.fragment.default_var["trainable_params"].get(t_param_postfix).get('data')
            nd_struct.fragment.default_var["args"][f"{t_param_postfix}_shape"] = nparr.shape
            nd_struct.fragment.default_var["args"][f"{t_param_postfix}_dtype"] = nparr.dtype
            init_tensor_template = f"Parameter(Tensor(np.random.uniform(0, 1, "\
                                    f"{{{t_param_postfix}_shape}}).astype(np.{{{t_param_postfix}_dtype}})), "\
                                    f"name=None)"
            nd_struct.fragment.default_var["parameters"][t_param_postfix] = init_tensor_template

    def _get_same_trainable_params_onnx_name_from_repeated_nodes(self,
                                                                 t_param_postfix,
                                                                 t_param_data_dict,
                                                                 nd_struct_list: list):
        """Return all onnx names from the same weights in repeated nodes."""
        (_, base_nd_struct) = nd_struct_list[0]
        t_base_name = t_param_data_dict.get('onnx_name')
        t_onnx_names = [t_base_name]
        for (_, nd_struct) in nd_struct_list[1:]:
            compared_t_param_data_dict = nd_struct.fragment.default_var["trainable_params"].get(t_param_postfix)
            if not compared_t_param_data_dict:
                raise ValueError(f"Inconsistent trainable params detected for node "\
                                    f"{nd_struct.topo_idx} with base node {base_nd_struct.topo_idx}")
            compared_t_name = compared_t_param_data_dict.get('onnx_name')
            t_onnx_names.append(compared_t_name)
        return t_onnx_names

    def _partial_shared_weights_in_repeated_submodule_procs(self, nd_struct_list):
        """
        Check each node in repeated submodule to ensure the node has a fully / partial shared weight.

        Args:
            nd_struct_list (list): A list of node structs which are same node in repeated modules.
        """
        # Not repeated will skip this function
        if len(nd_struct_list) < 2:
            return
        (_, base_nd_struct) = nd_struct_list[0]
        shared_w_list = self._global_context.repeated_weights.keys()
        if not shared_w_list:
            if base_nd_struct.fragment.default_var.get("parameters"):
                # set only if has parameters as it requires rewritten.
                for (t_param_postfix, t_param_data_dict) in \
                    base_nd_struct.fragment.default_var["trainable_params"].items():
                    if not isinstance(t_param_data_dict.get('data'), np.ndarray):
                        continue
                    Generator._set_translated_args_for_unshared_weights(t_param_postfix, nd_struct_list)
            return

        for (t_param_postfix, t_param_data_dict) in base_nd_struct.fragment.default_var["trainable_params"].items():
            # check each weight if partial shared or fully shared weight
            if not t_param_data_dict:
                continue
            t_onnx_names = self._get_same_trainable_params_onnx_name_from_repeated_nodes(t_param_postfix,
                                                                                         t_param_data_dict,
                                                                                         nd_struct_list)
            t_shared_status = [name in shared_w_list for name in t_onnx_names]
            if True in t_shared_status and False in t_shared_status:
                # is partial shared, set unshared to fake shared in GlobalContext
                for idx, (name, status) in enumerate(zip(t_onnx_names, t_shared_status)):
                    if status:
                        # actual shared, do nothing, skip
                        continue
                    node_onnx_name = nd_struct_list[idx][1].onnx_name
                    if not self._global_context.repeated_weights.get(name):
                        self._global_context.repeated_weights[name] = [node_onnx_name]
                    else:
                        self._global_context.repeated_weights[name] += [node_onnx_name]
            if True not in t_shared_status and base_nd_struct.fragment.default_var.get("parameters"):
                # if the repeated node is not shared weight and the mapper accept parameters rewritten.
                if not isinstance(t_param_data_dict.get('data'), np.ndarray):
                    continue
                Generator._set_translated_args_for_unshared_weights(t_param_postfix, nd_struct_list)


    def _list_formal_parameters_in_a_module(self, module_filter_return):
        """
        Find all formal args / params from nodes in a module.

        Args:
            module_filter_return (dict): The filtered results from the module_map_filter.

        Return:
            list, a list of sets or None indicates all formal args of each node in the module in order.
        """
        formal_params_list = list()
        transposed = [list(e) for e in zip(*module_filter_return)]
        for operation in transposed:
            # use the map filtered result for partial shared weights procs
            self._partial_shared_weights_in_repeated_submodule_procs(operation)
        for operation in transposed:
            formal_parameters = self._compare_with_base_parameters(operation)
            if formal_parameters:
                formal_params_list.append(formal_parameters)
            else:
                formal_params_list.append(None)
        return formal_params_list

    def _list_formal_parameters(self, repeated_submodules) -> dict:
        """
        Return a list of formal parameters in each submodule.

        Args:
            repeated_submodules (dict): A dict which contains repeated submodules,
                                        acquire this dict from _list_repeated_submodules()

        Return:
            OrderedDict, a dict with each submodule's formal args.

        Example:
            A return for ResNet50 could be:

            {0: # submoodule 0
             [set('stride', 'in_channels', 'out_channels'), # args of the first node to be set as formal
              set('num_features'), # args of the second node to be set as formal
              None, # args of third node to be set as formal, which does not have
              set('in_channels', 'out_channels'),
              set('num_features'),
              None
             ]},
            {3: # submodule 3
             [...],
            {5: # submodule 5
             []} # empty returns means no nodes or it's a parent module of submodules.
            }
        """
        formal_args_in_each_submodule = OrderedDict()
        checked_module = set()
        # filter module_map by submodule_num (without depth)
        for _, module_nums in repeated_submodules.items():
            for module_num in module_nums:
                if module_num in checked_module:  # module already checked
                    continue
                checked_module.add(module_num)
                map_filtered = self.module_map_filter(module_num=module_num)
                formal_args_in_this_module = self._list_formal_parameters_in_a_module(map_filtered)
                formal_args_in_each_submodule[module_num] = formal_args_in_this_module
        return formal_args_in_each_submodule

    def _add_submodule_to_parent(self):
        """
        Recursively add all submodule to its parent module until Main module.

        Note:
            This function deepcopy the first node of the submodule, and reset its params as parent module.
        """
        depth = self._module_depth_max
        while depth > 0:
            for (scope_path_str, md_struct) in self.module_structs.copy().items():
                if scope_path_str == '[]':
                    continue  # is main module, skip
                if md_struct.scope_depth != depth:
                    continue  # skip all submodules not at current depth
                md_struct_scope = copy.deepcopy(md_struct.identifier)
                md_struct_scope.pop()
                parent_scope = md_struct_scope
                # 1. check if this module has parent module
                parent_md_struct = self.module_structs.get(str(parent_scope))
                if parent_md_struct is not None:
                    # 1A. has parent, directly add md_struct to its parent ModuleStruct.
                    parent_md_struct.add_submodule(md_struct)
                    self.module_structs[str(parent_scope)] = parent_md_struct
                else:
                    # 1B. not has parent, generate a new ModuleStruct
                    # use this submodule to create a parent module
                    parent_md_struct = ModuleStruct(None, init_as_parent=True, parent_base=md_struct)
                    # rewrite parent md struct
                    parent_md_struct.add_submodule(md_struct)
                    self.module_structs[str(parent_scope)] = parent_md_struct
                sub = self.module_structs.pop(scope_path_str)  # remove this submodule from collections
                self._global_context.add_module_struct(sub.pattern_id, sub)
            depth -= 1

    @GeneratorError.check_except("Generator occurs an error when building modules.")
    def _recursive_form_module(self):
        """Main routine in generator to build modules from bottom to top."""
        # 1. List repeated submodules
        repeated_submodules = self._list_repeated_submodules()
        # 2. List reused parameters
        formal_parameters = self._list_formal_parameters(repeated_submodules)
        # 3. Build base subdmodules and set in/ext params translation
        for module_struct in self.module_structs.values():
            if module_struct.pattern_id == -1:  # is main module
                continue
            formal_args = formal_parameters.get(module_struct.pattern_id)
            module_struct.update_args_translation_list(formal_args)

        # 4. Form parent modules
        md_collection_len = len(self.module_structs.keys())
        len_changes = True
        while len_changes:
            self._add_submodule_to_parent()
            new_len = len(self.module_structs.keys())
            if md_collection_len != new_len:
                md_collection_len = new_len
            else:
                len_changes = False
        GlobalContext().build_struct_finished = True
        # 5. Update all translated args from module map
        self._update_all_modules_args_translator()

        # 6. Update all nodes and moudles input/output
        self.build_outputs_connection()
        self.module_structs.get('[]').allocate_construct_header_x()
        self.module_structs.get('[]').collect_returns()

        matcher = MatcherLauncher(self.module_structs.get('[]'))
        matcher.matching_process()

        for nd_struct in self.node_structs.values():
            if nd_struct.fragment.metadata.get("operation") == "Split":
                self._split_op_procs(nd_struct)

    def _shared_weights_processing(self):
        """Process shared weights."""
        # check each node has shared weight
        for nd_struct in self.node_structs.values():
            shared_weights = SharedWeightHelper.check_node_has_shared_weight(nd_struct)
            if shared_weights:
                # register each shared weight to public module
                for shared_w in shared_weights:
                    SharedWeightHelper.register_shared_weight_to_public_parent(nd_struct,
                                                                               shared_w,
                                                                               pub_module_identifier=[])

    def _update_all_modules_args_translator(self):
        """Update all modules' args translators."""
        done_submodule = set()
        for depth in range(self._module_depth_max, 0, -1):
            # check modules from bottom to top
            repeated_submodules = copy.deepcopy(self._repeated_submodules)
            repeated_modules = repeated_submodules.get(depth)
            if depth is None:
                continue
            for pattern_id in repeated_modules:
                if pattern_id in done_submodule:
                    continue
                # get all md_structs by same pattern
                md_list = self._global_context.module_structs.get(pattern_id)
                self._take_formal_args_from_updated_submodules(md_list)
                args_translators = self.get_args_translator_from_module_structs_list(md_list)
                formal_args_list = ArgsTranslationHelper.find_formal_args_in_modules(args_translators)
                changed_args_translators = self.get_args_translator_from_module_structs_list(
                    md_list, exclude_root_son=True)
                ArgsTranslationHelper.change_args_to_formal_for_all_translators(
                    formal_args_list, changed_args_translators)
                done_submodule.add(pattern_id)

    def _take_formal_args_from_updated_submodules(self, md_list):
        """
        Take formal args from provided modules' nodes and submodules.

        Args:
            md_list (list): A list of ModuleStruct.
        """
        if isinstance(md_list, ModuleStruct):
            md_list = [md_list]

        for md in md_list:
            md.args_translator.take_formal_args_from_nodes_and_submodules(md.get_all_sub_translators())

    def _update_module_depth_max(self, nd_struct: NodeStruct):
        """
        Update the Generator attribute module_depth_max, which is the maximum depth in the Model.

        Args:
            nd_struct (NodeStruct): NodeStruct to be checked its depth.
        """
        depth = nd_struct.scope.depth
        if isinstance(depth, int):
            if depth > self._module_depth_max:
                self._module_depth_max = depth
        else:
            raise TypeError("Unable to update global depth due to TypeError in NodeStruct.scope.depth")

    def add_node(self, node_identifier, node_instance=None, node_fragment=None):
        """
        Add Node information to the generator.

        Args:
            node_identifier (str): The unique identifier for the node passed in.
            node_instance (GraphNode): The GraphNode instance of each node.
            node_fragment (NodeFragment): The NodeFragment instance of this node passed in.
        """

        if node_identifier is None:
            raise ValueError("Node Identifier should not be None.")
        self._global_context.node_fragments[node_identifier] = node_fragment
        args = []
        if node_instance is not None:
            args.append(node_instance)
        if node_fragment is not None:
            args.append(node_fragment)

        nd_struct = self.node_structs.get(node_identifier)
        if nd_struct:  # NodeStruct already exists
            nd_struct.update(args)
        else:  # create new Node Struct
            nd_struct = NodeStruct(args)
            nd_struct.identifier = node_identifier
            self._update_module_depth_max(nd_struct)
            self.node_structs[node_identifier] = nd_struct

    @property
    def node_structs(self):
        """Return all NodeStructs in this model."""
        return self._node_struct_collections

    @property
    def module_structs(self):
        """Return all ModuleStructs in this model."""
        return self._module_struct_collections

    def generate_weight_scope_name(self, node):
        """Generate weight scope name for checkpoint."""
        replaced_module_dict = self.node_structs[node].global_context_mgr.known_module_name
        scope_list = self.node_structs[node].scope.scope_list
        ms_var_name = self.node_structs[node].ms_var_name

        weight_scope_name = None
        for scope in scope_list[1:]:
            replaced_module = replaced_module_dict.get(scope.split(SEPARATOR_BTW_NAME_AND_ID)[0])
            if replaced_module:
                scope = scope.replace(scope.split(SEPARATOR_BTW_NAME_AND_ID)[0], replaced_module)
            if not weight_scope_name:
                weight_scope_name = scope
            else:
                weight_scope_name = '.'.join((weight_scope_name, scope))

        if not weight_scope_name:
            weight_scope_name = ms_var_name
        else:
            weight_scope_name = '.'.join((weight_scope_name, ms_var_name))

        return weight_scope_name.lower()

    def generate_checkpoint(self):
        """Generate checkpoint."""

        mindspore = import_module('mindspore')
        trainable_weights_dict = dict()
        weight_map = list()
        for node_name, node_inst in self.node_structs.items():
            if node_inst.fragment.exchange_msg['var_0']['trainable_params']:
                weights_scope_name = self.generate_weight_scope_name(node_name)
                onnx_weight_inst = node_inst.fragment.exchange_msg['var_0']['weights']
                for idx, (weight_key, weight_value_object) in \
                        enumerate(node_inst.fragment.exchange_msg['var_0']['trainable_params'].items()):
                    value_type = weight_value_object.get('type', WeightType.COMMON.value)
                    value_data = weight_value_object['data']
                    if value_type == WeightType.PARAMETER.value:
                        weight_name = SEPARATOR_BTW_NAME_AND_ID.join((weights_scope_name, weight_key))
                    else:
                        weight_name = LINK_IN_WEIGHT_NAME.join((weights_scope_name, weight_key))
                    weight_shape = mindspore.Tensor(value_data).shape
                    data_type = mindspore.Tensor(value_data).dtype
                    trainable_weights_dict[weight_name] = value_data

                    onnx_weight_name = onnx_weight_inst[idx].name
                    onnx_weight_shape = onnx_weight_inst[idx].value.shape
                    onnx_data_type = onnx_weight_inst[idx].value.dtype

                    weight_map.append(
                        {
                            'converted_weight': {
                                'name': weight_name,
                                'shape': weight_shape,
                                'data_type': str(data_type)
                            },
                            'source_weight': {
                                'name': onnx_weight_name,
                                'shape': onnx_weight_shape,
                                'data_type': str(onnx_data_type)
                            }
                        }
                    )

        save_obj = list()
        for weight_name, weight_value in trainable_weights_dict.items():
            obj = {
                'name': weight_name,
                'data': mindspore.Tensor(weight_value)
            }
            save_obj.append(obj)

        return save_obj, weight_map

    @GeneratorError.check_except("Generator occurs an error when generating code statements.")
    def generate(self):
        """
        Generate the final script file.

        Returns:
            list, a list of each line in script file.
        """
        self._form_bottom_submodule()
        self._recursive_form_module()
        self._shared_weights_processing()

        ckpt_data_list, weight_map = self.generate_checkpoint()

        CodeStruct(self.module_structs.get('[]'), self._repeated_submodules)

        outputs = [get_imported_module()]

        for code_struct in self._global_context.code_structs.values():
            for line in code_struct.code_line_list:
                outputs.append(line)

        formatted_code, _ = FormatCode("\n".join(outputs),
                                       style_config=mindspore_yapf_config())

        report_generator = ReportGenerator()
        report = report_generator.gen_report(formatted_code)
        del self._global_context

        return {"model": (formatted_code, report, ckpt_data_list, weight_map)}

    def get_node_struct(self, node_identifier):
        """
        Get specific NodeStruct by node_identifier.

        Args:
            node_identifier (str): The node unique identifier.

        Return:
            NodeStruct, the node's NodeStruct.
        """
        return self._node_struct_collections.get(node_identifier, None)

    def get_module_struct(self, module_identifier):
        """
        Get specific ModuleStruct by module_identifier.

        Args:
            module_identifier (str): The module unique identifier.

        Return:
            ModuleStruct, the node's ModuleStruct.
        """
        return self._module_struct_collections.get(module_identifier, None)

    def get_args_translator_from_module_structs_list(self, md_list, exclude_root_son=False):
        """
        Return a list of args translators which belongs to given module structs.

        Args:
            md_list (list): A list of ModuleStruct.
            exclude_root_son (Bool): If the returned result should include args translator belongs to
                modules under the Main module.

        Returns:
            list, a list of args translators which belongs to given module structs.
        """
        ret = []
        for md in md_list:
            if exclude_root_son and md.parent_id == -1:
                continue
            if md.args_translator is not None:
                ret.append(md.args_translator)

        return ret

    def module_map_filter(self, depth=None, module_num=None, uid=None):
        """
        Filter the module map by given conditions.

        Args:
            depth (int): Scope depth.
            module_num (int): The submodule number.
            uid (int): The unique identifier of a submodule.

        Return:
            list, list of NodeStruct list of each submodule.
        """
        ret = list()
        for scope_path, nd_struct_list in self._module_map.items():
            path = Scope.path_str_to_list(scope_path)
            if not path:  # skip main
                continue

            # if depth not equals to the indicated depth, skip
            if depth is not None and len(path) != depth:
                continue

            scope_at_depth = path[-1]
            (m_num, m_uid) = scope_at_depth
            if uid is not None:
                if m_num == module_num and m_uid == uid:
                    ret.append(nd_struct_list)
            else:
                if m_num == module_num:
                    ret.append(nd_struct_list)
        return ret

    def build_outputs_connection(self):
        """Build all nodes and modules outputs connections."""
        for nd_struct in self.node_structs.values():
            # for each output in curr node output manager
            for out in nd_struct.outputs_manager.outputs:
                # Set the onnx output edge name to this output
                self._global_context.outputs_storage.add_output(out)
                self._global_context.outputs_storage.add_onnx_node_name(out.onnx_edge_name,
                                                                        nd_struct.fragment.metadata.get('source'))
                self._global_context.outputs_storage.add_ms_identifier(out.onnx_edge_name, nd_struct.identifier)

            # Set input with existing output mapping
            for idx, inp in enumerate(nd_struct.inputs_edges_names):
                if inp in self._global_context.outputs_storage.outputs_collections:
                    output_obj = self._global_context.outputs_storage.outputs_collections[inp]
                    output_obj.idx_in_onnx_user[nd_struct.onnx_name] = idx

                    # set ms_user idx, need to modify if not follow onnx order
                    output_obj.idx_in_ms_user[nd_struct.identifier] = idx

                    # set this output to be returned to external
                    output_obj.to_external = not (nd_struct.check_target_node_internal(
                        self._global_context.outputs_storage.onnx_name(inp)
                    ))

        # collect submodule's and nodes' outputs mgr
        self._collect_output_mgr()

    def _collect_output_mgr(self, module=None):
        """
        Collect the outputs manager from nodes and submodules the current module has.

        Args:
            module (ModuleStruct): The module struct collecting its nodes and submodules.
        """
        root_module = module or self.get_module_struct('[]')
        output_mgr_list = list()
        for struct in root_module.get_generate_order():
            if isinstance(struct, tuple):
                # index 1 is the NodeStruct while 0 is topological index.
                struct = struct[1]
            if isinstance(struct, ModuleStruct) and struct.outputs_manager is None:
                self._collect_output_mgr(module=struct)
            for out in struct.outputs_manager.outputs:
                if Generator.check_output_need_to_external(root_module, out):
                    output_mgr_list.append(out.deepcopy())
        root_module.outputs_manager = ModuleOutputManager(root_module.identifier,
                                                          base_out=output_mgr_list)
        root_module.outputs_manager.assign_opt_var_name_to_each_output(root_module.ms_opt_var_name)

    @staticmethod
    def check_output_need_to_external(root_module: ModuleStruct, checked_output: BaseOutput):
        """
        Check the output still need to be returned to module external.

        Args:
            root_module (ModuleStruct): The Module that the output to be determined.
            checked_output (BaseOutput): The output to be checked whether returned by the Module.

        Returns:
            bool, True if the output need to be returned to the module external.
        """
        for user in checked_output.onnx_user:
            if user in root_module.external_successor_nodes_names:
                return True
        return False

    def _split_op_procs(self, split_struct: NodeStruct):
        """
        Support for Split operation multiple outputs.

        Args:
            split_struct (NodeStruct): The NodeStruct of the Split op.
        """
        for successor in split_struct.successor_nodes_structs:
            # 1. target user is internal
            if split_struct.check_target_node_internal(successor.identifier):
                idx = self._get_correct_input_idx_from_split(split_struct, successor)
                if idx is None:
                    raise ValueError("The Split OP should not has empty output.")
                correct_input = split_struct.fragment.fragment.get_outputs_by_idx(0, idx)
                to_be_replaced = None
                for inp in successor.matched_inputs:
                    if "split" in inp:
                        to_be_replaced = inp
                        break
                if to_be_replaced is not None:
                    successor.matched_inputs = replace_string_in_list(successor.matched_inputs,
                                                                      to_be_replaced,
                                                                      correct_input)
            # 2. target user is external
            else:
                public_parent = self._get_public_parent_module(split_struct, successor)
                to_be_modified_md = self._get_submodule_has_out_user_under_public_parent(public_parent, successor)
                idx = self._get_correct_input_idx_from_split(split_struct, successor)
                if idx is None:
                    raise ValueError("The Split OP should not has empty output.")
                if to_be_modified_md is None:
                    raise ValueError("Unable to locate the submodule to be modified for Split output matching.")
                correct_input = split_struct.fragment.fragment.get_outputs_by_idx(0, idx)
                to_be_replaced = None
                for inp in to_be_modified_md.matched_inputs:
                    if "split" in inp:
                        to_be_replaced = inp
                        break
                if to_be_replaced is not None:
                    to_be_modified_md.matched_inputs = replace_string_in_list(to_be_modified_md.matched_inputs,
                                                                              to_be_replaced,
                                                                              correct_input)

    def _get_correct_input_idx_from_split(self, split_struct: NodeStruct, split_out_user: NodeStruct):
        """Return the index of the split output the user used."""
        split_struct_out_edges = split_struct.fragment.metadata.get("outputs")
        for idx, out in enumerate(split_struct_out_edges):
            if out in split_out_user.fragment.metadata.get("inputs"):
                return idx
        return None

    def _get_public_parent_module(self, node_a: NodeStruct, node_b: NodeStruct):
        """Return the public parent module of both Node A and Node B."""
        find = False
        b_onnx_name = node_b.onnx_name
        tmp = node_a
        while not find:
            parent_struct = tmp.parent_module_struct
            if b_onnx_name in parent_struct.onnx_names:
                find = True
            tmp = parent_struct
        return tmp

    def _get_submodule_has_out_user_under_public_parent(self, public_module: ModuleStruct, node_out_user: NodeStruct):
        """Return the ModuleStruct which under the public module and contains the NodeStruct which provided."""
        for module_struct in public_module.module_structs:
            if node_out_user.onnx_name in module_struct.onnx_names:
                return module_struct
        return None
