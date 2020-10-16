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
"""Define PyTorch graph node."""
from copy import deepcopy

from .base import GraphNode

from ..constant import NodeType, SEPARATOR_IN_SCOPE, SEPARATOR_BTW_NAME_AND_ID, LEFT_BUCKET, RIGHT_BUCKET, \
    SEPARATOR_IN_ONNX_OP
from ..mapper.base import Mapper


class PyTorchGraphNode(GraphNode):
    """
    PyTorch graph node.

    Args:
        node (torch._C.Node): Node in raw PyTorch graph.

    """

    _type_frozen = False
    _module_name_frozen = False

    def __init__(self, node=None, weight=None):
        super(PyTorchGraphNode, self).__init__(node=node)
        self._op_params = self._get_raw_params(node)
        self._op_name = node.kind() if node else None
        self._scope_name = node.scopeName() if node else None
        self._opt_var_name = None
        self._variable_name = self._extract_var_name(self._scope_name)
        self._module_name = None
        self._weight = weight

    def clear_args_of_declaration(self):
        """
        Clear `self._args_in_code`.
        """
        self._args_in_code = dict()

    def _get_arg_name(self, arg):
        """
        Get arg name.

        Args:
            arg (str): Generate arg name.

        Returns:
            str, arg name in function or class declaration.
        """
        return f"{arg}_{self._variable_name}"

    @property
    def hash_key(self):
        """
        Return unique hash key of current node.

        Returns:
            str, hash key.
        """
        if self._node_type not in {NodeType.CLASS.value,
                                   NodeType.FUNC.value,
                                   NodeType.MODULE.value}:
            self._hash_key = self._op_name.lower()
        return self._hash_key

    @hash_key.setter
    def hash_key(self, h):
        """
        Setter of hash key.

        Args:
            h (str): Key.

        """
        self._hash_key = h

    @property
    def variable_name(self):
        """
        Variable name.

        Returns:
            str, variable name declared in init.
        """
        return self._variable_name

    @variable_name.setter
    def variable_name(self, v):
        """
        Setter of variable name.

        Args:
            v (str): Variable name.

        """
        self._variable_name = v

    @property
    def module_name(self):
        """
        Module name.

        Returns:
            str, module name.
        """
        if not self._module_name_frozen:
            module_name = self.tag
            return module_name

        return self._module_name

    def _froze_module_name(self, m):
        """
        Once module_name is set, then it's unchangeable.

        Args:
            m (str): Module name.

        """
        if not self._module_name_frozen:
            self._module_name = m
            self._module_name_frozen = True

    @property
    def op_name(self):
        """
        Op name in torch.

        Returns:
            str, op name.
        """
        return self._op_name

    @op_name.setter
    def op_name(self, name):
        """
        Setter of op name.

        Args:
            name(str): op_name.

        """
        self._op_name = name

    @property
    def real_name(self):
        return

    def add_input_and_output_shape(self, input_shape, output_shape):
        """
        Add the node input shape.

        Args:
            output_shape (tuple): Output tensor shape.
            input_shape (tuple): Input tensor shape.

        """
        self._ipt_shape = input_shape
        self._opt_shape = output_shape

    def to_code(self, ipt_args_in_construct: str, output_var: str):
        """
        Generate statements.

        Args:
            ipt_args_in_construct (str): Args of input.
            output_var (str): Output variable name in construct.

        Returns:
            Union[str, str], declare in init and call in construct.
        """
        operator = self.op_in_ms or self.module_name
        self._opt_var_name = output_var

        args = self.args_in_code
        if self._node_type == NodeType.OPERATION.value and not self.convert_successful():
            args.update({"input_shape": self.input_shape,
                         "output_shape": self.output_shape})

        if self._node_type == NodeType.OPERATION.value:
            expr = ", ".join([f"{k.replace(f'_{self._variable_name}', '')}={v}"
                              for k, v in args.items()])
        else:
            # When it's type is module, class or func,
            # it's not necessary to replace var.
            expr = ", ".join([f"{k.replace(f'_{self._variable_name}', '')}={v}"
                              for k, v in args.items()])
        declare = f"self.{self._variable_name} = {operator}({expr})"
        call = f"{self._opt_var_name} = self.{self._variable_name}({ipt_args_in_construct})"

        return declare, call

    def to_ir(self):
        """
        No need to implement for now.
        """
        raise NotImplementedError

    def _get_raw_params(self, node):
        """
        Get params in onnx.

        Args:
            node (Any): Node.

        Returns:
            dict, raw params.
        """
        from .torch_utils import getitem_of_node

        raw_params = dict()

        if not node:
            return raw_params

        for k in node.attributeNames():
            raw_params[k] = getitem_of_node(node, k)
        return raw_params

    def replace_with_arg(self, src_arg, tgt_arg):
        """
        Replace actual parameter with formal parameter.

        Args:
            src_arg (str): Original arg name.
            tgt_arg (str): Target arg name.

        """
        self._args_in_code[src_arg] = tgt_arg

    @staticmethod
    def _extract_var_name(scope_name: str):
        """
        Extract variable name from scope name.
        """
        if not scope_name:
            return None
        var = scope_name.split(SEPARATOR_IN_SCOPE)[-1].lower()
        var = var.replace(LEFT_BUCKET, SEPARATOR_BTW_NAME_AND_ID).replace(
            RIGHT_BUCKET, "")
        return var

    def param_transform(self, mapper: Mapper):
        """
        Transform torch params into mindspore.

        Args:
            mapper (Mapper): Mapper of params.

        """
        if self._node_type != NodeType.OPERATION.value:
            args = deepcopy(self._args_in_code)
            self._args_in_code = dict()
            for arg, value in args.items():
                self._args_in_code[self._get_arg_name(arg)] = value
            return None, None

        if not self.transformed:
            _, _ = super(PyTorchGraphNode, self).param_transform(mapper)

            for arg, value in self._params_in_ms.items():
                self._args_in_code[self._get_arg_name(arg)] = value

            self.transformed = True

        return self._op_in_ms, self._params_in_ms

    def froze_node_type_and_module_name(self, node_type, module_name):
        """
        Froze node type and module name.

        After node_type is frozen, then the `module_name`
        will be affected when `node_type` is `class`.
        Thus, this line must be placed before `nd_inst.data.module_name`.

        Args:
            module_name: Modified module name.
            node_type (str): Node type, class of func.

        """
        if not self._type_frozen:
            self._node_type = node_type
            self._type_frozen = True

        if not self._module_name_frozen:
            self._froze_module_name(module_name)

    def convert_successful(self):
        """
        Whether convert successfully.

        Returns:
            bool, true or false.
        """
        if self._op_in_ms and SEPARATOR_IN_ONNX_OP not in self._op_in_ms:
            return True
        return False
