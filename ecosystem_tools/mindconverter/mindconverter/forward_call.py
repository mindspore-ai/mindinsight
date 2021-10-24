# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Find out forward functions of script file"""
import ast

import pasta


class ForwardCall(ast.NodeVisitor):
    """
    AST visitor that processes forward calls.

    Find the sub functions called by the forward function in the script file.
    """

    def __init__(self, ast_tree):
        self._tree = ast_tree
        self._name_stack = []
        self._forward_stack = []
        self.calls = {}  # key is function name, value is forward function ast node.
        self._function_list = {}  # key is function name, value is function ast node.
        self.process()

    def process(self):
        """visit ast tree to find the forward functions."""
        self.visit(self._tree)
        # first visit to find out all functions, so restores all variables except _function_list
        self._name_stack.clear()
        self._forward_stack.clear()
        self.calls.clear()
        self.visit(self._tree)

    def get_current_namespace(self):
        """Get the namespace when visit the AST node"""
        namespace = '.'.join(self._name_stack)
        return namespace

    @classmethod
    def get_call_name(cls, node):
        """Get functional call name."""
        if not isinstance(node, ast.Call):
            return None

        return pasta.dump(node.func)

    def visit_ClassDef(self, node):
        """Callback function when visit AST tree"""
        self._name_stack.append(node.name)
        self.generic_visit(node)
        self._name_stack.pop()

    def visit_FunctionDef(self, node):
        """Callback function when visit AST tree"""
        namespace = self.get_current_namespace()
        if namespace:
            func_name = f'{namespace}.{node.name}'
        else:
            func_name = node.name
        func_name = f'{self.get_current_namespace()}.{node.name}'
        is_in_chain = func_name in self.calls or node.name == 'forward'
        if is_in_chain:
            self._forward_stack.append(func_name)

        if node.name == 'forward':
            self.calls.update({func_name: node})

        self._function_list.update({func_name: node})
        self.generic_visit(node)

        if is_in_chain:
            self._forward_stack.pop()

    def visit_Call(self, node):
        """Callback function when visit AST tree"""
        for arg in node.args:
            self.visit(arg)
        for keyword in node.keywords:
            self.visit(keyword.value)
        func_name = self.get_call_name(node)
        if isinstance(node.func, ast.Name):
            if func_name not in ['super', 'str', 'repr']:
                if self._forward_stack:
                    self.calls.update({func_name: self._function_list.get(func_name)})
                self.visit(node.func)
        else:
            if self._forward_stack:
                if func_name.startswith('self.'):
                    whole_name = f'{self.get_current_namespace()}.{func_name.split(".")[-1]}'
                    self.calls.update({whole_name: self._function_list.get(whole_name)})
                else:
                    self.calls.update({func_name: self._function_list.get(func_name)})
                self.visit(node.func)
