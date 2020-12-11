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
"""Define CodeLine object."""
import abc


class TrainableParams:
    """Trainable parameters."""

    def __init__(self, shape, dtype, reference):
        self.param_name = None
        self.shape = shape
        self.dtype = dtype
        self.reference = reference  # Weight name in global npy.


class CodeSetting:
    """Code generation settings."""

    def __init__(self):
        self.output_vars_suffix = []
        self.operation_input_type = None  # Construct input type, tensor or list.
        self.operation_extra_input = dict()  # `values` in original setting dict.
        self.operation_extra_tensor = None  # For `MatMul`, `BiasAdd` op, need a tensor


class Fragment(abc.ABC):
    """
    Define comment attributes of code generation.

    Args:
        operation (str): Operation name in MindSpore.
        actual_args (dict): Actual arg values.
        settings (namedTuple): Code generation setting.

    """

    def __init__(self, operation, actual_args, input_shape, output_shape, settings=None):
        self._operation = operation
        self._input_shape = input_shape
        self._output_shape = output_shape
        self._declared_variable_name = None
        self._output_var_name = list()  # Output variable name(could be multi-opt).
        self._operation_inputs = list()  # Index indices the order of input.
        self._operation_extra_inputs = settings
        self._code_setting = settings
        self._formal_args_list = dict()
        self._actual_args_list = actual_args  # Key is the param_key, value is the corresponding value.
        self._node_type = ""

    @property
    def code_setting(self):
        return self._code_setting

    @property
    def node_type(self):
        """Node type getter."""
        return self._node_type

    @node_type.setter
    def node_type(self, t):
        """Node type setter."""
        self._node_type = t

    @property
    def operation_extra_inputs(self):
        """Getter of extra operation inputs."""
        return self._operation_extra_inputs

    @property
    def declared_var_name(self):
        """Declared variable name getter."""
        return self._declared_variable_name

    @declared_var_name.setter
    def declared_var_name(self, var):
        """Setter of declared variable name."""
        self._declared_variable_name = var

    @property
    def output_var_name(self) -> list:
        """Getter of output variable name."""
        return self._output_var_name

    @output_var_name.setter
    def output_var_name(self, opt_vars):
        """
        Output variable name setter.

        Args:
            opt_vars (list[str]): Output variable name.

        """
        self._output_var_name = opt_vars

    @property
    def operation_inputs(self):
        """
        Operation getter.

        Returns:
            list[Fragment], list of inputs.
        """
        return self._operation_inputs

    def update_operation_inputs(self, ipt):
        """
        Update operation inputs.

        Args:
            ipt (Fragment): Where input comes from.

        """
        self._operation_inputs += ipt

    @property
    def operation(self):
        """
        Operation getter.

        Returns:
            str, operation name to be initialized.
        """
        return self._operation

    @operation.setter
    def operation(self, op: str):
        """
        Operation setter.

        Args:
            op (str): Operation name.

        """
        self._operation = op

    @property
    def actual_args(self) -> dict:
        """Getter of actual args."""
        return self._actual_args_list

    @property
    def formal_args(self) -> dict:
        """Get formal args."""
        return self._formal_args_list

    def update_formal_args(self, formal_args: dict):
        """
        Update formal args.

        Args:
            formal_args (dict): To be updated args.

        """
        return self._formal_args_list.update(formal_args)

    @property
    def input_shape(self):
        return self._input_shape

    @property
    def output_shape(self):
        return self._output_shape


class CodeFragment(Fragment):
    """
    Manage the variables related with code generation.

    For single operation type node, the variables in `CodeLine` stands for:
    ```python
    class Module(nn.Cell):
        def __init__ (self, ...):
            super(Module, self).__init__()
            self.<CodeLine.declared_variable_name> = <CodeLine.operation>(<CodeLine.scalar_args>,
                                                                          <CodeLine.init_trainable_params>)
            self.<CodeLine.trainable_params[k].param_name> = Tensor(<CodeLine.trainable_params[k].shape>,
                                                                    dtype=<CodeLine._trainable_params[k].dtype>)

        def construct(self, x, ...):
            <CodeLine.output_var_name> = self.<CodeLine.declared_variable_name>(<CodeLine.operation_inputs>)
            ...
            return output
    ```

    Args:
        operation (str): Operation name in MindSpore.
        actual_args (dict): Actual arg values.
        settings (namedTuple): Code generation setting.

    """

    def __init__(self, operation, actual_args, settings, input_shape, output_shape,
                 trainable_params=None):
        super(CodeFragment, self).__init__(operation=operation, actual_args=actual_args,
                                           input_shape=input_shape, output_shape=output_shape,
                                           settings=settings)
        self._trainable_params = dict()  # External weights, like Matmul.
        self._init_trainable_params = trainable_params  # Can put into operation init method, like Conv2d.

    @property
    def trainable_params(self):
        return self._trainable_params


class ModuleFragment(Fragment):
    """Manage module type code variables."""

    def __init__(self, operation, actual_args, settings, input_shape, output_shape):
        super(ModuleFragment, self).__init__(operation=operation, actual_args=actual_args,
                                             input_shape=input_shape, output_shape=output_shape,
                                             settings=settings)
