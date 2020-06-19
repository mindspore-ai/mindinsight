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
"""code analysis module"""
import ast

import pasta
from pasta.base import scope

from mindinsight.mindconverter.common.exceptions import ScriptNotSupport


class APIAnalysisSpec:
    """API analysis specifications"""

    import_name_mapping = {'torch': ['mindspore', None],
                           'torch.nn': ['mindspore.nn', 'nn'],
                           'torch.nn.functional': ['mindspore.ops.operations', 'P']}

    base_name_mapping = {'Module': 'Cell',
                         'Sequential': 'SequentialCell'
                         }

    @classmethod
    def get_convertible_external_names(cls):
        """
        Obtain the convertible external names.

        The external name is the full dotted name being referenced.
        """
        return cls.import_name_mapping.keys()

    @staticmethod
    def get_network_base_class_names():
        """Obtain the base names which network class base from"""
        return ['Module',
                'Sequential',
                'ModuleList',
                'ModuleDict',
                'ParameterList',
                'ParameterDict']

    @staticmethod
    def check_external_alias_ref(ref_name, external_name):
        """
        Check 'import as' is standard.

        Standard references are follow:
        import torch.nn as nn
        import torch.nn.functional as F

        Args:
            ref_name (str): The name that refers to the external_name.
            external_name (str): The full dotted name being referenced. For examples:
                1. 'import torch.nn as nn', torch.nn is external_name, nn is ref_name.
                2. 'from torch import nn as mm, torch.nn is external_name, mm is ref_name which is not a standard name.

        Returns:
            boolean, True if ref_name is standard else False.
        """
        if ref_name != 'nn' and external_name == 'torch.nn':
            is_standard = False
        elif ref_name != 'F' and external_name == 'torch.nn.functional':
            is_standard = False
        else:
            is_standard = True

        return is_standard


class CodeAnalyzer(ast.NodeVisitor):
    """Code analyzer that analyzes PyTorch python script by AST Visitor.

    CodeAnalyzer find the codes that need to be converted to MindSpore,
    and provides the attributes related to the codes.
    """

    def __init__(self):
        self._stack = []  # Used to easily access the parent node
        self._external_references = {}
        self._is_standard_external_ref = True
        self._root_scope = None
        # Used to save functions that need to be converted, value type is pasta.base.scope.Scope
        self._network_functions = []

        # Used to easily trace the function node
        self._functions_stack = []

        # key type is pasta.base.scope.Scope, value type is list
        self._network_classes = {}

    @property
    def root_scope(self):
        """The root scope of the python script code."""
        return self._root_scope

    @property
    def is_standard_external_ref(self):
        """Obtain whether the result is a standard external reference."""
        return self._is_standard_external_ref

    @property
    def external_references(self):
        """Obtain all external references in the analyzed code."""
        return self._external_references

    def network_definitions(self):
        """Obtain the network definitions which need to be converted."""
        return {"functions": self._network_functions,
                "cell": self._network_classes}

    def process(self, ast_tree):
        """
        Start to analyze the code.

        Args:
            ast_tree (AST): The root node of the source code.
        """
        self.__init__()
        self._root_scope = scope.analyze(ast_tree)
        self._pre_process()
        self.visit(ast_tree)
        if not self._network_classes:
            msg = "model definition not be found."
            raise ScriptNotSupport(msg)

    @staticmethod
    def _check_external_standard(external_refs):
        """Check whether all external references are standard."""
        is_standard = True
        for external_name, external_ref_info in external_refs.items():
            is_standard = APIAnalysisSpec.check_external_alias_ref(external_name, external_ref_info.name)
            if not is_standard:
                break
        return is_standard

    def _is_base_from_cell(self, node):
        """
        Check whether the node bases from cell classes which are defined in APIAnalysisSpec.

        Args:
            node (ast.ClassDef): The node which is a class definition.

        Returns:
            boolean, True if the check result is Passed else False.
        """
        if self._is_ref_convertible_imports(node):
            whole_name = self._get_whole_name(node)
            if whole_name.split('.')[-1] in APIAnalysisSpec.get_network_base_class_names():
                return True
        return False

    def _pre_process(self):
        """Preprocessor checks the code before analyzing."""
        is_torch = False

        # check whether the code imports torch.
        for ref_name in self._root_scope.external_references.keys():
            if ref_name.split('.')[0] in APIAnalysisSpec.get_convertible_external_names():
                is_torch = True
                break
        if not is_torch:
            msg = "The source code does not import torch, model definition can not be found."
            raise ScriptNotSupport(msg)

        # Find out external reference in the code and save it.
        external_refs = self._analyze_import_references(self._root_scope)
        self._is_standard_external_ref = self._check_external_standard(external_refs)
        self._check_external_standard(external_refs)
        for external_name, external_ref_info in external_refs.items():
            self._external_references.update({
                external_name: {
                    'external_ref_info': external_ref_info,
                    'parent_node': None
                }
            })

    @staticmethod
    def _analyze_import_references(root_scope):
        """
        Find out all references from the import statements.

        Case1: (from)import alias, node_ref.name_ref.id is node_ref.name_ref.definition.asname.
        Case2: import without alias, node_ref.name_ref.definition.asname is None.
            e.g., import a.b.c, the reference definition id maybe is a, a.b or a.b.c.
            The reference id a.b.c is really wanted.
        """
        external_name_ref = dict()
        all_node_references = []
        for node_references in root_scope.external_references.values():
            all_node_references.extend(node_references)

        for node_ref in all_node_references:
            name_ref = node_ref.name_ref
            if not name_ref:
                continue
            definition = name_ref.definition
            if node_ref.name_ref.id in [definition.asname, definition.name]:
                external_name_ref[name_ref.id] = node_ref

        return external_name_ref

    def visit(self, node):
        """Overridden visit of the base class to maintain stack information to access parent node."""
        self._stack.append(node)
        super(CodeAnalyzer, self).visit(node)
        self._stack.pop()

    @staticmethod
    def _get_full_name(node):
        """Get the full name of the node."""
        if not isinstance(node, (ast.Attribute, ast.Name)):
            return None
        return pasta.dump(node)

    def _get_whole_name(self, node):
        """
        Get the whole name of the node.

        For example, nn.Module is spliced two nodes, nn node and Module node.
        When visit ast nodes,
        Module node is first visited, the full name is the same as the whole name, that is nn.Module.
        And then nn node is visited, the full name is nn, the whole name is nn.Module.
        """
        full_name = self._get_full_name(node)
        if not full_name:
            return None
        whole_name = full_name
        # node is in stack top pos
        if node is self._stack[-1]:
            parent_index = -1
            while isinstance(self._stack[parent_index], ast.Attribute):
                parent_index -= 1

            whole_name = self._get_full_name(self._stack[parent_index])
        return whole_name

    def _is_ref_convertible_imports(self, node):
        """Check whether the node references convertible imports."""
        check_result = False
        whole_name = self._get_whole_name(node)
        if whole_name:
            module_name = whole_name.split('.')[0]
            for ref_name, ref_info in self._external_references.items():
                external_ref = ref_info['external_ref_info']
                # external reference is convertible module
                if external_ref.name in APIAnalysisSpec.get_convertible_external_names():
                    # import from the same external module
                    if module_name == ref_name.split('.')[0]:
                        check_result = True
                        break

        return check_result

    @staticmethod
    def _get_external_node(external_references, only_convertible=False):
        """Get all external reference nodes."""
        external_nodes = {}
        for ref_name, ref_info in external_references.items():
            is_add = False
            if only_convertible:
                if ref_info['external_ref_info'].name in APIAnalysisSpec.get_convertible_external_names():
                    is_add = True
            else:
                is_add = True
            if is_add:
                external_nodes.update({ref_info['external_ref_info'].node: ref_name})
        return external_nodes

    def _update_external_ref_parent(self, node):
        """Set external reference parent node info."""
        external_nodes = self._get_external_node(self._external_references, only_convertible=False)
        convertible_external_nodes = self._get_external_node(self._external_references, only_convertible=True)
        for name_node in node.names:
            if name_node in convertible_external_nodes.keys():
                if len(node.names) > 1:
                    msg = """\
                    Not support multiple imports of torch on one line in your script. line:%s: %s
                    """ % (node.lineno, pasta.dump(node))
                    raise ScriptNotSupport(msg)
            if name_node in external_nodes.keys():
                ref_name = external_nodes[name_node]
                self._external_references[ref_name]['parent_node'] = node

    @staticmethod
    def _get_class_scope(node_scope):
        """Find the class scope of the node_scope."""
        parent_scope = node_scope.parent_scope
        class_scope = None
        while parent_scope:
            if isinstance(parent_scope.node, ast.ClassDef):
                class_scope = parent_scope
                break
            parent_scope = parent_scope.parent_scope
        return class_scope

    def _update_convertible_functions(self, node):
        """Update convertible functions."""
        node_scope = self._root_scope.lookup_scope(node)
        class_scope = self._get_class_scope(node_scope)
        if class_scope:
            network_classes = self._network_classes.get(class_scope, [])
            if node_scope not in network_classes:
                network_classes.append(node_scope)
        else:
            if node_scope not in self._network_functions:
                self._network_functions.append(node_scope)

    def visit_ClassDef(self, node):
        """Callback function when visit AST tree"""
        if not self._stack[-1] is node:
            return

        for base in node.bases:
            if self._is_ref_convertible_imports(base):
                self._network_classes[self._root_scope.lookup_scope(node)] = []

        self.generic_visit(node)

    def _update_external_when_visit(self, node):
        """Update external reference when visiting import and import from statements."""
        self._update_external_ref_parent(node)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Callback function when visit AST tree"""
        self._update_external_when_visit(node)

    def visit_ImportFrom(self, node):
        """Callback function when visit AST tree"""
        self._update_external_when_visit(node)

    def visit_Call(self, node):
        """Callback function when visit AST tree"""
        if not self._stack[-1] is node:
            return
        is_in_network_function = False
        # If torch call is happened in the function, save the function for network definition.
        if self._functions_stack and self._is_ref_convertible_imports(node.func):
            self._update_convertible_functions(self._functions_stack[-1])
            is_in_network_function = True
        if not is_in_network_function:
            self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Callback function when visit AST tree"""
        if not self._stack[-1] is node:
            return
        if node.name == "forward":
            self._update_convertible_functions(node)

        self._functions_stack.append(node)
        self.generic_visit(node)
        self._functions_stack.pop()

    def get_name(self, node):
        """
        Get the node name.

        Args:
            node (AST): The ast node of the source code.

        Returns:
            str, the name of the node
        """
        if isinstance(node, pasta.base.scope.Scope):
            items = [self.get_name(node.node)]
            parent_scope = node.parent_scope
            while parent_scope:
                if not isinstance(parent_scope.node, ast.Module):
                    items.append(self.get_name(parent_scope.node))
                parent_scope = parent_scope.parent_scope
            return '.'.join(reversed(items))
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            return node.name
        if isinstance(node, (ast.Name, ast.Attribute)):
            return self._get_full_name(node)
        return str(node)

    def lookup_scope(self, node):
        """
        Search the scope of the node.

        Args:
            node (AST): The ast node of the source code.

        Returns:
            scope, the scope of the node
        """
        if isinstance(node, pasta.base.scope.Scope):
            return node
        return self._root_scope.lookup_scope(node)
