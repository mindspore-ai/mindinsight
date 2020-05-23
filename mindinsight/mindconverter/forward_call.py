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
import os


class ForwardCall(ast.NodeVisitor):
    """
    AST visitor that processes forward calls.

    Find the sub functions called by the forward function in the script file.
    """

    def __init__(self, filename):
        self.filename = filename
        self.module_name = os.path.basename(filename).replace('.py', '')
        self.name_stack = []
        self.forward_stack = []
        self.calls = []
        self.process()

    def process(self):
        """Parse the python source file to find the forward functions."""
        with open(self.filename, 'rt', encoding='utf-8') as file:
            content = file.read()
        self.visit(ast.parse(content, self.filename))

    def get_current_namespace(self):
        """Get the namespace when visit the AST node"""
        namespace = '.'.join(self.name_stack)
        return namespace

    @classmethod
    def get_ast_node_name(cls, node):
        """Get AST node name."""
        if isinstance(node, ast.Attribute):
            return f'{cls.get_ast_node_name(node.value)}.{node.attr}'

        if isinstance(node, ast.Name):
            return node.id

        return node

    def visit_ClassDef(self, node):
        """Callback function when visit AST tree"""
        self.name_stack.append(node.name)
        self.generic_visit(node)
        self.name_stack.pop()

    def visit_FunctionDef(self, node):
        """Callback function when visit AST tree"""
        func_name = f'{self.get_current_namespace()}.{node.name}'
        is_in_chain = func_name in self.calls or node.name == 'forward'
        if is_in_chain:
            self.forward_stack.append(func_name)

        if node.name == 'forward':
            self.calls.append(func_name)

        self.generic_visit(node)

        if is_in_chain:
            self.forward_stack.pop()

    def visit_Call(self, node):
        """Callback function when visit AST tree"""
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw.value)
        func_name = self.get_ast_node_name(node.func)
        if isinstance(node.func, ast.Name):
            if func_name not in ['super', 'str', 'repr']:
                if self.forward_stack:
                    self.calls.append(func_name)
                self.visit(node.func)
        else:
            if self.forward_stack:
                if 'self' in func_name:
                    self.calls.append(f'{self.get_current_namespace()}.{func_name.split(".")[-1]}')
                else:
                    self.calls.append(func_name)
                self.visit(node.func)
