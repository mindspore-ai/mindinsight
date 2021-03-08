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
"""Define CodeLine object."""
import abc
import re
from typing import List, Tuple

from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords


class Fragment(abc.ABC):
    """
    Define comment attributes of code generation.

    Args:
        operation (str): Operation name in MindSpore.
        actual_args (dict): Actual arg values.
        input_shape (tuple): The input shape of the node.
        output_shape (tuple): The output shape of the node.
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
        """Code Setting getter."""
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
        """Return the input shape."""
        return self._input_shape

    @property
    def output_shape(self):
        """Return the output shape."""
        return self._output_shape


class NewFragment:
    """
    Fragment definition for MindSpore code generation.

    Args:
        data_entity (dict): Required data by operations. The format of `data_entity` is as follow:
            {
                "var1": {
                    "metadata": {  # ONNX Metadata
                        "operation": "Conv2d",
                        "source": "conv_pw_13/Conv2D",
                        "attributes": {
                            # Put original onnx attributes here.
                        }
                    },
                    "variable_name": None,
                    "inputs": [],
                    "output_type": "tensor" | "array",
                    "args": {"in_channels": 768, "out_channels": 1024},
                    "trainable_params": {"weight": "Parameter(Tensor(GLOBAL_W[NAME]))"}
                },
                "var2": {
                    "variable_name": "pad",
                    "args": {"padding": [0, 1, 1, 0], "mode": "SAME"}
                }
            }
        code_template (dict): Code template generated by mapper. The format of `code_template` is as follow:
            {
                "var1": {
                    "init": [
                        "self.{var1} = nn.Conv2d(in_channels={in_channels})",
                        "self.{var1}.weight = {weight}"
                    ],
                    "construct": [
                        "opt_{var1} = self.{var1}({inputs}[, extra])"
                    ]
                },
                "var2": {
                    "init": [
                        "self.{var2} = nn.Pad(padding={padding}, mode={mode})"
                    ],
                    "construct": [
                        "opt_{var2} = self.{var2}(opt_{var1}[, extra])"
                    ]
                }
            }
        outputs (list[str]): Outputs name slot list.
        outputs_mapping (tuple): Outputs index mapping between ir node and MindSpore operation.
    """

    def __init__(self, data_entity: dict, code_template: dict, outputs: List[str], outputs_mapping):
        self.exchange_msg = data_entity
        self._code_template = code_template
        self.inputs = []
        self._outputs = outputs
        self.outputs_mapping = outputs_mapping
        self.format_args = dict()

    def _get_outputs(self):
        """
        Get outputs of the code snippet.

        Returns:
            list[str], outputs of current code block.
        """
        outputs = []
        variables = {
            k: self.exchange_msg[k][ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value]
            for k in self.exchange_msg if k != ExchangeMessageKeywords.METADATA.value
        }
        for o in self._outputs:
            extractor = r".*\{(?P<var>.+)\}.*"
            var_def = re.match(extractor, o)
            if not var_def:
                raise ValueError(f"Output variable name {o} is illegal.")
            outputs.append(
                (
                    o.format(**variables),
                    self.exchange_msg[var_def.group("var")][
                        ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value]
                )
            )
        return outputs

    def get_outputs_by_idx(self, idx, inner_idx=-1):
        """Get outputs by idx."""
        outputs = self._get_outputs()
        opt, opt_type = outputs[idx]
        if opt_type == ExchangeMessageKeywords.VariableScope.value.ARR_TYPE.value:
            return f"{opt}[{inner_idx}]"
        return opt

    @staticmethod
    def create_parameter(weight_shape, weight_dtype):
        """Create a parameter code line."""
        return f"Parameter(Tensor(np.random.uniform(0, 1, {weight_shape}).astype(np.{weight_dtype})), " \
               f"name=None)"

    def __call__(self) -> Tuple[List[str], List[str]]:
        """
        Define parameter rewrite function.

        Returns:
            tuple[list[str], list[str]], init statement and construct statement.
        """
        init_stats, call_stats = [], []
        precursor_node_var = [None, None]
        for op_var, template in self._code_template.items():
            if ExchangeMessageKeywords.VariableScope.value.INPUTS.value not in self.exchange_msg[op_var]:
                # It's possible inputs and precursor node both exists.
                self.exchange_msg[op_var][ExchangeMessageKeywords.VariableScope.value.ARGS.value][
                    precursor_node_var[0]] = precursor_node_var[1]
            for tpl in template[TemplateKeywords.INIT.value]:
                init_stat = self._rewrite(op_var, self.exchange_msg[op_var], tpl)
                init_stats.append(init_stat)
            for tpl in template[TemplateKeywords.CONSTRUCT.value]:
                call_stat = self._rewrite(op_var, self.exchange_msg[op_var], tpl)
                call_stats.append(call_stat)
            precursor_node_var = op_var, self.exchange_msg[op_var].get(
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value)
        return init_stats, call_stats

    def register_parameter(self, var, line):
        """Append a new parameter into template."""
        self._code_template[var][TemplateKeywords.INIT.value].append(line)

    @staticmethod
    def _rewrite(var, data, template: str) -> str:
        """
        Backfill data into code template.

        Args:
            var (str): Current operation variable name.
            data (dict): Data to be written.
            template (str): Code template.

        Returns:
            str, single code line.
        """
        rewrite_data = {var: data[ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value]}
        if ExchangeMessageKeywords.VariableScope.value.INPUTS.value in data:
            group_inputs = ExchangeMessageKeywords.VariableScope.value.GROUP_INPUTS.value
            if group_inputs in data:
                input_tuple_list = []
                tuple_index = 0
                tuple_id = 0
                while tuple_index < len(data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value]):
                    if tuple_id < len(data[group_inputs]) and tuple_index in data[group_inputs][tuple_id]:
                        tuple_added = ", ".join(data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value]
                                                [data[group_inputs][tuple_id][0]:
                                                 data[group_inputs][tuple_id][-1]+1])
                        tuple_added = f"({tuple_added})"
                        input_tuple_list.append(tuple_added)
                        tuple_index = data[group_inputs][tuple_id][-1]+1
                        tuple_id += 1
                        continue
                    input_tuple_list.append(data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value]
                                            [tuple_index])
                    tuple_index += 1

                rewrite_data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value] = \
                    ", ".join(input_tuple_list)
            else:
                rewrite_data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value] = ", ".join(
                    data[ExchangeMessageKeywords.VariableScope.value.INPUTS.value])
        if ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value in data:
            rewrite_data.update(data[ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value])
        if ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value in data:
            rewrite_params = {
                f"{var}/{slot}": data[ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value].get(slot)
                for slot in data[ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value]
            }
            rewrite_data.update(rewrite_params)
        rewrite_data.update(data[ExchangeMessageKeywords.VariableScope.value.ARGS.value])
        template = template.format(**{
            k: str(rewrite_data[k]) for k in rewrite_data
        })
        return template.format(**{
            k: str(rewrite_data[k]) for k in rewrite_data
        })
