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
"""Base module."""

import os
import re
import enum
import collections

import numpy as np

from mindinsight.domain.graph.exceptions import UnknownTensorError


class MindSporeType(enum.Enum):
    """MindSpore Type."""
    INT = 'int32'
    UINT = 'uint'
    FLOAT = 'float16'
    TENSOR = 'tensor'


class DeviceType(enum.Enum):
    """Device Type."""
    ASCEND = 'ascend'
    GPU = 'gpu'


class DumpType(enum.Enum):
    """Dump Type."""
    E2E = 'e2e'
    ASYNC = 'async'


class Tensor:
    """
    Tensor object of dump file.

    Args:
        op_id (str): Operator ID.
        index (int): Index of operator inputs/outputs.
        file_path (str): Absolute file path of tensor file.
    """

    FEATURE = collections.namedtuple('Feature', ['type', 'id', 'io'])
    VALUE = collections.namedtuple('Value', ['index', 'shape', 'dtype', 'path'])

    @classmethod
    def extract_shape_from_str(cls, shape_str):
        """
        Extract shape from tensor file.

        Args:
            shape_str (str): Shape string.

        Returns:
            tuple, shape of tensor file.
        """
        shape = tuple([int(dim.strip()) for dim in shape_str.strip('_').split('_')])
        # The shape info in dump file name is (0,) which is inconsistent with the actual tensor shape.
        # The shape needs to be converted to (1,).
        if shape == (0,):
            shape = (1,)
        return shape

    @classmethod
    def parse_tensor_file_name(cls, file_name):
        """
        Parse tensor file name.

        Args:
            file_name (str): Tensor file name.

        Returns:
            bool, indicating if node is operator.
            dict, tensor file info.

        Raises:
            UnknownTensorError: If tensor file name can not be recognized.
        """
        is_op = False
        is_npy = file_name.endswith('.npy')
        if re.search(r'-op\d+(_|(\.\d+\.\d+\.))(input|output)(_|\.)', file_name):
            is_op = True
            dump_type = DumpType.E2E
            if re.search(r'-op(?P<op_id>\d+)\.(?P<stream_id>\d+)\.(?P<task_id>\d+)', file_name):
                dump_type = DumpType.ASYNC

            if dump_type == DumpType.ASYNC:
                file_name = file_name[file_name.find('.')+1:]
                if is_npy:
                    regex = r'_(?P<op_name>[A-Za-z0-9]+)-op(?P<op_id>\d+)' \
                            r'\.(?P<stream_id>\d+)\.(?P<task_id>\d+)' \
                            r'\.(?P<io>input|output)' \
                            r'\.(?P<index>\d+)' \
                            r'\.npy$'
                else:
                    regex = r'_(?P<op_name>[A-Za-z0-9]+)-op(?P<op_id>\d+)' \
                            r'\.(?P<stream_id>\d+)\.(?P<task_id>\d+)' \
                            r'\.(?P<io>input|output)' \
                            r'\.(?P<index>\d+)' \
                            r'\.(?P<shape>[0-9\_]+)' \
                            r'\.(?P<dtype>bool|((uint|int|float)\d+))' \
                            r'\.(?P<format>[A-Za-z0-9\_]+)\.bin$'

            else:
                regex = r'--(?P<op_name>[A-Za-z0-9\_]+)-op(?P<op_id>\d+)' \
                        r'_(?P<io>input|output)' \
                        r'_(?P<index>\d+)' \
                        r'_shape_(?P<shape>[0-9\_]+)' \
                        r'_.*(?P<dtype>Bool|((UInt|Int|Float)\d+))' \
                        r'_(?P<format>[A-Za-z0-9\_]+)\.bin$'

        else:
            regex = r'^(?P<node_name>[A-Za-z0-9\.\_]+)' \
                    r'_(?P<io>input|output)' \
                    r'_(?P<index>\d+)' \
                    r'_shape_(?P<shape>[0-9\_]+)' \
                    r'_.*(?P<dtype>Bool|((UInt|Int|Float)\d+))' \
                    r'_(?P<format>[A-Za-z0-9\_]+)\.bin$'

        pattern = re.search(regex, file_name)
        if pattern is None:
            raise UnknownTensorError(is_op, file_name)

        info = pattern.groupdict()
        info['index'] = int(info['index'])
        info['shape'] = None if is_npy else cls.extract_shape_from_str(info['shape'])
        info['dtype'] = None if is_npy else info['dtype'].lower()
        return is_op, info

    @classmethod
    def scan_tensors(cls, tensor_dir):
        """
        Scan tensors.

        Args:
            tensor_dir (str): Directory path where holds the tensor files.
            check (lambda): Function to check tensor values.

        Returns:
            dict, tensor file mapping.
        """
        tensor_mapping = {}
        if not tensor_dir:
            return tensor_mapping

        file_names = os.listdir(tensor_dir)
        for file_name in file_names:
            full_path = os.path.join(tensor_dir, file_name)
            if not re.search(r'\.(bin|npy)$', file_name) or os.path.isdir(full_path):
                continue

            try:
                is_op, info = cls.parse_tensor_file_name(file_name)
            except UnknownTensorError:
                continue

            if is_op:
                feature = cls.FEATURE(type=info['op_name'], id=info['op_id'], io=info['io'])
            else:
                feature = cls.FEATURE(type='', id=info['node_name'], io=info['io'])

            value = cls.VALUE(index=info['index'], shape=info['shape'], dtype=info['dtype'], path=full_path)
            tensors = tensor_mapping.get(feature)
            if tensors:
                tensor_mapping[feature].append(value)
                tensor_mapping[feature].sort(key=lambda x: x[0])
            else:
                tensor_mapping[feature] = [value]

        return tensor_mapping

    def __init__(self, op_id, index, file_path):
        self.op_id = op_id
        self.index = index
        self.file_path = file_path

    def load(self):
        """
        Load tensor file.

        Returns:
            ndarray, tensor data.
        """
        if self.file_path.endswith('.npy'):
            tensor = np.load(self.file_path)
            return tensor

        metas = self.metas
        if metas is None:
            return None
        dtype = getattr(np, metas['dtype'])
        tensor = np.fromfile(self.file_path, dtype=dtype)
        try:
            tensor = tensor.reshape(metas['shape'])
        except ValueError:
            pass
        return tensor

    @property
    def metas(self):
        """
        Metas property.

        Returns:
            dict, metas extracted from tensor file name.
        """
        file_name = os.path.basename(self.file_path)
        try:
            is_op, info = self.parse_tensor_file_name(file_name)
        except UnknownTensorError:
            return None

        if is_op:
            info.pop('op_name')
            info.pop('op_id')
        else:
            info.pop('node_name')

        if file_name.endswith('.npy'):
            info.pop('dtype')
            info.pop('shape')

        return info

    @property
    def full_name(self):
        """
        Full name property.

        Returns:
            str, full name.
        """
        full_name_str, _ = os.path.basename(self.file_path).split('_output_')
        return full_name_str.replace('--', '/')

    @property
    def scope(self):
        """
        Scope property.

        Returns:
            str, scope.
        """
        return os.path.dirname(self.full_name)

    def __repr__(self):
        return str({
            'op_id': self.op_id,
            'index': self.index,
            'file_path': self.file_path,
        })


class NodeType(enum.Enum):
    """Node Type."""
    OPERATOR = 'operator'
    PARAMETER = 'parameter'
    CONSTANT = 'constant'


class InputType(enum.Enum):
    """Input Type."""
    OPERATOR = 'operator'
    PARAMETER = 'parameter'
    CONSTANT = 'constant'
    TENSOR = 'tensor'
    SCALAR = 'scalar'
    REFERENCE = 'reference'
    NONE = 'none'


class OutputType(enum.Enum):
    """Output Type."""
    NONE = 'none'
    BOOL = 'bool'
    INT8 = 'int8'
    INT16 = 'int16'
    INT32 = 'int32'
    INT64 = 'int64'
    UINT8 = 'uint8'
    UINT16 = 'uint16'
    UINT32 = 'uint32'
    UINT64 = 'uint64'
    FLOAT16 = 'float16'
    FLOAT32 = 'float32'
    FLOAT64 = 'float64'
    TENSOR = 'tensor'
    TUPLE = 'tuple'


class NodeInput:
    """
    Graph node input.

    Args:
        input_type (InputType): Input type.
        input_name (str): Input name.
    """

    def __init__(self, input_type, input_name):
        self.type = input_type
        self.name = input_name
        self.op_id = ''
        self.info = None

    def __repr__(self):
        return str({
            'type': self.type,
            'name': self.name,
            'op_id': self.op_id,
            'info': self.info,
        })


class NodeOutput:
    """
    Graph node output.

    Args:
        output_type (OutputType): Output type.
    """

    SCALAR_TYPES = (
        OutputType.INT8,
        OutputType.INT16,
        OutputType.INT32,
        OutputType.INT64,
        OutputType.UINT8,
        OutputType.UINT16,
        OutputType.UINT32,
        OutputType.UINT64,
        OutputType.FLOAT16,
        OutputType.FLOAT32,
    )

    def __init__(self, output_type):
        self.type = output_type
        if output_type == OutputType.NONE:
            self.info = None
        elif output_type == OutputType.BOOL:
            self.info = dict(value=None)
        elif output_type in self.SCALAR_TYPES:
            self.info = dict(value=None)
        elif output_type == OutputType.TENSOR:
            self.info = dict(dtype='', shape=(), tensor=None)
        elif output_type == OutputType.TUPLE:
            self.info = dict(dtypes=[], shapes=[], tensors=[])

    def __repr__(self):
        return str({
            'type': self.type,
            'info': self.info,
        })


class Source:
    """
    Source address info.

    Args:
        file_path (str): Absolute path of source file.
        line_no (int): Line number of code line in source file.
        code_line (int): Code line content.
    """

    def __init__(self, file_path, line_no, code_line):
        self.file_path = file_path
        self.line_no = line_no
        self.code_line = code_line

    def to_dict(self):
        """Parse to dict."""
        return {
            'file_path': self.file_path,
            'line_no': self.line_no,
            'code_line': self.code_line,
        }

    def __repr__(self):
        return str(self.to_dict())

    def __str__(self):
        return f'{self.file_path}:{self.line_no}\n{self.code_line}' if self.file_path else self.code_line

    @classmethod
    def build_stack_from_source_address(cls, source_address):
        """
        Build stack from source address.

        Args:
            source_address (str): Source address content.

        Returns:
            list, list of Source objects.
        """
        stack = []
        for line in source_address.strip().split('\n'):
            regex = r'#\sIn\sfile\s(?P<file_path>.+)\((?P<line_no>\d+)\)/(?P<code_line>.+)/'
            pattern = re.search(regex, line.strip())
            if pattern is None:
                source = {
                    'file_path': '',
                    'line_no': 0,
                    'code_line': line.strip(),
                }
            else:
                source = pattern.groupdict()
                source['line_no'] = int(source['line_no'])
                source['code_line'] = source['code_line'].strip()
            stack.append(cls(**source))

        return stack


class Node:
    """
    Graph node.

    Args:
        name (str): Node name.
    """

    def __init__(self, name):
        self.name = name
        self.output = None
        self.downstream = []
        self.raw = ''


class Constant(Node):
    """Constant node within graph."""

    def __repr__(self):
        return str({
            'name': self.name,
            'output': self.output,
            'downstream': self.downstream,
        })


class Parameter(Node):
    """Parameter node within graph."""

    def __repr__(self):
        return str({
            'name': self.name,
            'output': self.output,
            'downstream': self.downstream,
        })


class Operator(Node):
    """
    Operator node within graph.

    Args:
        op_name (str): Operator name.
        op_type (str): Operator type.
    """

    def __init__(self, op_name, op_type):
        super().__init__(op_name)
        self.type = op_type
        self.inputs = []
        self.attrs = {}
        self.full_name = ''
        self.stack = []

    @property
    def scope(self):
        """
        Scope property.

        Returns:
            str, scope.
        """
        return os.path.dirname(self.full_name)

    @property
    def op_id(self):
        """
        Op ID property.

        Returns:
            str, op ID.
        """
        pattern = re.search(r'-op(?P<op_id>\d+)$', self.full_name)
        if not pattern:
            return self.full_name

        info = pattern.groupdict()
        return info['op_id']

    def __repr__(self):
        return str({
            'name': self.name,
            'type': self.type,
            'inputs': self.inputs,
            'output': self.output,
            'downstream': self.downstream,
            'attrs': self.attrs,
            'full_name': self.full_name,
            'op_id': self.op_id,
        })


class Parser:
    """Graph file parser."""

    def __init__(self, graph_data=None, tensor_dir=''):
        self.graph_data = graph_data
        self.tensor_dir = os.path.realpath(tensor_dir) if tensor_dir else ''

        self.constants = []
        self.parameters = []
        self.operators = []
        self.tensor_mapping = {}

    def parse(self):
        """Parse."""
        raise NotImplementedError
