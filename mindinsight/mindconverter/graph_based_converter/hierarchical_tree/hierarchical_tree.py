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
"""Define hierarchical tree."""
import os
import stat
from copy import deepcopy
from typing import NoReturn, Union
from queue import Queue

from yapf.yapflib.yapf_api import FormatCode
from treelib import Tree, Node

from mindinsight.mindconverter.common.log import logger as log

from .name_mgr import ModuleNameMgr, GlobalVarNameMgr
from ..common.utils import is_converted, save_code_file_and_report
from ..mapper.base import Mapper
from ..third_party_graph.pytorch_graph_node import PyTorchGraphNode
from ..third_party_graph.onnx_graph_node import OnnxGraphNode
from ..constant import SEPARATOR_IN_SCOPE, get_imported_module, NO_CONVERTED_OPERATORS
from ..constant import CodeFormatConfig
from ..constant import SEPARATOR_BTW_NAME_AND_ID, FIRST_LEVEL_INDENT
from ..constant import NEW_LINE, SECOND_LEVEL_INDENT
from ..constant import NodeType
from ..report_generator import ReportGenerator
from ...common.exceptions import ReportGenerationError, ScriptGenerationError, NodeInputTypeNotSupportError


class HierarchicalTree(Tree):
    """Define hierarchical tree."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    modes = stat.S_IRUSR | stat.S_IWUSR
    modes_usr = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

    _root_created = False
    ROOT_LEVEL = 0

    GLOBAL_VAR_NAME_MGR = GlobalVarNameMgr()

    def __init__(self):
        super(HierarchicalTree, self).__init__()
        self._hierarchical_order = dict()
        # Manage mapping of unique key and module name.
        self._merged_module = dict()
        # Manage mapping of unique key and module args.
        self._merged_module_args = dict()
        # Record creation of module with unique key.
        self._created_module = dict()
        # Manage module name to used.
        self._module_mgr = ModuleNameMgr()
        # Manage variable name in a module.
        self._vars_mgr_in_module = dict()
        self._module_vars = dict()
        # scope name mapping record for easy node searching
        self._scope_name_map = dict()
        self.code_fragment_recorder = dict()

    @property
    def tree_identifier(self):
        """
        Return identifier of tree.

        Returns:
            tree, id of tree.
        """
        return self.identifier

    def get_node(self, nid):
        """Override get_node method to support tf ver. generated scope."""
        if nid is None or not self.contains(nid):
            if self._scope_name_map and nid in self._scope_name_map:
                nid = self._scope_name_map.get(nid)
            else:
                return None
        return self._nodes[nid]

    def insert(self, node: Union[PyTorchGraphNode, OnnxGraphNode], node_name: str):
        """
        Insert node into hierarchical tree.

        Args:
            node_name (str): Node name.
            node (Union[PyTorchGraphNode, OnnxGraphNode]): Node to be inserted.

        """
        scopes = node_name.split(SEPARATOR_IN_SCOPE)
        for idx, scope in enumerate(scopes):
            parent = SEPARATOR_IN_SCOPE.join(scopes[:idx])
            identifier = SEPARATOR_IN_SCOPE.join(scopes[:idx + 1])
            try_parent = f"{parent}{SEPARATOR_IN_SCOPE}{scope}" \
                if parent else scope
            if self.contains(try_parent):
                # Whether current node existed.
                parent = try_parent

            if not parent and not self._root_created:
                # If no root node, then create it and mark it.
                parent = None
                self._root_created = True
            elif not parent and self._root_created:
                # Already have root node, skip it.
                continue

            if not self.contains(identifier):
                # Insert node into tree.
                if isinstance(node, OnnxGraphNode):
                    tgt_node = node if idx == len(
                        scopes) - 1 else OnnxGraphNode()
                else:
                    tgt_node = node if idx == len(
                        scopes) - 1 else PyTorchGraphNode()
                tgt_node.successor_nodes = node.successor_nodes
                tgt_node.precursor_nodes = node.precursor_nodes
                tgt_node.node_type = (NodeType.OPERATION if idx == len(scopes) - 1
                                      else NodeType.MODULE).value
                tgt_node.variable_name = self._get_var_name(identifier)
                self.create_node(
                    tag=scope.split(SEPARATOR_BTW_NAME_AND_ID)[0],
                    identifier=identifier,
                    parent=parent,
                    data=tgt_node
                )

    def remove(self, node: Node, keep_sub=False):
        """
        Remove node into hierarchical tree.

        Args:
            node (Node): Node to be removed.
            keep_sub (bool): Whether keep sub-tree.

        """
        if not keep_sub:
            self.remove_node(node.identifier)
            return

    def shrink(self, node: Node):
        """
        Shrink sub-tree into one node.

        Use child node to replace its ancestor.

        Args:
            node (Node): List of nodes to be merged.

        """
        node_name = node.identifier
        parent_node = self[node.predecessor(self.tree_identifier)]
        # Keep successors of parent.
        brothers = deepcopy(parent_node.successors(self.tree_identifier))
        # Because shrink occurs when node has only one child,
        # so we take index-0.
        child = node.successors(self.tree_identifier)[0]
        self.move_node(source=child,
                       destination=node.predecessor(self.tree_identifier))
        self.remove(node)
        brothers[brothers.index(node_name)] = child
        parent_node.set_successors(brothers, tree_id=self.tree_identifier)

    def save_source_files(self, out_folder: str, mapper: Mapper,
                          model_name: str,
                          report_folder: str = None,
                          scope_name_map: dict = None) -> NoReturn:
        """
        Save source codes to target folder.

        Args:
            report_folder (str): Report folder.
            mapper (Mapper): Mapper of third party framework and mindspore.
            model_name(str): Name of Converted model.
            out_folder (str): Output folder.
            scope_name_map(str): Scope name map of tensorflow.

        """
        if scope_name_map:
            self._scope_name_map = scope_name_map
        try:
            self._adjust_structure()
            code_fragments = self._generate_codes(mapper)
        except (NodeInputTypeNotSupportError, ScriptGenerationError, ReportGenerationError) as e:
            log.error("Error occur when generating codes.")
            raise e

        save_code_file_and_report(model_name, code_fragments, out_folder, report_folder)

    def _preprocess_node_args(self, node, module_key):
        """
        Remove unused args.

        Args:
            node (Node): Node instance.
            module_key (str): Nodule key.

        Returns:
            Node, node.
        """
        if module_key in self._merged_module_args:
            node = self._clear_unused_args(
                node, self._merged_module_args[module_key])
        else:
            node.data.clear_args_of_declaration()
        return node

    def _postprocess_node_args(self, node, precursor_module_key):
        """
        Post process args in node.

        Args:
            node (Node): Node instance.
            precursor_module_key (str): Parent node module name.

        Returns:
            Node, node.
        """
        if node.data.node_type in {NodeType.MODULE.value, NodeType.CLASS.value,
                                   NodeType.FUNC.value}:
            # If current node is class or function, then
            # remove unused args in __init__.
            cur_module_key = node.data.hash_key or self.hash_key(node)
            if cur_module_key in self._merged_module_args:
                node = self._clear_unused_args(node,
                                               self._merged_module_args[cur_module_key])

        # `self._merged_module_args` records formal args.
        # We need to replace actual args.
        if precursor_module_key in self._merged_module_args:
            # If parent node is in `_merged_module_args`, then
            # replace current node args with arg name declared
            # in _merged_module_args.
            for arg in node.data.args_in_code.keys():
                if arg in self._merged_module_args[precursor_module_key]:
                    node.data.replace_with_arg(arg, arg)
        return node

    def _clear_unused_args(self, node, used_args):
        """
        Clear unused args.

        Args:
            node (Node): Node.
            used_args (list): Args list.

        Returns:
            Node, node instance.
        """
        args_in_code = list(node.data.args_in_code.keys())
        for arg in args_in_code:
            ori_arg = arg.replace(
                f"_{self.code_fragment_recorder[node.identifier].declared_var_name}", ""
            )
            if ori_arg not in used_args:
                node.data.args_in_code.pop(arg)
        return node

    @ScriptGenerationError.check_except("FormatCode run error. Check detailed information in log.")
    @ReportGenerationError.check_except("Not find valid operators in converted script.")
    def _generate_codes(self, mapper):
        """
        Generate code files.

        - 1. Generate args.
        - 2. Merge module.
        - 3. Pre-process node args.
        - 4. Post-process child node args.
        - 5. Generate class/func code.
        - 6. Merge code snippets.

        Args:
            mapper (Mapper): Mapper of third party operation and mindspore.

        Returns:
            Dict, codes.
        """
        code_blocks = [get_imported_module()]
        depths = sorted(list(self._hierarchical_order.keys()), reverse=True)

        for depth in depths:
            node_collection = self._hierarchical_order[depth]
            for node_name in node_collection:
                # Traverse nodes in topological order.
                node = self.get_node(node_name)
                # 1. Generate args for each node in this level.
                if node.data.node_type == NodeType.MODULE.value:
                    self._create_module_args_and_vars(node, mapper)
                if depth == depths[-1]:
                    self.code_fragment_recorder[node.identifier] = node.data.param_transform(mapper, "")

        # Module merging based on all nodes.
        self._module_merging()

        for depth in depths:
            node_collection = self._hierarchical_order[depth]
            snippets = set()
            for node_name in node_collection:
                nd_inst = self.get_node(node_name)
                if nd_inst.data.node_type != NodeType.MODULE.value:
                    continue

                # Generate hash key for node.
                module_key = nd_inst.data.hash_key
                # Get code generation func.
                func, node_type = self._fetch_func_and_type(nd_inst)

                if module_key in self._created_module:
                    # If the module has already been created,
                    # then assign the created module name to current node,
                    # and delete unused args.
                    module_name = self._created_module[module_key]
                    self.code_fragment_recorder[nd_inst.identifier].operation = module_name
                    self.code_fragment_recorder[nd_inst.identifier].node_type = node_type
                    self._preprocess_node_args(nd_inst, module_key)
                    continue

                module_name = nd_inst.tag

                if node_type == NodeType.CLASS.value:
                    module_name = f"{module_name[0].upper()}{module_name[1:]}"

                # After node_type and module_name is frozen,
                # then it's unchangeable.
                module_name = self._module_mgr.get_name(module_name)
                self.code_fragment_recorder[nd_inst.identifier].operation = module_name
                self.code_fragment_recorder[nd_inst.identifier].node_type = node_type

                # 3. Pre-process node args.
                nd_inst = self._preprocess_node_args(nd_inst, module_key)
                # 4. Post-process child node args.
                for _, scsr_nd_name in enumerate(nd_inst.successors(self.tree_identifier)):
                    self._postprocess_node_args(self.get_node(scsr_nd_name), module_key)
                # 5. Generate code.
                snippets.add(func(nd_inst, self.code_fragment_recorder[nd_inst.identifier].operation, module_key))

            code_blocks.extend(snippets)

        if self._scope_name_map:  # from tf. conversion
            c_blocks = []
            for s in code_blocks:
                s = s.replace('$', '')
                c_blocks.append(s)
            code_blocks = c_blocks

        formatted_code, _ = FormatCode("".join(code_blocks),
                                       style_config=CodeFormatConfig.PEP8.value)

        report_generator = ReportGenerator()
        report = report_generator.gen_report(formatted_code)

        return {"model": (formatted_code, report)}

    def _fetch_func_and_type(self, node) -> Union[object, str]:
        """
        Generate code snippet.

        Args:
            node (Node): Node.

        Returns:
            Union[object, str], code snippet func.
        """

        def _is_func():
            """
            The correct thought is to check whether have more than one
            path in this block.
            """
            nonlocal node

            if node.predecessor(self.tree_identifier) is None:
                return False

            tgt_type = {NodeType.MODULE.value,
                        NodeType.FUNC.value, NodeType.CLASS.value}
            md_type_lst = [self.get_node(child).data.node_type
                           for child in node.successors(self.tree_identifier)]
            diff_set = set(md_type_lst) - tgt_type
            return not diff_set

        if _is_func():
            return self._generate_func_snippet, NodeType.FUNC.value
        return self._generate_class_snippet, NodeType.CLASS.value

    def _generate_func_snippet(self, node, func_name, func_key):
        """
        Generate function snippet.

        Args:
            node (Node): Node inst.

        Returns:
            str, code snippet.
        """
        definition = ""

        if func_key.lower() in self._merged_module_args and \
                self._merged_module_args[func_key.lower()]:
            definition = ", ".join(self._merged_module_args[func_key.lower()])

        module_list = []
        for node_name in node.successors(self.tree_identifier):
            c_nd = self.get_node(node_name)
            operator = self.code_fragment_recorder[c_nd.identifier].operation

            if c_nd.data.node_type != NodeType.OPERATION.value:
                hash_key = c_nd.data.hash_key or self.hash_key(c_nd)
                if hash_key in self._created_module:
                    operator = self._created_module[hash_key]

            args = c_nd.data.args_in_code
            if c_nd.data.node_type == NodeType.OPERATION.value and not is_converted(
                    self.code_fragment_recorder[c_nd.identifier].operation):
                args.update({"input_shape": c_nd.data.input_shape,
                             "output_shape": c_nd.data.output_shape})

            # Generate code statement.
            expr = ", ".join(
                [f"{k.replace(f'_{self.code_fragment_recorder[c_nd.identifier].declared_var_name}', '')}={v}"
                 for k, v in args.items()]
            )
            code_line = f"{operator}({expr})"
            module_list.append(code_line)

        body = f",{NEW_LINE}{SECOND_LEVEL_INDENT}".join(module_list)
        snippet = f"{FIRST_LEVEL_INDENT}module_list = [{NEW_LINE}" \
                  f"{SECOND_LEVEL_INDENT}{body}{NEW_LINE}" \
                  f"{FIRST_LEVEL_INDENT}]{NEW_LINE}" \
                  f"{FIRST_LEVEL_INDENT}return nn.SequentialCell(*module_list)"
        definition = f"def {func_name}({definition}):{NEW_LINE}"

        # Mark the structure has been created.
        self._created_module[func_key.lower()] = func_name

        return f"{definition}{snippet}{NEW_LINE * 3}"

    def _generate_class_snippet(self, node, class_name, class_key):
        """
        Generate class-type code snippet.

        Args:
            node (Node): Node.

        Returns:
            str, code snippet.
        """
        super_call = f"super({class_name}, self).__init__()"

        if class_key.lower() in self._merged_module_args and \
                self._merged_module_args[class_key.lower()]:
            args = f"{', '.join(self._merged_module_args[class_key.lower()])}"

            class_init = f"{FIRST_LEVEL_INDENT}def __init__(self, " \
                         f"{args}):" \
                         f"{NEW_LINE}{SECOND_LEVEL_INDENT}" \
                         f"{super_call}{NEW_LINE}{SECOND_LEVEL_INDENT}"
        else:
            class_init = f"{FIRST_LEVEL_INDENT}def __init__(self):{NEW_LINE}{SECOND_LEVEL_INDENT}" \
                         f"{super_call}{NEW_LINE}{SECOND_LEVEL_INDENT}"

        init_block = []
        construct_block = []

        for idx, node_name in enumerate(node.successors(self.tree_identifier)):
            nd_inst = self.get_node(node_name)
            if nd_inst.data.op_name in NO_CONVERTED_OPERATORS:
                continue

            # Generate code statement.
            init, construct = self._generate_stat(nd_inst, node, idx)

            # support multiple construct and init block returns:
            if isinstance(construct, list):
                construct_block += construct
            else:
                construct_block.append(construct)

            if isinstance(init, list):
                init_block += init
            else:
                init_block.append(init)

        class_construct = f"{NEW_LINE}{FIRST_LEVEL_INDENT}def construct(self, x):" \
                          f"{NEW_LINE}{SECOND_LEVEL_INDENT}"
        init_body = f"{NEW_LINE}{SECOND_LEVEL_INDENT}".join(init_block)
        csrt_body = f"{NEW_LINE}{SECOND_LEVEL_INDENT}".join(construct_block)
        csrt_rtn = f"{NEW_LINE}{SECOND_LEVEL_INDENT}return output{NEW_LINE}"

        cls_definition = f"class {class_name}(nn.Cell):{NEW_LINE * 2}"

        # Mark the structure has been created.
        self._created_module[class_key.lower()] = class_name

        return f"{cls_definition}" \
               f"{class_init}" \
               f"{init_body}{NEW_LINE}" \
               f"{class_construct}" \
               f"{csrt_body}{csrt_rtn}{NEW_LINE * 2}"

    def _generate_stat(self, cur_nd_inst, pre_nd_inst, idx):
        """
        Generate statements.

        Args:
            cur_nd_inst (Node): Current node instance.
            pre_nd_inst (Node): Precursor node instance.
            idx (int): Index of cur node.

        Returns:
            Tuple[str, str], declare in init and call in construct.
        """

        ipt_args_in_construct = "x"
        opt_arg_in_construct = ["output"]

        if idx != 0:
            if cur_nd_inst.data.is_in_multi_opt_graph:
                ipt_args_in_construct = self._get_current_ipt_var(cur_nd_inst)
            else:
                # Get previous node output variable name.
                ipt_args_in_construct = self._get_previous_opt_var(cur_nd_inst, pre_nd_inst)
        if idx != len(pre_nd_inst.successors(self.tree_identifier)) - 1:
            # Set opt variable name.
            if cur_nd_inst.data.node_type == NodeType.MODULE.value or not cur_nd_inst.data.is_in_multi_opt_graph:
                opt_arg_in_construct = [
                    f"{self.code_fragment_recorder[cur_nd_inst.identifier].declared_var_name}_opt"
                ]
            else:
                opt_arg_in_construct = [
                    f"opt_{var_name}"
                    for var_name in self.code_fragment_recorder[cur_nd_inst.identifier].output_var_name
                ]

        declare, call = cur_nd_inst.data.to_code(ipt_args_in_construct=ipt_args_in_construct,
                                                 variable_name=self.code_fragment_recorder[
                                                     cur_nd_inst.identifier].declared_var_name,
                                                 output_var=opt_arg_in_construct,
                                                 code_fragment=self.code_fragment_recorder[cur_nd_inst.identifier])

        return declare, call

    @staticmethod
    def _get_var_name(s):
        """
        Get variable name using scope name.

        Args:
            s (str): String.

        Returns:
            str, variable name.
        """
        return s.split(SEPARATOR_IN_SCOPE)[-1].lower().split(SEPARATOR_BTW_NAME_AND_ID)[0]

    def _get_current_ipt_var(self, cur_nd):
        """"
        Get current input variable name from node_id.

        Args:
            cur_nd (Node): Current node.

        Returns:
            str, needed var names.
        """
        if cur_nd.data.node_type != NodeType.OPERATION.value:
            while True:
                p_nd = cur_nd.successors(self.tree_identifier)
                if not p_nd:
                    break
                cur_nd = self.get_node(p_nd[0])

        ipt_lst_raw = []
        for operation_input in self.code_fragment_recorder[cur_nd.identifier].operation_inputs:
            ipt_lst_raw.append(f"{operation_input}")

        opt_var_names_p_nds = set()
        for e in cur_nd.data.precursor_nodes:
            p_nd = self.get_node(e)
            if p_nd.data.op_name in NO_CONVERTED_OPERATORS:
                continue

            opt_var_names_p_nd = set(p_nd.data.opt_var_names)
            opt_var_names_p_nds = set.union(opt_var_names_p_nds, opt_var_names_p_nd)

        ipt_lst = [f"opt_{ipt}" for ipt in set(ipt_lst_raw).intersection(opt_var_names_p_nds)]
        return ", ".join(ipt_lst)

    def _find_all_previous_opt_var_(self, cur_nd, pre_nd):
        """
        Find all input variable names.

        Args:
            cur_nd (Node): Current node.
            pre_nd (Node): Precursor node.

        Returns:
            list, needed var names list.
        """
        ipt_lst = []
        if cur_nd.tag in NO_CONVERTED_OPERATORS:
            return ipt_lst

        for e in cur_nd.data.precursor_nodes:
            p_nd = self.get_node(e)
            if e not in pre_nd.successors(self.tree_identifier):
                while True:
                    if p_nd.identifier in pre_nd.successors(self.tree_identifier):
                        ipt_lst.append(
                            f"{self.code_fragment_recorder[p_nd.identifier].declared_var_name}_opt"
                        )
                        break
                    pre_nd_name = p_nd.predecessor(self.tree_identifier)
                    if not pre_nd_name:
                        ipt_lst.append("x")
                        break
                    p_nd = self.get_node(pre_nd_name)
                continue
            ipt_lst.append(
                f"{self.code_fragment_recorder[p_nd.identifier].declared_var_name}_opt"
            )
        return ipt_lst

    def _get_previous_opt_var(self, cur_nd, pre_nd):
        """
        Get needed input variable names.

        Args:
            cur_nd (Node): Current node.
            pre_nd (Node): Precursor node.

        Returns:
            str, needed var names.
        """
        if cur_nd.data.node_type != NodeType.OPERATION.value:
            while True:
                p_nd = cur_nd.successors(self.tree_identifier)
                if not p_nd:
                    break
                cur_nd = self.get_node(p_nd[0])
        return ", ".join(self._find_all_previous_opt_var_(cur_nd, pre_nd))

    def hash_key(self, node):
        """
        Generate hash key for each node.

        Args:
            node (Node): Node.

        Returns:
            str, hash key.
        """
        scsr_topo_order = []
        for s in node.successors(self.tree_identifier):
            cur_nd = self.get_node(s)
            if cur_nd.data.node_type in {NodeType.MODULE.value,
                                         NodeType.FUNC.value,
                                         NodeType.CLASS.value}:
                if cur_nd.data.hash_key:
                    scsr_topo_order.append(f"({cur_nd.data.hash_key})")
                    continue

                raise ValueError("Current node doesn't have hash key.")

            if cur_nd.data.hash_key:
                scsr_topo_order.append(cur_nd.data.hash_key)
                continue
        unique_key = "->".join(scsr_topo_order)
        node.data.hash_key = unique_key
        return unique_key

    def _module_merging(self):
        """Generate sub-module and corresponding params."""
        merged_module_args = dict()
        for module_key, module_args in self._merged_module.items():
            if module_key not in merged_module_args:
                merged_module_args[module_key] = []
            # Take first element's args as base.
            keys = module_args[0].keys()
            for key in keys:
                for i in range(1, len(module_args)):
                    if key in module_args[i] and module_args[0][key] != module_args[i][key]:
                        merged_module_args[module_key].append(key)
                        break
                    if key not in module_args[i]:
                        merged_module_args[module_key].append(key)
                        break

        self._merged_module_args.update(merged_module_args)

    def _create_module_args_and_vars(self, node, mapper):
        """
        Create module args and variables in current node.

        Args:
            node (Node): Node on tree.
            mapper (Mapper): Mapper of params.

        """
        # All args and value pair in current node module.
        module_args = dict()
        module_key = self.hash_key(node)
        created = False

        if module_key not in self._vars_mgr_in_module:
            self._vars_mgr_in_module[module_key] = self.GLOBAL_VAR_NAME_MGR
            self._module_vars[module_key] = []
        else:
            created = True

        # Sub-modules in the module could have arg name conflicts.
        for idx, successor_name in enumerate(node.successors(self.tree_identifier)):
            nd_inst = self.get_node(successor_name)
            if nd_inst.data.op_name in NO_CONVERTED_OPERATORS:
                continue

            # Generation of params must behind variable assigment.
            if created:
                variable_name = self._module_vars[module_key][idx]
            else:
                variable_name = nd_inst.data.op_name or nd_inst.tag
                variable_name = self._vars_mgr_in_module[module_key].get_name(variable_name)

            code_fragment = nd_inst.data.param_transform(mapper, variable_name)
            code_fragment.declared_var_name = variable_name
            code_fragment.output_var_name = nd_inst.data.opt_var_names
            code_fragment.update_operation_inputs(nd_inst.data.ipt_var_names)
            self.code_fragment_recorder[nd_inst.identifier] = code_fragment

            module_args.update(nd_inst.data.args_in_code)

            if not created:
                self._module_vars[module_key].append(variable_name)

        node.data.args_in_code = module_args

        # Collect module args of `module_key`.
        if module_key not in self._merged_module:
            self._merged_module[module_key] = [deepcopy(node.data.args_in_code)]
        else:
            self._merged_module[module_key].append(deepcopy(node.data.args_in_code))

    @staticmethod
    def _create_operation_args(node, mapper):
        """
        Create operation args.

        Args:
            node (Node): Node on tree.
            mapper (Mapper): Mapper of params.

        """
        node.data.param_transform(mapper)

    def update_hierarchical_order(self) -> NoReturn:
        """
        Update hierarchical order.
        """
        hierarchical_order = dict()
        queue = Queue()
        queue.put(item=(self.root, self.ROOT_LEVEL), block=False)
        while not queue.empty():
            node_name, cur_level = queue.get(block=False)
            node_inst = self[node_name]
            if cur_level not in hierarchical_order:
                hierarchical_order[cur_level] = []
            hierarchical_order[cur_level].append(node_name)
            for successor_name in node_inst.successors(self.tree_identifier):
                queue.put(item=(successor_name, cur_level + 1), block=False)
        self._hierarchical_order = hierarchical_order

    def sub_graph_merging(self) -> NoReturn:
        """Shrink the module has only one child."""
        self.update_hierarchical_order()
        depths = sorted(list(self._hierarchical_order.keys()), reverse=True)
        for depth in depths:
            for node_name in self._hierarchical_order[depth]:
                node_inst = self[node_name]
                # If the node type is module and has only one child,
                # then merge it with its child.
                if node_inst.data.node_type == NodeType.MODULE.value and \
                        len(node_inst.successors(self.tree_identifier)) == 1:
                    self.shrink(node_inst)

    def _adjust_structure(self) -> NoReturn:
        """Adjust tree structure to generate source code."""
        self.sub_graph_merging()
        self.update_hierarchical_order()
