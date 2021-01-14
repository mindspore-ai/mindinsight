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
"""Name manager."""
import abc


class NameMgr(abc.ABC):
    """Module name manager."""
    PLACEHOLDER = 1

    def __init__(self):
        self.record = dict()
        self.topo_order = []

    def get_name(self, old_name):
        """
        Get module/variable name.

        If the module already existed, then add a suffix to it.

        Args:
            old_name (str): Name.

        Returns:
            str, module name.
        """
        if old_name not in self.record:
            self.record[old_name] = [self.PLACEHOLDER]
            suffix = ""
        else:
            self.record[old_name].append(self.PLACEHOLDER)
            suffix = f"{len(self.record[old_name]) - 1}"

        new_name = f"{old_name}{suffix}"
        self.topo_order.append(new_name)

        return new_name


class ModuleNameMgr(NameMgr):
    """Module name manager."""


# Manage variable name of different modules.
global_var_namespace = set()
# Manage variable name of different type.
global_op_namespace = dict()
START_IDX = 0


class GlobalVarNameMgr:
    """Global variable name mgr."""

    def __init__(self):
        global_op_namespace.clear()
        global_var_namespace.clear()

    @staticmethod
    def _get_name(name):
        """Deal with op name."""
        if "::" in name:
            return name.split("::")[1]
        return name

    def get_name(self, op_type):
        """
        Get module/variable name.

        If the module already existed, then add a suffix to it.

        conv1 onnx::conv

        Args:
            op_type (str): Operator type in onnx.

        Returns:
            str, module name.
        """

        def _gen(t):
            t = t.lower()
            if t not in global_op_namespace:
                global_op_namespace[t] = START_IDX
                suffix = ""
            else:
                global_op_namespace[t] += 1
                suffix = f"{global_op_namespace[t] - 1}"

            return f"{self._get_name(t)}{suffix}"

        new_name = _gen(op_type)
        while new_name in global_var_namespace:
            new_name = _gen(op_type)

        global_var_namespace.add(new_name)
        return new_name


class LocalVarNameMgr:
    """Local variable name mgr."""

    def __init__(self):
        self.local_op_namespace = dict()
        self.local_var_namespace = set()

    @staticmethod
    def _get_name(name):
        """Deal with op name."""
        if "::" in name:
            return name.split("::")[1]
        return name

    def get_name(self, op_type):
        """
        Get module/variable name.

        If the module already existed, then add a suffix to it.

        conv1 onnx::conv

        Args:
            op_type (str): Operator type in onnx.

        Returns:
            str, module name.
        """

        def _gen(t):
            t = t.lower()
            if t not in self.local_op_namespace:
                self.local_op_namespace[t] = START_IDX
                suffix = ""
            else:
                self.local_op_namespace[t] += 1
                suffix = f"{self.local_op_namespace[t] - 1}"

            return f"{self._get_name(t)}{suffix}"

        new_name = _gen(op_type)
        while new_name in self.local_var_namespace:
            new_name = _gen(op_type)

        self.local_var_namespace.add(new_name)
        return new_name
