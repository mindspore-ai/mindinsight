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
import re

from .base import GraphNode
from ..common.utils import is_converted

from ..constant import NodeType, SEPARATOR_IN_SCOPE, SEPARATOR_BTW_NAME_AND_ID, LEFT_BUCKET, RIGHT_BUCKET, \
    SEPARATOR_IN_ONNX_OP, SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT


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
        self._weight = weight
        self._ipt_var_names, self._opt_var_names \
            = self._extract_ipt_opt_var_names() if node else (list(), list())

    def _extract_ipt_opt_var_names(self):
        """Extract ipt and opt var names."""
        node_content = SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT.join(
            str(self._src_node).split(SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT)[1:]
        )
        node_inputs = re.findall(r"[(](.*?)[)]", node_content)[0]
        node_inputs = re.sub(r"[\s%]", '', node_inputs).split(",")
        node_title = str(self._src_node).split(SEPARATOR_TITLE_AND_CONTENT_IN_CONSTRUCT)[0]
        node_outputs = re.findall(r"[%](.*?) [:]", node_title)
        return node_inputs, node_outputs

    def clear_args_of_declaration(self):
        """
        Clear `self._args_in_code`.
        """
        self._args_in_code = dict()

    def _get_arg_name(self, arg, variable_name):
        """
        Get arg name.

        Args:
            arg (str): Generate arg name.

        Returns:
            str, arg name in function or class declaration.
        """
        return f"{arg}_{variable_name}"

    @property
    def is_in_multi_opt_graph(self):
        return self._is_in_multi_opt_graph

    @is_in_multi_opt_graph.setter
    def is_in_multi_opt_graph(self, multi_opt_state):
        self._is_in_multi_opt_graph = multi_opt_state

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

    def to_code(self, ipt_args_in_construct: str, variable_name: str, output_var: list, code_fragment):
        """
        Generate statements.

        Args:
            variable_name (str): Variable name.
            ipt_args_in_construct (str): Args of input.
            output_var (list): Output variable names in construct.
            code_fragment (CodeFragment): CodeFragment instance.

        Returns:
            Union[str, str], declare in init and call in construct.
        """
        operator = code_fragment.operation

        args = self.args_in_code
        settings = code_fragment.code_setting

        if self._node_type == NodeType.OPERATION.value and not is_converted(code_fragment.operation):
            args.update({"input_shape": self.input_shape,
                         "output_shape": self.output_shape})

        if self._node_type == NodeType.OPERATION.value:
            expr = ", ".join([f"{k.replace(f'_{variable_name}', '')}={v}"
                              for k, v in args.items()])
            ipt_args_settings_in_construct = self._generate_ipt_args_settings_in_construct(
                ipt_args_in_construct, settings)
        else:
            # When it's type is module, class or func,
            # it's not necessary to replace var.
            expr = ", ".join([f"{k.replace(f'_{variable_name}', '')}={v}"
                              for k, v in args.items()])
            ipt_args_settings_in_construct = ipt_args_in_construct

        if SEPARATOR_IN_ONNX_OP in operator:
            operator = operator.replace(SEPARATOR_IN_ONNX_OP, ".")

        declare = f"self.{variable_name} = {operator}({expr})"
        call = f"{', '.join([output for output in output_var])}" \
               f" = self.{variable_name}({ipt_args_settings_in_construct})"

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
