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
"""Define ONNX graph node."""
from importlib import import_module

from mindinsight.mindconverter.graph_based_converter.third_party_graph.base import GraphNode
from mindinsight.mindconverter.graph_based_converter.common.utils import is_converted

from mindinsight.mindconverter.graph_based_converter.constant import NodeType, SEPARATOR_IN_SCOPE, \
    SEPARATOR_BTW_NAME_AND_ID, LEFT_BUCKET, RIGHT_BUCKET, SEPARATOR_IN_ONNX_OP


class OnnxGraphNode(GraphNode):
    """
    ONNX Graph Node.

    Args:
        node (OnnxNode): OnnxNode Object.
        weight (list): List of recording node weights.
    """
    _type_frozen = False
    _module_name_frozen = False

    def __init__(self, node=None, weight=None):
        super(OnnxGraphNode, self).__init__(node=node)
        self._op_params = self._get_raw_params(node.raw_node) if node else None
        self._op_name = "onnx::" + node.op_type if node else None
        self._scope_name = node.scope_name if node else None
        self._weight = weight

    def clear_args_of_declaration(self):
        """Clear `self._args_in_code`."""
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
        Op name in onnx.

        Returns:
            str, op name
        """
        return self._op_name

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

    def _add_tensor_args_to_code(self, op_name: str, settings, declare, args, variable_name):
        """
        Add nn used tensors to args in init and construct blocks.

        Args:
            op_name (str): Add the tensor to args if the current node has this
                op_name.
            declare (str): Declare statement generated in to_code().
            args (str): Args statement generated in to_code().

        Returns:
            declare_list list, multiple declare statements.
            input_args list, multiple input args generated statements.
        """
        if not self._op_name == op_name:
            return declare, args
        if not settings or not settings.op_extra_tensor:
            # TensorAdd operation in onnx could add a tensor twice.
            ipt_vars = args.split(", ")
            if len(ipt_vars) == 1:
                args = f"{ipt_vars[0]}, {ipt_vars[0]}"
            return declare, args
        declare_list = [declare]
        declare_t = f"self.{variable_name}_w = Tensor(" \
                    f"np.random.uniform(0, 1, {str(settings.op_extra_tensor.shape)}), " \
                    f"{settings.op_extra_tensor.dtype})"
        declare_list.append(declare_t)
        args += f", self.{variable_name}_w"
        return declare_list, args

    def to_code(self, ipt_args_in_construct: str, variable_name: str, output_var: str,
                code_fragment):
        """
        Generate statements.

        Args:
            variable_name (str): Variable name.
            ipt_args_in_construct (str): Args of input.
            output_var (str): Output variable name in construct.
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

        # Extra Tensor generator for nn.MatMul
        declare, ipt_args_settings_in_construct = self._add_tensor_args_to_code(
            'onnx::MatMul', settings, declare, ipt_args_settings_in_construct, variable_name)

        # Extra Tensor generator for onnx::Add
        declare, ipt_args_settings_in_construct = self._add_tensor_args_to_code(
            'onnx::Add', settings, declare, ipt_args_settings_in_construct, variable_name)

        # Extra Tensor generator for onnx::Mul
        declare, ipt_args_settings_in_construct = self._add_tensor_args_to_code(
            'onnx::Mul', settings, declare, ipt_args_settings_in_construct, variable_name)

        call = f"{output_var} = self.{variable_name}({ipt_args_settings_in_construct})"

        return declare, call

    def to_ir(self):
        """No need to implement for now."""
        raise NotImplementedError

    def _get_raw_params(self, node):
        """
        Get params in onnx.
        Note: parameters are attributes in node.

        Args:
            node (onnx.NodeProto): Onnx defined node proto.

        Returns:
            dict, raw params.
        """
        onnx = import_module("onnx")

        raw_params = dict()

        if not node:
            return raw_params

        for attribute in node.attribute:
            name = attribute.name
            value = onnx.helper.get_attribute_value(attribute)
            raw_params[name] = value

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
        """Extract variable name from scope name."""
        if not scope_name:
            return None
        var = scope_name.split(SEPARATOR_IN_SCOPE)[-1].lower()
        var = var.replace(LEFT_BUCKET, SEPARATOR_BTW_NAME_AND_ID).replace(
            RIGHT_BUCKET, "")
        return var
