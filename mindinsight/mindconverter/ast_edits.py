# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless REQUIRED by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Convert for Python scripts according API mapping information."""

import ast
import logging
import re
from enum import Enum

import pasta
from pasta.base import formatting as fmt

from mindinsight.mindconverter.code_analysis import CodeAnalyzer
from mindinsight.mindconverter.code_analysis import APIAnalysisSpec
from mindinsight.mindconverter.config import ALL_MAPPING, F_LIST
from mindinsight.mindconverter.config import NN_LIST
from mindinsight.mindconverter.config import ALL_TORCH_APIS
from mindinsight.mindconverter.config import ALL_2P_LIST
from mindinsight.mindconverter.config import TENSOR_DOT_LIST
from mindinsight.mindconverter.config import get_prompt_info
from mindinsight.mindconverter.common.log import logger
from mindinsight.mindconverter.common.exceptions import NodeTypeNotSupport
from mindinsight.mindconverter.forward_call import ForwardCall

LOG_FMT_INSERT = "[Insert] '%s' is inserted to the converted file."
LOG_FMT_CONVERT = "[Convert] '%s' is converted to '%s'."
LOG_FMT_CONVERT_WITH_TIPS = "[Convert] '%s' is converted to '%s'. %s"
LOG_FMT_NOT_CONVERT = "[UnConvert] '%s' didn't convert. %s"
LOG_FMT_PROMPT_INFO = "[INFO] %s"
LOG_SUGGESTION_MANUAL_CONVERT = "Please manual convert the code, along with the code associated with it."


class ApiMatchingEnum(Enum):
    """Node edge type enum."""
    NOT_API = 'not an api name'
    API_INFER = 'infer api name to map'
    API_STANDARD = 'api name in the correct format'
    API_FOUND = 'found an api name in api list'
    API_MATCHED = 'api is matched to map'


class _ConvertReport:
    """Report log of converting source code."""

    def __init__(self, is_stub=False):
        self._is_stub = is_stub
        self._max_line = 0
        self._log_head = []
        self._log_body = []  # report log, type is (severity, line, col, msg)

    def _add_log(self, severity, line, col, msg):
        """Add log."""
        if self._is_stub:
            return
        if line is None and col is None:
            self._log_head.append(msg)
            return
        if isinstance(line, int) and isinstance(col, int):
            self._log_body.append((severity, line, col, msg))
            if self._max_line < line:
                self._max_line = line
        else:
            raise TypeError('The parameter type is incorrect.')

    def info(self, line, col, msg):
        """Interface to add infer log"""
        self._add_log(logging.INFO, line, col, msg)

    def warning(self, line, col, msg):
        """Interface to add warning log"""
        self._add_log(logging.WARNING, line, col, msg)

    def header_msg(self, msg):
        """Interface to add header message log"""
        self._add_log(logging.INFO, None, None, msg)

    def get_logs(self):
        """Get convert logs"""
        logs = []
        logs.extend(self._log_head)
        # sort rule: line * self._max_line + col
        self._log_body.sort(key=lambda log: log[1] * self._max_line + log[2])
        for log_info in self._log_body:
            log_info = "line %d:%d: %s" % (log_info[1], log_info[2], log_info[3])
            if logs:
                # Deduplication for logs
                if logs[-1] != log_info:
                    logs.append(log_info)
            else:
                logs.append(log_info)
        return logs


class _LineColEditVisitor(ast.NodeVisitor):
    """
    Update line number and col offset of ast node.

    Use the line and column number of the original code to update
    the line and column number of the new code replaced with the original code.
    """

    class _NodeInfo:
        """NodeInfo class definition."""

        def __init__(self, node):
            self.node = node
            self.call_list = []  # Used to save all ast.Call node in self._node

    def __init__(self):
        self._dst_node_info = None
        self._src_node_info = None
        self._visiting = self._src_node_info  # Used to point to the visiting node

    def update(self, replace_with_node, src_node):
        """Update the line and column number of the new code replaced with the original code."""
        replace_with_node.lineno = src_node.lineno
        replace_with_node.col_offset = src_node.col_offset
        self._dst_node_info = self._NodeInfo(replace_with_node)
        self._src_node_info = self._NodeInfo(src_node)
        self._visiting = self._src_node_info
        self.visit(self._visiting.node)

        self._visiting = self._dst_node_info
        self.visit(self._visiting.node)

        self._update_line_col()

    def visit_Call(self, node):
        """Callback function when visit AST tree"""
        self._visiting.call_list.append(node)
        self.generic_visit(node)

    def _update_line_col(self):
        """Update the line and column number information for all ast.Call node."""
        dst_call_list = list(self._dst_node_info.call_list)
        src_call_list = list(self._src_node_info.call_list)
        len_diff = len(dst_call_list) - len(src_call_list)

        # After MindSpore api replaces Torch api, more calls are generated.
        # For example, out.view() is replaced with P.Reshape()(out).
        # out.view() has only one call, but P.Reshape()(out) has two calls.
        # To match the replaced calls, the calls of out.view is padded to the same quantity.
        if len_diff > 0:
            src_call_list = [src_call_list[0]] * len_diff + src_call_list

        for dst_call, src_call in zip(dst_call_list, src_call_list):
            dst_call.lineno = src_call.lineno
            dst_call.col_offset = src_call.col_offset

            if not dst_call.args:
                continue

            # When out.size().view(1, ...) transforms to P.Reshape()(out.size(), 1, ...),
            # in this case, the column of parameter out.size() will be bigger than the following parameters.
            # To ensure the sequence of parameters, adjust the column of the second parameter.
            args = []
            for arg in dst_call.args:
                if self._check_arg2update(arg):
                    args.append(arg)
            for arg in args:
                # line number starts from 1, column number starts from 0.
                arg.lineno += dst_call.lineno - 1
                arg.col_offset += dst_call.col_offset

    @staticmethod
    def _check_arg2update(arg):
        # When the arg is a function call, its col_offset is handled separately.
        if not isinstance(arg, ast.Call):
            return True
        return False


class AstEditVisitor(ast.NodeVisitor):
    """AST Visitor that process function calls.

    Converts function calls from torch api to MindSpore api using api mapping information.
    """

    def __init__(self):
        self._process_log = _ConvertReport()
        self._tree = None
        self._code_analyzer = None
        self._stack = []  # Used to easily access the parent node
        self._forward_list = {}
        self._is_forward_function = False  # Used to allow access the visiting function forward attribute
        self._new_call_nodes = []  # Used to save new ast.call nodes

    def process(self, ast_tree):
        """
        Convert source code to MindSpore code.

        Args:
            ast_tree (AST): The root node of the source code.
        """
        self.__init__()
        self._tree = ast_tree
        self._code_analyzer = CodeAnalyzer()
        self._code_analyzer.process(self._tree)

        self._forward_list = ForwardCall(self._tree).calls
        # replace python function under nn.Module
        self._convert_api()

        # replace external reference statements
        self._convert_external_reference()

    def get_logs(self):
        """Get conversion report."""
        return self._process_log.get_logs()

    def _convert_cell(self, cell_scope):
        """
        Convert a PyTorch Module class into MindSpore Cell class.

        Args:
            cell_scope (pasta.base.Scope): The network class definition node inherits from torch.nn.Module.
        """
        cell_ast_node = cell_scope.node
        line_no = cell_ast_node.lineno
        logger.info("Line %3d: start converting nn.Module %s", line_no, self._code_analyzer.get_name(cell_ast_node))

        class_elements = self._code_analyzer.network_definitions()['cell']
        # step1. update function definition
        for func_scope in class_elements.get(cell_scope, []):
            self._update_function_def(func_scope)

        # step2. update base name of class
        self._update_base_name(cell_scope)

    def _update_base_name(self, class_def_scope):
        """
        Update base name of class.

        Args:
            class_def_scope (ast.ClassDef): Class definition node.
        """
        base_name_mapping = APIAnalysisSpec.base_name_mapping
        class_def_node = class_def_scope.node
        base_class_nodes = class_def_scope.node.bases
        # update base class name
        for base_class_node in base_class_nodes:
            base_name = base_class_node.attr
            if base_name in APIAnalysisSpec.get_network_base_class_names():
                old_code = pasta.dump(base_class_node)
                if base_name in base_name_mapping:
                    new_code = 'nn.' + base_name_mapping[base_class_node.attr]
                    new_node = pasta.parse(new_code)
                    pasta.ast_utils.replace_child(class_def_node, base_class_node, new_node)
                    self._process_log.info(base_class_node.lineno, base_class_node.col_offset, LOG_FMT_CONVERT %
                                           (old_code, new_code))
                else:
                    self._process_log.info(base_class_node.lineno, base_class_node.col_offset, LOG_FMT_NOT_CONVERT %
                                           (old_code, ''))

    @staticmethod
    def _modify_function_name(func_def_node, new_func_name):
        """Modify function name"""
        if not isinstance(func_def_node, ast.FunctionDef):
            raise NodeTypeNotSupport('It is not ast.FunctionDef node type.')

        old_func_name = func_def_node.name
        func_def_node.name = new_func_name

        # Modify formatting information stored by pasta
        old_function_def = fmt.get(func_def_node, 'function_def')
        if old_function_def:
            new_function_def = old_function_def.replace(old_func_name, new_func_name)
            fmt.set(func_def_node, 'function_def', new_function_def)
            fmt.set(func_def_node, 'name__src', new_func_name)

    def _update_function_def(self, func_scope):
        """
        Convert a PyTorch function into MindSpore function.

        Args:
            func_scope (pasta.base.scope.Scope): The node scope of function definition.
        """
        is_forward = self._judge_forward(func_scope)
        # step1. convert the content of the function.
        self._convert_function(func_scope, is_forward)

        # step2. replace function name if name is forward
        func_ast_node = func_scope.node
        old_func_name = 'forward'
        new_func_name = 'construct'
        if func_ast_node.name == old_func_name:
            self._modify_function_name(func_ast_node, new_func_name)
            real_line_number = self._get_real_line_number(func_ast_node)
            self._process_log.info(real_line_number, func_ast_node.col_offset,
                                   LOG_FMT_CONVERT % (old_func_name, new_func_name))

    def _convert_api(self):
        """Convert PyTorch api call to MindSpore api call in a function."""
        tasks = []
        found_func_nodes = []
        convert_elements = self._code_analyzer.network_definitions()
        for func_node_scope in convert_elements.get("functions", []):
            found_func_nodes.append(func_node_scope.node)
            is_forward = self._judge_forward(func_node_scope)
            tasks.append((self._convert_function, (func_node_scope, is_forward)))
        for class_scope, func_scopes in convert_elements.get("cell", []).items():
            for func_node_scope in func_scopes:
                found_func_nodes.append(func_node_scope.node)
            tasks.append((self._convert_cell, (class_scope,)))

        # Some functions in the forward call chain are not found by self._code_analyzer.
        for func_node in self._forward_list.values():
            is_forward = True
            if func_node and func_node not in found_func_nodes:
                func_node_scope = self._code_analyzer.lookup_scope(func_node)
                tasks.append((self._convert_function, (func_node_scope, is_forward)))

        for convert_fun, args in tasks:
            convert_fun(*args)

    @staticmethod
    def _dump_without_prefix(node):
        """Get the python source for an AST."""
        pos = 0
        source_prefix = pasta.base.formatting.get(node, 'prefix')
        if source_prefix:
            pos = len(source_prefix)
        source_code = pasta.dump(node)
        return source_code[pos:]

    @staticmethod
    def _get_real_line_number(node):
        """Get the real line number of the node."""
        try:
            line_number = node.lineno + len(node.decorator_list)
        except AttributeError:
            line_number = node.lineno
        return line_number

    def _replace_external_reference(self):
        """
        Replace external reference statements.

        Returns:
            dict, key is external name, value is the new replaced node.
        """
        all_name_mappings = APIAnalysisSpec.import_name_mapping
        names_replaced_with = dict()
        for ref_info in self._code_analyzer.external_references.values():
            external_ref_info = ref_info['external_ref_info']
            import_node = ref_info['parent_node']
            if import_node is None:
                continue
            code = self._dump_without_prefix(import_node)
            import_parent_node = self._code_analyzer.root_scope.parent(import_node)
            # replace import with new name
            if external_ref_info.name in APIAnalysisSpec.get_convertible_external_names():
                external_ref_info = ref_info['external_ref_info']
                if external_ref_info.name in all_name_mappings.keys():
                    replace_info = all_name_mappings[external_ref_info.name]
                    new_node = self._make_import(name_to_import=replace_info[0], as_name=replace_info[1])
                    new_code = pasta.dump(new_node)
                    pasta.ast_utils.replace_child(import_parent_node, import_node, new_node)
                    names_replaced_with.update({external_ref_info.name: new_node})
                    self._process_log.info(import_node.lineno, import_node.col_offset, LOG_FMT_CONVERT %
                                           (code.strip(), new_code.strip()))
            elif external_ref_info.name.startswith('torch.'):
                self._process_log.warning(import_node.lineno, import_node.col_offset, LOG_FMT_NOT_CONVERT %
                                          (code.strip(), LOG_SUGGESTION_MANUAL_CONVERT))
            else:
                pass
        return names_replaced_with

    def _convert_external_reference(self):
        """Convert import statements."""
        all_name_mappings = APIAnalysisSpec.import_name_mapping

        # Step1. Replace external reference first.
        names_replaced_with = self._replace_external_reference()
        new_import_node = dict()
        insert_pos = 0
        # Step2. Find out remaining mapping name which not found in script.
        for src_name, new_import_name in all_name_mappings.items():
            if src_name not in names_replaced_with:
                new_node = self._make_import(name_to_import=new_import_name[0], as_name=new_import_name[1])
                new_import_node.update({insert_pos: new_node})
                insert_pos += 1
            else:
                try:
                    # insert pos after the last one, if last one name is replaced.
                    replaced_with_node = names_replaced_with[src_name]
                    insert_pos = self._tree.body.index(replaced_with_node) + 1
                except ValueError:
                    pass

        # Step3. Insert import reference in order.
        insert_cnt = 0
        for insert_pos, new_node in new_import_node.items():
            # Insert the node into the module
            self._tree.body.insert(insert_pos + insert_cnt, new_node)
            new_code = self._dump_without_prefix(new_node)
            self._process_log.header_msg(LOG_FMT_INSERT % new_code.strip())
            insert_cnt += 1

    @staticmethod
    def _make_import(name_to_import, as_name=None):
        """
        Create an import to the ast tree.

        Args:
            name_to_import: (string) The absolute name to import.
            as_name: (string) The alias for the import ("import name_to_import as asname")

        Returns:
            ast.Import, a new ast.Import node.
        """
        new_alias = ast.alias(name=name_to_import, asname=as_name)
        import_node = ast.Import(names=[new_alias])
        return import_node

    def _convert_function(self, func_scope, is_forward):
        """
        Convert a PyTorch function into MindSpore function.

        Args:
            func_scope (pasta.base.scope.Scope): The node scope of function definition.
            is_forward (boolean): If the function is defined in forward function in nn.Module in torch.
        """
        func_ast_node = func_scope.node
        line_no = func_ast_node.lineno
        logger.info("Line %3d: start converting function %s()", line_no, func_ast_node.name)

        parent = func_scope.parent_scope.node
        self._stack.clear()
        self._new_call_nodes.clear()
        if parent:
            self._stack.append(parent)

        self._is_forward_function = is_forward
        self.visit(func_scope.node)

    def _judge_forward(self, func_scope):
        """
        Check if function is a forward function.

        Args:
            func_scope (pasta.base.scope.Scope): The node scope of function definition.

        Returns:
            boolean, True or False
        """
        is_forward = func_scope.node in self._forward_list.values()
        if is_forward:
            logger.debug("%s is a forward function", self._code_analyzer.get_name(func_scope))
        return is_forward

    # Overridden to maintain stack information to access parent node
    def visit(self, node):
        """Visit a ast tree."""
        self._stack.append(node)
        super(AstEditVisitor, self).visit(node)
        self._stack.pop()

    def _mapping_standard_api_name(self, api_name):
        """Get mapping from external reference name to standard external reference name"""
        standard_name = api_name
        if not self._code_analyzer.is_standard_external_ref:
            # key is real ref name, value is standard ref name.
            mapping_names = self._mapping_standard_external_ref()
            api_name_parts = api_name.split('.')
            api_name_parts[0] = mapping_names.get(api_name_parts[0], api_name_parts[0])
            standard_name = '.'.join(api_name_parts)
        return standard_name

    def _infer_api_name(self, call_func_node, check_context=True):
        """Infer the call name.

        Examples:
            1. nn.Sequential inferred to nn.Sequential
            2. mmm.size inferred to .size if import torch.nn as nn
            3. mmm.size inferred to mmm.size if import torch.nn as mmm
        """
        match_case = ApiMatchingEnum.NOT_API
        api_name = None
        call_name = pasta.dump(call_func_node)

        is_include_sub_call = self._is_include_sub_call(call_func_node)
        if is_include_sub_call:
            # x.y().z splits to ['x.y()', 'z']
            name_attributes = call_name.rsplit('.', 1)
        else:
            # x.y.z splits to ['x', 'y', 'z']
            name_attributes = call_name.split('.')

        # rewritten external module name
        # e.g., mm.ReLU will be written to nn.ReLU if 'import torch.nn as mm' in script.
        if check_context and not self._code_analyzer.is_standard_external_ref:
            standard_name = self._mapping_standard_api_name(name_attributes[0])
        else:
            standard_name = name_attributes[0]

        if standard_name in ["nn", "F", "torch"]:
            match_case = ApiMatchingEnum.API_STANDARD
            api_name = call_name
        else:
            # only infer function for tensor object.
            # e.g., api_call_name is out.view, .view is an api name for out which is maybe a tensor object.
            # e.g., 'xxxx'.size can be not inferred to .size, because string is not a tensor object.
            if self._check_tensor_object(call_func_node):
                api_name = '.' + name_attributes[-1]
                match_case = ApiMatchingEnum.API_INFER

        return api_name, match_case

    def _check_tensor_object(self, node):
        """Check whether the reference object of the node is a tensor object."""
        if not isinstance(node, (ast.Attribute, ast.Name)):
            return False
        name_attributes = self._dump_without_prefix(node).split('.')
        node_ref_name = name_attributes[0]
        if re.search(r'\W', node_ref_name) or len(name_attributes) == 1:
            return False

        func_name = '.' + name_attributes[-1]
        if func_name not in TENSOR_DOT_LIST:
            return False

        extracted_api = []
        for api in name_attributes[1:len(name_attributes) - 1]:
            if "(" or ")" in api:
                start = api.find("(")
                start = start if start != -1 else len(api)
                end = api.find(")")
                end = end if end != -1 else len(api)
                if start < end:
                    api = f"{api[:start]}{api[end + 1:]}"
            extracted_api.append(api)

        is_tensor_object = True
        if self._code_analyzer:
            # Check whether the object is external reference.
            real_ref = None
            for ref_name in self._code_analyzer.external_references:
                if node_ref_name == ref_name:
                    real_ref = self._code_analyzer.external_references[ref_name]["external_ref_info"]
                    break
            if real_ref and f"{real_ref.name}.{'.'.join(extracted_api)}" not in F_LIST:
                is_tensor_object = False

        return is_tensor_object

    @staticmethod
    def _is_include_sub_call(call_func_node):
        """"Inspect a sub call in call expression.

        Examples:
            1. nn.functional.relu() return False
            2. nn.functional.relu(out).size() return True. nn.functional.relu(out) is sub call.
            3. nn.functional.relu(out=out.size()).size() return False. out.size() is not sub call of argument.
        """
        is_include_call = False
        try:
            sub_node = call_func_node
            while sub_node and not isinstance(sub_node, ast.Call):
                sub_node = sub_node.value
            if isinstance(sub_node, ast.Call):
                is_include_call = True
        except AttributeError:
            is_include_call = False
        return is_include_call

    def match_api(self, call_func_node, is_forward, check_context=True):
        """
        Check api name to convert, check api name ok with a is_forward condition.

        Args:
            call_func_node (ast.Attribute): The call.func node.
            is_forward (bool): whether api belong to forward.
            check_context (boolean): If True, the code context will be checked. Default is True.

        Returns:
            str, the standard api name used to match.
            ApiMappingEnum, the match result.
        """
        match_case = ApiMatchingEnum.NOT_API
        api_call_name = pasta.dump(call_func_node)
        if api_call_name.startswith('self.'):
            return api_call_name, match_case

        api_name, match_case = self._infer_api_name(call_func_node, check_context)
        api_call_name = pasta.dump(call_func_node)
        is_tensor_obj_call = False
        if api_name != api_call_name:
            is_tensor_obj_call = True

        standard_api_call_name = api_name

        # rewritten external module name
        # e.g., mm.ReLU will be written to nn.ReLU if 'import torch.nn as mm' in script.
        if not is_tensor_obj_call:
            standard_api_call_name = self._get_api_whole_name(call_func_node, check_context)

        if standard_api_call_name in ALL_TORCH_APIS:
            match_case = ApiMatchingEnum.API_FOUND
            if (not is_forward and standard_api_call_name in NN_LIST) or \
                    (is_forward and standard_api_call_name in ALL_2P_LIST):
                match_case = ApiMatchingEnum.API_MATCHED
        else:
            if standard_api_call_name and standard_api_call_name.startswith('torch.nn.init'):
                match_case = ApiMatchingEnum.API_MATCHED
        return standard_api_call_name, match_case

    @staticmethod
    def _get_call_parameters_str(call_node):
        """Get parameters string for a call node."""
        if not isinstance(call_node, ast.Call):
            raise NodeTypeNotSupport('It is not ast.Call node type.')
        parameters_str = ''
        call_str = pasta.dump(call_node)
        call_name = pasta.dump(call_node.func)
        last_parameter_str = ''

        if call_node.args:
            last_parameter_str = pasta.dump(call_node.args[-1])
        if call_node.keywords:
            last_parameter_str = pasta.dump(call_node.keywords[-1])
        if last_parameter_str:
            left_parenthesis_pos = call_str.find(call_name) + len(call_name)
            # call is like abc.call(a, b,), last parameter is b,
            # but parameters string must have last ',' character after the last parameter b.
            last_parameter_pos = call_str.rfind(last_parameter_str) + len(last_parameter_str)
            right_parenthesis_pos = call_str.find(')', last_parameter_pos)

            # parameters start pos must skip '(' character for calling.
            parameters_str = call_str[left_parenthesis_pos + 1:right_parenthesis_pos]
        return parameters_str

    def _get_api_whole_name(self, call_func_node, check_context=True):
        """
        Get the whole name for the call node.

        Args:
            call_func_node (AST): The func attribute of ast.Call.
            check_context (boolean): If True, the code context will be checked. Default is True.

        Returns:
            str, the whole name.
        """
        api_name, match_case = self._infer_api_name(call_func_node, check_context)
        if match_case == ApiMatchingEnum.API_STANDARD:
            api_name_splits = api_name.split('.')
            api_name_splits[0] = self._get_external_ref_whole_name(api_name_splits[0])
            if api_name_splits[0]:
                api_name = '.'.join(api_name_splits)
        return api_name

    def mapping_api(self, call_node, check_context=True):
        """
        Convert api_name in code to MindSpore api, if api_name is a python api, code will not convert.

        If do not check context of the script, the code represented by the node must be written in the standard way.

        Args:
            call_node (ast.Call): The ast node to convert.
            check_context (boolean): If True, the code context will be checked. Default is True.

        Returns:
            str, the converted code.
        """
        if not isinstance(call_node, ast.Call):
            raise NodeTypeNotSupport("It is not ast.Call node.")
        code = pasta.dump(call_node)
        api_call_name = pasta.dump(call_node.func)
        if api_call_name.startswith('self.'):
            return code

        new_code = self._mapping_api(call_node, check_context)

        return new_code

    def _mapping_api(self, call_node, check_context=True):
        """
        Convert api_name in code to MindSpore api, if api_name is a python api, code will not convert.

        If do not check context of the script, the code represented by the node must be written in the standard way.

        Args:
            call_node (ast.Call): The ast node to convert.
            check_context (boolean): If True, the code context will be checked. Default is True.

        Returns:
            str, the converted code.
        """
        code = pasta.dump(call_node)
        api_call_name = pasta.dump(call_node.func)

        # find full api expected to be converted. eg:expr="nn.Conv2d(1,2,3)" args_str="(1,2,3)"
        args_str = '(' + self._get_call_parameters_str(call_node) + ')'

        try:
            api_name, _ = self._infer_api_name(call_node.func, check_context)
            standard_api_call_name = api_call_name
            if api_name != api_call_name:
                # api name .view inferred from out.view, split tensor object name is out
                tensor_obj_name = api_call_name[:-len(api_name)]
                map_helper = ALL_MAPPING[api_name]
                new_code = map_helper.convert(tensor_obj_name, args_str)
            else:
                # change to external ref name
                # e.g., mm.ReLU will be changed to nn.ReLU if 'import torch.nn as mm' in script.
                if check_context and not self._code_analyzer.is_standard_external_ref:
                    standard_api_call_name = self._mapping_standard_api_name(api_name)

                map_helper = ALL_MAPPING[standard_api_call_name]
                new_code = map_helper.convert(standard_api_call_name, args_str)
        except KeyError:
            return code

        return new_code

    @staticmethod
    def _get_detail_prompt_msg(old_node, new_node):
        """Get detail converted prompt information."""
        msg = None
        if isinstance(old_node, ast.Call) and isinstance(new_node, ast.Call):
            old_api_name = pasta.dump(old_node.func)
            new_api_name = pasta.dump(new_node.func)
            if new_api_name == old_api_name:
                old_parameter_num = len(old_node.args) + len(old_node.keywords)
                new_parameter_num = len(new_node.args) + len(new_node.keywords)
                if old_parameter_num > 1:
                    msg = 'Parameters are converted.'
                else:
                    if old_parameter_num == 0 and new_parameter_num == 0:
                        msg = 'The API name is converted to mindspore API'
                    else:
                        msg = 'Parameter is converted.'
        return msg

    def _convert_call(self, node, matched_api_name):
        """"Convert the call node."""
        new_node = None
        code = pasta.dump(node)
        api_name = pasta.dump(node.func)
        warning_info = get_prompt_info(matched_api_name)
        if warning_info is None:
            warning_info = ''
        if matched_api_name in ALL_MAPPING:
            logger.info("Line %3d start converting API: %s", node.lineno, api_name)
            new_code = self.mapping_api(node)
            if new_code != code:
                try:
                    new_node = pasta.parse(new_code).body[0].value
                    # find the first call name
                    new_api_name = new_code[:new_code.find('(')]
                    detail_msg = self._get_detail_prompt_msg(node, new_node)
                    if detail_msg:
                        warning_info = detail_msg + ' ' + warning_info
                except AttributeError:
                    new_node = pasta.parse(new_code).body[0]
                    new_api_name = new_code
                self._process_log.info(node.lineno, node.col_offset,
                                       LOG_FMT_CONVERT_WITH_TIPS % (api_name, new_api_name, warning_info))
        else:
            logger.warning("Line %3d: found unsupported API: %s%s", node.lineno, api_name, warning_info)
            self._process_log.warning(node.lineno, node.col_offset, LOG_FMT_NOT_CONVERT % (api_name, warning_info))

        return new_node

    def visit_Call(self, node):
        """Callback function when visit AST tree"""
        code = pasta.dump(node)
        api_name = pasta.dump(node.func)

        # The parent node first call is equal to this node, skip when parent node is replaced.
        # This scenario occurs, for example, when out.view(out.size(0), -1) is first converted to
        # P.Reshape()(out, (out.size(0). -1)), will skip P.Reshape() in following visiting.
        # Access from the penultimate element in reverse order.
        for parent_node in self._stack[-2::-1]:
            if parent_node in self._new_call_nodes and pasta.dump(parent_node).startswith(api_name):
                return
        parent = self._stack[-2]
        new_node = None
        new_code = code
        matched_api_name, match_case = self.match_api(node.func, self._is_forward_function)
        if match_case in [ApiMatchingEnum.API_INFER, ApiMatchingEnum.API_MATCHED]:
            new_node = self._convert_call(node, matched_api_name)
        elif match_case in [ApiMatchingEnum.API_STANDARD, ApiMatchingEnum.API_FOUND]:
            self._process_log.warning(node.lineno, node.col_offset, LOG_FMT_NOT_CONVERT % (api_name, ''))
        else:
            pass

        if parent and new_node:
            update_line_col = _LineColEditVisitor()
            update_line_col.update(new_node, node)
            pasta.ast_utils.replace_child(parent, node, new_node)
            self._new_call_nodes.append(new_node)

            node = new_node
            self._stack[-1] = node
        try:
            self.generic_visit(node)
        except Exception:
            logger.error('original code:%s, new code:%s', code, new_code, exc_info=True)
            raise

    def _mapping_standard_external_ref(self):
        """Obtain the mapping dict of mapping the external references to standard external references."""
        renames = {}
        external_refs = self._code_analyzer.external_references
        for ref_name, ref_info in external_refs.items():
            external_ref_info = ref_info['external_ref_info']
            if ref_name != 'nn' and external_ref_info.name == 'torch.nn':
                renames[ref_name] = 'nn'
            elif ref_name != 'F' and external_ref_info.name == 'torch.nn.functional':
                renames[ref_name] = 'F'
        return renames

    def _get_external_ref_whole_name(self, ref_name):
        """
        Find out external reference whole name.

        For example:
        In the parsed source code, there is import statement
            import torch.nn as new_name
        _get_external_ref_whole_name('new_name') will return 'torch.nn' string.
        """
        external_refs = self._code_analyzer.external_references
        for external_ref_name, ref_info in external_refs.items():
            external_ref_info = ref_info['external_ref_info']
            if external_ref_name == ref_name:
                return external_ref_info.name
        return None

    def _check_isinstance_parameter(self, node):
        """Check whether the second parameter of isinstance function contains the torch type."""
        is_isinstance_arg = False
        # Check whether node is the second parameter of the isinstance function call.
        # Access from the penultimate element in reverse order.
        for parent_node in self._stack[-2::-1]:
            if isinstance(parent_node, ast.Call) and pasta.dump(parent_node.func) == 'isinstance':
                isinstance_node = parent_node
                seconde_arg_type_nodes = []
                if isinstance(isinstance_node.args[1], ast.Tuple):
                    seconde_arg_type_nodes.extend(isinstance_node.args[1].elts)
                else:
                    seconde_arg_type_nodes.append(isinstance_node.args[1])
                if node in seconde_arg_type_nodes:
                    is_isinstance_arg = True
                    break
        if not is_isinstance_arg:
            return False

        isinstance_type_arg = pasta.dump(node)
        check_torch_type = False
        if isinstance_type_arg:
            type_splits = isinstance_type_arg.split('.')
            whole_name = self._get_external_ref_whole_name(type_splits[0])
            if whole_name and whole_name.startswith('torch'):
                check_torch_type = True
        if check_torch_type:
            _, match_case = self.match_api(node, False)
            if match_case != ApiMatchingEnum.NOT_API:
                warn_info = 'Manually determine the conversion type.'
                self._process_log.warning(node.lineno, node.col_offset,
                                          LOG_FMT_NOT_CONVERT % (isinstance_type_arg, warn_info))
        return check_torch_type

    def visit_Attribute(self, node):
        """Callback function when visit AST tree"""
        self._check_isinstance_parameter(node)
        self.generic_visit(node)
