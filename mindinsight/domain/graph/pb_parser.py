# Copyright 2021 Huawei Technologies Co., Ltd
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
"""PB parser module."""
import numpy as np

from mindinsight.domain.graph.base import MindSporeType, InputType, OutputType
from mindinsight.domain.graph.base import NodeInput, NodeOutput, Tensor, Source, Constant, Parameter, Operator, Parser
from mindinsight.domain.graph.exceptions import UnknownDataTypeError, TupleGetitemIndexError
from mindinsight.domain.graph.proto import ms_graph_pb2 as graph_proto


class PBParser(Parser):
    """Protobuf file parser."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.proto = graph_proto
        self.dtype_mapping = {
            self.proto.DT_UNDEFINED: None,
            self.proto.DT_BOOL: 'bool',
            self.proto.DT_INT8: 'int8',
            self.proto.DT_INT16: 'int16',
            self.proto.DT_INT32: 'int32',
            self.proto.DT_INT64: 'int64',
            self.proto.DT_UINT8: 'uint8',
            self.proto.DT_UINT16: 'uint16',
            self.proto.DT_UINT32: 'uint32',
            self.proto.DT_UINT64: 'uint64',
            self.proto.DT_FLOAT16: 'float16',
            self.proto.DT_FLOAT32: 'float32',
            self.proto.DT_FLOAT64: 'float64',
            self.proto.DT_TENSOR: 'tensor',
            self.proto.DT_TUPLE: 'tuple',
            self.proto.DT_STRING: 'string',
            self.proto.DT_BASE_INT: MindSporeType.INT,
            self.proto.DT_BASE_UINT: MindSporeType.UINT,
            self.proto.DT_BASE_FLOAT: MindSporeType.FLOAT,
        }
        self.numpy_type_mapping = {
            self.proto.DT_BOOL: bool,

            self.proto.DT_INT8: np.int8,
            self.proto.DT_INT16: np.int16,
            self.proto.DT_INT32: np.int32,
            self.proto.DT_INT64: np.int64,

            self.proto.DT_FLOAT16: np.float16,
            self.proto.DT_FLOAT32: np.float32,
            self.proto.DT_FLOAT64: np.float64,

            self.proto.DT_STRING: str
        }
        self.int_types = (
            self.proto.DT_INT8,
            self.proto.DT_INT16,
            self.proto.DT_INT32,
            self.proto.DT_INT64,
        )
        self.uint_types = (
            self.proto.DT_UINT8,
            self.proto.DT_UINT16,
            self.proto.DT_UINT32,
            self.proto.DT_UINT64,
        )
        self.float_types = (
            self.proto.DT_FLOAT16,
            self.proto.DT_FLOAT32,
            self.proto.DT_FLOAT64,
        )

    def _parse_constants(self, pb_constant):
        """
        Parse constants.

        Args:
            pb_constant (Protobuf): Constant node.
        """
        constant = Constant(pb_constant)
        if not pb_constant.HasField('value'):
            constant.output = NodeOutput(OutputType.TENSOR)
            self.constants.append(constant)
            return

        if pb_constant.value.dtype in self.int_types:
            constant.output = NodeOutput(OutputType(self.dtype_mapping[pb_constant.value.dtype]))
            constant.output.info['value'] = pb_constant.value.int_val
            constant.output.info['np_value'] = np.array(pb_constant.value.int_val,
                                                        dtype=self.numpy_type_mapping[pb_constant.value.dtype])
        elif pb_constant.value.dtype in self.float_types:
            constant.output = NodeOutput(OutputType(self.dtype_mapping[pb_constant.value.dtype]))
            constant.output.info['value'] = pb_constant.value.float_val
            constant.output.info['np_value'] = np.array(pb_constant.value.float_val,
                                                        dtype=self.numpy_type_mapping[pb_constant.value.dtype])
        elif pb_constant.value.dtype == self.proto.DT_BOOL:
            constant.output = NodeOutput(OutputType(self.dtype_mapping[pb_constant.value.dtype]))
            constant.output.info['value'] = pb_constant.value.bool_val
            constant.output.info['np_value'] = np.array(pb_constant.value.bool_val,
                                                        dtype=self.numpy_type_mapping[pb_constant.value.dtype])
        elif pb_constant.value.dtype == self.proto.DT_STRING:
            constant.output = NodeOutput(OutputType(self.dtype_mapping[pb_constant.value.dtype]))
            constant.output.info['value'] = pb_constant.value.str_val
            constant.output.info['np_value'] = np.array(pb_constant.value.str_val,
                                                        dtype=self.numpy_type_mapping[pb_constant.value.dtype])
        elif pb_constant.value.dtype == self.proto.DT_TENSOR:
            constant.output = NodeOutput(OutputType.TENSOR)
            if pb_constant.value.tensor_val.data_type:
                constant.output.info['dtype'] = self.dtype_mapping[pb_constant.value.tensor_val.data_type]
                constant.output.info['shape'] = tuple(pb_constant.value.tensor_val.dims)

            feature = Tensor.FEATURE(type='', id=constant.name, io='output')
            values = self.tensor_mapping.get(feature, [])
            if len(values) == 1:
                value = values[0]
                constant.output.info['tensor'] = Tensor(constant.name, 0, value.path)
        else:
            constant.output = NodeOutput(OutputType.NONE)

        self.constants.append(constant)

    def _parse_parameters(self, pb_parameter):
        """
        Parse parameters.

        Args:
            pb_parameter (Protobuf): Parameter node.
        """
        parameter = Parameter(pb_parameter)
        output = NodeOutput(OutputType.TENSOR)
        if pb_parameter.type.tensor_type.elem_type == self.proto.DT_UNDEFINED:
            output.type = OutputType.NONE
        else:
            output.info['dtype'] = self.dtype_mapping[pb_parameter.type.tensor_type.elem_type]
            output.info['shape'] = tuple([dim.size for dim in pb_parameter.type.tensor_type.shape.dim])

            feature = Tensor.FEATURE(type='', id=parameter.name, io='output')
            values = self.tensor_mapping.get(feature, [])
            if len(values) == 1:
                value = values[0]
                output.info['tensor'] = Tensor(parameter.name, 0, value.path)

        parameter.output = output
        self.parameters.append(parameter)

    def _get_proto_value(self, value):
        """
        Get proto value.

        Args:
            value (Protobuf): Protobuf value.

        Returns:
            any, proto value.

        Raises:
            UnknownDataTypeError: If data type of protobuf value can not be recognized.
        """
        if value.dtype == self.proto.DT_UNDEFINED:
            return None
        if value.dtype == self.proto.DT_TYPE:
            return self.dtype_mapping[value.type_val.data_type]
        if value.dtype == self.proto.DT_BOOL:
            return value.bool_val
        if value.dtype == self.proto.DT_STRING:
            return value.str_val
        if value.dtype in self.uint_types:
            return value.uint_val
        if value.dtype in self.int_types:
            return value.int_val
        if value.dtype in self.float_types:
            return value.float_val
        if value.dtype in (self.proto.DT_LIST, self.proto.DT_TUPLE):
            value_items = []
            for value_item in value.values:
                value_items.append(self._get_proto_value(value_item))
            if value.dtype == self.proto.DT_TUPLE:
                value_items = tuple(value_items)
            return value_items
        raise UnknownDataTypeError(value.dtype)

    def _find_operator_output_tensors(self, operator):
        """
        Find operator output tensors.

        Args:
            operator (Operator): Operator object.
        """
        output = operator.output
        if operator.type in ('tuple_getitem', 'make_tuple') or output.type in (OutputType.BOOL, OutputType.NONE):
            return

        is_load_op = False
        if operator.full_name.find('-op') == -1:
            is_load_op = True
            feature = Tensor.FEATURE(type='', id=operator.full_name, io='output')
        else:
            _, op_id = operator.full_name.split('-op')
            feature = Tensor.FEATURE(type=operator.type, id=op_id, io='output')

        values = self.tensor_mapping.get(feature)
        if not values:
            return

        if output.type == OutputType.TENSOR and len(values) == 1:
            value = values[0]
            if is_load_op:
                output.info['tensor'] = Tensor(operator.full_name, 0, value.path)
            else:
                output.info['tensor'] = Tensor(op_id, value.index, value.path)
        elif output.type == OutputType.TUPLE and len(values) == len(output.info['dtypes']):
            for value in values:
                output.info['tensors'][value.index] = Tensor(op_id, value.index, value.path)

    def _process_operator_input(self, operator, input_index, input_types):
        """
        Process operator input.

        Args:
            operator (Operator): Operator.
            input_index (int): Input index.
            input_types (dict): Input types.
        """
        op_input = operator.inputs[input_index]
        node = input_types[op_input.type].get(op_input.name)
        if not node:
            return
        node.downstream.append(operator.op_id)
        if op_input.type == InputType.OPERATOR:
            op_input.op_id = node.op_id

        op_input.info = {}

        if op_input.type in (InputType.PARAMETER, InputType.CONSTANT):
            op_input.info = node.output.info.copy() if node.output.info else None
            return

        if operator.type in ('tuple_getitem', 'TupleGetItem'):
            op_input.info['dtype'] = OutputType.TUPLE
            return

        if node.output.type == OutputType.TENSOR:
            op_input.info = node.output.info.copy()
        else:
            op_input.info['dtype'] = node.output.type

        if node.full_name.find('-op') == -1:
            op_id = node.full_name
            feature = Tensor.FEATURE(type='', id=node.full_name, io='output')
        else:
            _, op_id = node.full_name.split('-op')
            feature = Tensor.FEATURE(type=node.type, id=op_id, io='input')

        values = self.tensor_mapping.get(feature)
        if values and len(values) == len(operator.inputs) and op_input.info['tensor'] is None:
            value = values[input_index]
            op_input.info['tensor'] = Tensor(op_id, value.index, value.path)

    def _parse_operators(self, pb_operator):
        """
        Parse operator.

        Args:
            pb_operator (Protobuf): Operator node.

        Raises:
            UnknownDataTypeError: If data type of protobuf value can not be recognized.
        """
        if pb_operator.name == '':
            return

        operator = Operator(pb_operator)
        self.operators.append(operator)

        # parse source code
        if getattr(pb_operator, 'source_address', None):
            operator.stack = Source.build_stack_from_source_address(pb_operator.source_address)

        # parse attrs
        for attr in pb_operator.attribute:
            operator.attrs[attr.name] = self._get_proto_value(attr.value)
            if attr.name in ('input_names', 'output_names'):
                operator.attrs[attr.name] = list(operator.attrs[attr.name])

        self._parse_operator_inputs(operator, pb_operator)
        self._parse_operator_outputs(operator, pb_operator)
        self._find_operator_output_tensors(operator)

    def _parse_operator_outputs(self, operator, pb_operator):
        """Parse the outputs of the operator."""
        proto_output = pb_operator.output_type
        if proto_output.data_type in (self.proto.DT_UNDEFINED, self.proto.DT_NONE):
            output = NodeOutput(OutputType.NONE)
        elif proto_output.data_type == self.proto.DT_BOOL:
            output = NodeOutput(OutputType.BOOL)
        elif proto_output.data_type == self.proto.DT_TENSOR:
            output = NodeOutput(OutputType.TENSOR)
            output.info['dtype'] = self.dtype_mapping[proto_output.tensor_type.elem_type]
            if proto_output.tensor_type.shape:
                output.info['shape'] = tuple([dim.size for dim in proto_output.tensor_type.shape.dim])
        elif proto_output.data_type == self.proto.DT_TUPLE:
            output = NodeOutput(OutputType.TUPLE)
            for elem_type in proto_output.sequence_type.elem_types:
                dtype = self._get_tuple_item_dtype(elem_type)
                if dtype is None:
                    continue
                output.info['dtypes'].append(dtype)
                output.info['shapes'].append(None)
                output.info['tensors'].append(None)
                output.slot_size += 1
        else:
            raise UnknownDataTypeError(proto_output.data_type)
        operator.output = output

    def _parse_operator_inputs(self, operator, pb_operator):
        """Parse the inputs of the operator."""
        cst_mapping = dict((cst.name, cst) for cst in self.constants)
        param_mapping = dict((param.name, param) for param in self.parameters)
        op_mapping = dict((op.name, op) for op in self.operators)
        for pb_input in pb_operator.input:
            input_type = InputType.REFERENCE
            if pb_input.name in cst_mapping:
                input_type = InputType.CONSTANT
            elif pb_input.name in param_mapping:
                input_type = InputType.PARAMETER
            elif pb_input.name in op_mapping:
                input_type = InputType.OPERATOR

            op_input = NodeInput(input_type, pb_input.name)
            if input_type == InputType.OPERATOR:
                op_input.op_id = op_mapping[op_input.name].op_id

            operator.inputs.append(op_input)

    def _get_tuple_item_dtype(self, elem_type):
        """
        Get tuple item dtype.

        Args:
            elem_type (TypeProto) : TypeProto of tuple item operator.

        Returns:
            any, tuple item dtype.
        """
        if elem_type.tensor_type.elem_type != self.proto.DT_UNDEFINED:
            return self.dtype_mapping[elem_type.tensor_type.elem_type]

        return self.dtype_mapping[elem_type.data_type]

    def _get_tuple_getitem_index(self, operator, constant_mapping):
        """
        Get tuple_getitem index.

        Args:
            operator (Operator) : Operator.
            constant_mapping (dict) : Constant mapping.

        Returns:
            int, tuple_getitem index.

        Raises:
            TupleGetitemIndexError: If tuple_getitem index error occurs.
        """
        if operator.inputs[1].type == InputType.CONSTANT:
            constant = constant_mapping[operator.inputs[1].name]
            if constant.output.type in NodeOutput.SCALAR_TYPES:
                return int(constant.output.info['value'])
            raise TupleGetitemIndexError(operator.name, constant.name)

        if operator.inputs[1].type == InputType.SCALAR:
            return int(operator.inputs[1].name)
        raise TupleGetitemIndexError(operator.name, f'{operator.inputs[1].name}')

    def _process_tuple_operator(self, operator, operator_mapping, constant_mapping):
        """
        Process tuple operator.

        Args:
            operator (Operator): Tuple operator.
            operator_mapping (dict): Dict mapping of operators.
            constant_mapping (dict): Dict mapping of constants.
        """
        if operator.type in ('make_tuple', 'MakeTuple'):
            return

        if operator.type in ('tuple_getitem', 'TupleGetItem'):
            index = self._get_tuple_getitem_index(operator, constant_mapping)
            node = operator_mapping.get(operator.inputs[0].name)
            if node is None:
                return
            output = node.output
            if output.type == OutputType.TUPLE and len(output.info['tensors']) > index:
                operator.output.info['tensor'] = output.info['tensors'][index]

    def _process_transition_operator(self, operator, input_types):
        """
        Process transition operator.

        Args:
            operator (Operator): Transition operator.
            input_types (dict): Dict mapping of input types.
        """
        if operator.output.info['tensor'] is None:
            op_input = operator.inputs[0]
            if op_input.type in input_types:
                node = input_types[op_input.type][op_input.name]
                operator.output.info['tensor'] = node.output.info['tensor']

    def _post_process(self):
        """Post-process."""
        constant_mapping = dict((constant.name, constant) for constant in self.constants)
        parameter_mapping = dict((parameter.name, parameter) for parameter in self.parameters)
        operator_mapping = dict((operator.name, operator) for operator in self.operators)
        input_types = {
            InputType.CONSTANT: constant_mapping,
            InputType.PARAMETER: parameter_mapping,
            InputType.OPERATOR: operator_mapping,
        }

        tuple_operator_types = ('make_tuple', 'MakeTuple', 'tuple_getitem', 'TupleGetItem')
        transition_operator_types = ('Squeeze', 'Reshape', 'ExpandDims', 'Flatten')

        for operator in self.operators:
            if operator.type in tuple_operator_types:
                self._process_tuple_operator(operator, operator_mapping, constant_mapping)

            elif operator.type in transition_operator_types:
                self._process_transition_operator(operator, input_types)

            elif operator.type == 'Depend':
                if operator.output.type in (OutputType.NONE, OutputType.BOOL) \
                        or (operator.output.type == OutputType.TENSOR and operator.output.info['tensor'] is None):
                    op_input = operator.inputs[0]
                    if op_input.type == InputType.OPERATOR:
                        node = operator_mapping.get(op_input.name)
                        if node is None:
                            continue
                        operator.output = node.output

            elif operator.type == 'Assign' and len(operator.inputs) == 3:
                operator.inputs = operator.inputs[1:]

            for input_index, op_input in enumerate(operator.inputs):
                if op_input.type in input_types:
                    self._process_operator_input(operator, input_index, input_types)

    def parse(self):
        """Parse."""
        self.tensor_mapping = Tensor.scan_tensors(self.tensor_dir)

        # parse constants
        for pb_constant in self.graph_data.const_vals:
            self._parse_constants(pb_constant)

        # parse parameters:
        for pb_parameter in self.graph_data.parameters:
            self._parse_parameters(pb_parameter)

        # parse operators
        for pb_operator in self.graph_data.node:
            self._parse_operators(pb_operator)

        # post-process
        self._post_process()
