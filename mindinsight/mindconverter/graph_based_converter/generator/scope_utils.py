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
"""Define a scope class processing all operations related to scope and scope name."""
import re


class Scope():
    """Define scope related operations."""

    def __init__(self, scope_str):
        scopes = scope_str.split('/')
        self.module_path = list()
        self.scope_list = scopes[:-1]
        self.head = self.scope_list[0]
        self.tail = self.scope_list[-1]
        self.initialization()

    def initialization(self):
        """Init scope class."""
        self._update_module_path_from_scope_list()

    def _update_module_path_from_scope_list(self):
        """Update the module scope path from a list of scope."""
        self.module_path = list()
        for scope in self.scope_list:
            if scope == 'Model':
                continue

            if 'Module' in scope:
                regex = r"Module(?P<num>\d+)_(?P<curr_level_unique_id>\d+)"
                match = re.match(regex, scope)
                if match:
                    module_num = match.group('num')
                    uid = match.group('curr_level_unique_id')
                    self.module_path.append((int(module_num), int(uid)))

    @property
    def path(self):
        """Return module scope path."""
        return self.module_path

    def set_path(self, ind, path_tuple: tuple):
        """
        Set the module scope path.

        Args:
            ind (int): The index of the scope path to be set.
            path_tuple ((int, int)): The tuple of the scope path.
        """
        self.module_path[ind] = path_tuple

    @property
    def to_str(self):
        """Return the full module scope as the string format."""
        full_str_list = ["Model"]
        for (num, uid) in self.module_path:
            local = "Module{}_{}".format(num, uid)
            full_str_list.append(local)

        return "/".join(full_str_list)

    @property
    def depth(self):
        """Return the depth of the scope path."""
        return len(self.path)

    @staticmethod
    def scope_to_module_name(path):
        """
        Helper function to convert any scope path string to the full module scope.

        Args:
            path (str): path string like "[(5, 0), (3, 0)]"

        Returns:
            str, the full module scope with format like "Model/Module5_0/Module3_0/"
        """
        scope_str_list = ["Model"]
        if isinstance(path, str):
            path = Scope.path_str_to_list(path)
        if isinstance(path, list):
            for (num, uid) in path:
                local = "Module{}_{}".format(num, uid)
                scope_str_list.append(local)

        return "/".join(scope_str_list)

    @staticmethod
    def parse_scope_from_node_identifier(node_identifier: str):
        """
        Helper function to parse the scope string from node identifier.

        Args:
            node_identifier (str): The string of the node identifier.

        Returns:
            str, parsed scope string from node identifier.
        """
        regex = r"(?P<scope>Model/.*)\$\S+\$"
        match = re.match(regex, node_identifier)
        if not match:
            return None
        return match.group('scope')

    @staticmethod
    def path_str_to_list(scope_path_str: str):
        """
        Helper function to convert the scope path string back to list.

        Args:
            scope_path_str (str): The scope path string like "[(5, 0), (3, 0)]".

        Returns:
            list, a list of the scope path like [(5, 0), (3, 0)].
        """
        ret = []
        tmp = scope_path_str.strip('[').strip(']')
        regex = r"\((?P<num>\d+), (?P<uid>\d+)\)"
        s_all = re.findall(regex, tmp)
        for (num, uid) in s_all:
            ret.append((int(num), int(uid)))

        return ret

    @staticmethod
    def get_parent_module_num_and_uid(path):
        """
        Helper function to return its parent's scope tuple.

        Args:
            path (Union[str, list]): Module scope path string. e.g. "[(5, 0), (3, 0)]"

        Returns:
            tuple, parent's scope level. e.g. [(5, 0)]
        """
        if isinstance(path, str):
            path = Scope.path_str_to_list(path)
        if isinstance(path, list):
            if len(path) == 1: # modules under the main module, (-1, -1) means main module.
                return (-1, -1)
            if len(path) > 1: # modules under another non-main module. Return parent's scope.
                parent = path[-2]
                return parent

        return None
