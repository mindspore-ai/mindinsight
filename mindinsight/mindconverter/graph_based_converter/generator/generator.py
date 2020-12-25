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
"""Main Generator module."""
import copy
from collections import OrderedDict

from yapf.yapflib.yapf_api import FormatCode

from .scope_utils import Scope
from .node_struct import NodeStruct
from .module_struct import ModuleStruct
from .args_translator import ArgsTranslationHelper
from ..common.global_context import GlobalContext
from ...common.exceptions import GeneratorError
from ..hierarchical_tree.name_mgr import GlobalVarNameMgr
from ..constant import NEW_LINE, SECOND_LEVEL_INDENT, FIRST_LEVEL_INDENT, CodeFormatConfig, get_imported_module
from ..report_generator import ReportGenerator


class CodeStruct:
    """
    Define the Code template for each module generated in the final output.
    Each module has only one CodeStruct to its pattern.
    """
    GLOBAL_CONTEXT = GlobalContext()
    NOT_IN_SCOPE_OPT = dict()

    def __init__(self, struct, repeated_submodules=None):
        """Initialize the CodeStruct."""
        self.output_order = None  # output order
        self.input = None  # opt_var_name for prev. node
        self.extra_input = list()  # extra_input(s) at construct method args
        self.output = None  # opt_var_name for next node
        self.extra_output = list()  # extra_output(s)
        self.extra_comment = None  # comments for this code line / block.
        self.code_line_list = list()  # list of code line, a item is a line.
        self._global_var_mgr = GlobalVarNameMgr()  # var name procs within same module

        self.formal_args_collections = None

        if isinstance(struct, NodeStruct):
            self.output_order = struct.topo_idx
        if isinstance(struct, ModuleStruct):
            self.output_order = struct.head_nd_struct_index
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

        # For code line in init  & construct blocks
        init_lines = list()
        cons_lines = list()
        for (_, struct) in md_struct.get_generate_order():
            if isinstance(struct, NodeStruct):  # Generate code line for Node.
                code_line_init = struct.code_line_in_init()
                code_line_construct = struct.code_line_in_construct()
                init_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_init)}")
                cons_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_construct)}")
                # add extra tensor
                if struct.fragment.code_setting and struct.fragment.code_setting.op_extra_tensor:
                    init_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(struct.add_extra_tensor())}")

            elif isinstance(struct, ModuleStruct):
                # check if this instance generated CodeStruct
                if self.GLOBAL_CONTEXT.code_structs.get(struct.pattern_id) is None:
                    CodeStruct(struct, repeated_submodules)

                code_line_init = struct.code_line_in_init()
                code_line_construct = struct.code_line_in_construct(inputs=struct.matched_inputs)
                init_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_init)}")
                cons_lines.append(f"{SECOND_LEVEL_INDENT}{' = '.join(code_line_construct)}")

            else:
                raise TypeError("Unable to generate code from args are not ModuleStruct or NodeStruct.")

        # define header of init block
        self.new_line = f"{FIRST_LEVEL_INDENT}def __init__({', '.join(module_def_args)}):"
        self.new_line = f"{SECOND_LEVEL_INDENT}super({class_name}, self).__init__()"
        # add init code lines to code line list.
        self.code_line_list += init_lines
        self.new_line = f"{NEW_LINE * 2}"

        # define header of construct block
        inputs = ['self'] + list(md_struct.construct_header_x.keys())
        self.new_line = f"{FIRST_LEVEL_INDENT}def construct({', '.join(inputs)}):"
        # add construct code lines to code line list.
        self.code_line_list += cons_lines
        # define returns
        returns = []
        if md_struct.external_successor_local_returns_map:
            for r in list(md_struct.external_successor_local_returns_map.values()):
                if isinstance(r, tuple):  # results return with index nth output
                    returns.append(r[0])
                else:
                    returns.append(r)
            returns = list(set(returns))
        else:
            returns = [code_line_construct[0]]
        self.new_line = f"{SECOND_LEVEL_INDENT}return {', '.join(returns)}"
        self.new_line = f"{NEW_LINE * 2}"
        self.GLOBAL_CONTEXT.code_structs[md_struct.pattern_id] = self


class Generator:
    """The generator controls all routines of code generation."""

    def __init__(self):
        """Init the generator."""
        # define basic attributes
        self.framework = None

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
        for (base_parameter, base_value) in base_nd_struct.fragment.actual_args.items():  # for each param
            for (_, nd_struct) in nd_struct_list[1:]:
                compared_value = nd_struct.fragment.actual_args.get(base_parameter)
                if compared_value == base_value:
                    continue
                formal_args.add(base_parameter)
                break

        return formal_args

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
                    parent_md_struct = copy.deepcopy(md_struct)  # use this submodule to create a parent module
                    # rewrite parent md struct
                    parent_md_struct.reset_as_parent()
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

        # 5. Update all translated args from module map
        self._update_all_modules_args_translator()

        # 6. Update all nodes and moudles input/output
        self.module_structs.get('[]').allocate_construct_header_x()
        self.module_structs.get('[]').collect_returns()

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

    def add_node(self, node_identifier, node_instance=None, node_fragment=None, mapper_dict=None):
        """
        Add Node information to the generator.

        Args:
            node_identifier (str): The unique identifier for the node passed in.
            node_instance (GraphNode): The GraphNode instance of each node.
            node_fragment (NodeFragment): The NodeFragment instance of this node passed in.
            mapper_dict (dict): The dict contains converted attributes from mapper.
        """

        if node_identifier is None:
            raise ValueError("Node Identifier should not be None.")
        self._global_context.node_fragments[node_identifier] = node_fragment
        args = []
        if node_instance is not None:
            args.append(node_instance)
        if mapper_dict is not None:
            args.append(mapper_dict)
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

    @GeneratorError.check_except("Generator occurs an error when generating code statements.")
    def generate(self):
        """
        Generate the final script file.

        Returns:
            list, a list of each line in script file.
        """
        self._form_bottom_submodule()
        self._recursive_form_module()
        CodeStruct(self.module_structs.get('[]'), self._repeated_submodules)

        outputs = [get_imported_module()]

        for code_struct in self._global_context.code_structs.values():
            for line in code_struct.code_line_list:
                outputs.append(line.replace("onnx::", ""))

        formatted_code, _ = FormatCode("\n".join(outputs),
                                       style_config=CodeFormatConfig.PEP8.value)

        report_generator = ReportGenerator()
        report = report_generator.gen_report(formatted_code)
        del self._global_context

        return {"model": (formatted_code, report)}

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
