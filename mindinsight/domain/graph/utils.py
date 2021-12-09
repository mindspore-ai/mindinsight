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
"""Parse utils module."""

import os
import stat
from functools import cmp_to_key

import xlsxwriter

from mindinsight.domain.graph.base import InputType, OutputType


class Toolkit:
    """Toolkit."""

    PLACEHOLDER = '-'

    def __init__(self, dump_dir, constants, parameters, operators):
        self.dump_dir = dump_dir
        self.constants = constants
        self.parameters = parameters
        self.operators = operators

    def export_xlsx(self, file_path):
        """
        Export graph data to Excel file.

        Args:
            file_path (str) : Excel file path.
        """
        file_path = os.path.realpath(file_path)
        target_dir = os.path.dirname(file_path)
        if not os.path.isdir(target_dir):
            print(f'Directory {target_dir} not exists')
            return

        workbook = xlsxwriter.Workbook(file_path)

        # text_v_align: 1-top, 2-middle, 3-bottom
        # text_h_align: 1-left, 2-center, 3-right
        styles = dict(
            header_left_fmt=workbook.add_format(dict(
                text_v_align=2, text_h_align=1,
                font_color='#000000', bg_color='#d9d9d9',
                bold=True,
            )),
            header_center_fmt=workbook.add_format(dict(
                text_v_align=2, text_h_align=2,
                font_color='#000000', bg_color='#d9d9d9',
                bold=True,
            )),
            content_left_fmt=workbook.add_format(dict(
                text_v_align=2, text_h_align=1,
                text_wrap=False,
            )),
            content_center_fmt=workbook.add_format(dict(
                text_v_align=2, text_h_align=2,
                text_wrap=False,
            )),
            content_wrapped_fmt=workbook.add_format(dict(
                text_v_align=2, text_h_align=1,
                text_wrap=True,
            )),
        )

        self._add_info_worksheet(workbook, styles)
        self._add_constant_worksheet(workbook, styles)
        self._add_parameter_worksheet(workbook, styles)
        self._add_operator_worksheet(workbook, styles)
        self._add_statistics_worksheet(workbook, styles)
        self._add_source_worksheet(workbook, styles)

        for worksheet in workbook.sheetnames.values():
            worksheet.freeze_panes(1, 0)
            worksheet.freeze_panes(1, 1)

        workbook.close()
        os.chmod(file_path, stat.S_IRUSR)

    def _write_columns(self, worksheet, metas):
        """
        Write columns according to column metas.

        Args:
            worksheet (Workbook): Target worksheet.
            metas (list): Column metas.
        """
        for index, (column, fmt, width) in enumerate(metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(metas) - 1)

    def _convert_column_indices(self, metas):
        """
        Convert column metas into indices mapping.

        Args:
            metas (list): Column metas.

        Returns:
            dict, holds the indicess of columns.
        """
        mapping = {}
        for index, (name, _, _) in enumerate(metas):
            mapping[name] = index
        return mapping

    def _add_info_worksheet(self, workbook, styles):
        """
        Add info worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        worksheet = workbook.add_worksheet('info')

        # column metas contain column names, styles and widths
        column_metas = [
            ('argument', styles['header_center_fmt'], 20),
            ('value', styles['header_left_fmt'], 150),
        ]
        self._write_columns(worksheet, column_metas)

        indices = self._convert_column_indices(column_metas)
        worksheet.write(1, indices.get('argument'), 'dump-dir', styles['content_center_fmt'])
        worksheet.write(1, indices.get('value'), self.dump_dir or '', styles['content_left_fmt'])

    def _get_dtype_content(self, dtype):
        """
        Get dtype content.

        Args:
            dtype (Any): Tensor dtype.

        Returns:
            str, dtype content.
        """
        return Toolkit.PLACEHOLDER if dtype is None else str(dtype)

    def _get_shape_content(self, shape):
        """
        Get shape content.

        Args:
            shape (Any): Tensor shape.

        Returns:
            str, shape content.
        """
        return Toolkit.PLACEHOLDER if shape is None else str(shape)

    def _get_operator_input_content(self, operator, input_types):
        """
        Add operator input content.

        Args:
            operator (Operator): Operator.
            input_types (dict): Input types.

        Returns:
            tuple, input content, input dtype content and input shape content.
        """
        input_content = ''
        input_dtype_content = ''
        input_shape_content = ''

        for op_input in operator.inputs:
            if op_input.type == InputType.OPERATOR:
                op = input_types[InputType.OPERATOR][op_input.op_id]
                input_content += f'{op.type}_{op.name}' if op.type == 'Load' else f'{op.type}_{op.op_id}'
                if op_input.info:
                    input_dtype_content += self._get_dtype_content(op_input.info['dtype'])
                    input_shape_content += self._get_dtype_content(op_input.info.get('shape'))
                else:
                    input_dtype_content += Toolkit.PLACEHOLDER
                    input_shape_content += Toolkit.PLACEHOLDER
            elif op_input.type == InputType.PARAMETER:
                input_content += op_input.name
                param = input_types[InputType.PARAMETER][op_input.name]
                if param.output:
                    input_dtype_content += self._get_dtype_content(param.output.info['dtype'])
                    input_shape_content += self._get_shape_content(param.output.info.get('shape'))
                else:
                    input_dtype_content += Toolkit.PLACEHOLDER
                    input_shape_content += Toolkit.PLACEHOLDER
            elif op_input.type == InputType.CONSTANT:
                input_content += op_input.name
                cst = input_types[InputType.CONSTANT][op_input.name]
                if cst.output.type == OutputType.TENSOR:
                    input_dtype_content += self._get_dtype_content(cst.output.info.get('dtype'))
                    input_shape_content += self._get_shape_content(cst.output.info.get('shape'))
                else:
                    input_dtype_content += Toolkit.PLACEHOLDER
                    input_shape_content += Toolkit.PLACEHOLDER
            else:
                input_content += op_input.name
                input_dtype_content += Toolkit.PLACEHOLDER
                input_shape_content += Toolkit.PLACEHOLDER

            input_content += '\n'
            input_dtype_content += '\n'
            input_shape_content += '\n'

        return input_content.strip(), input_dtype_content.strip(), input_shape_content.strip()

    def _get_operator_type_content(self, operator):
        """
        Get operator downstream content.

        Args:
            operator (Operator): Operator.
            mapping (dict): Operator mapping.

        Returns:
            str, downstream content.
        """
        if operator.type == 'Load':
            return f'{operator.type}_{operator.name}'
        return f'{operator.type}_{operator.op_id}'

    def _get_operator_output_content(self, operator):
        """
        Get operator output content.

        Args:
            operator (Operator): Operator.

        Returns:
            tuple, output dtype content and output shape content.
        """
        output_dtype_content = ''
        output_shape_content = ''
        if operator.output:
            if operator.output.type == OutputType.TENSOR:
                output_dtype_content = operator.output.info['dtype']
                output_shape_content = str(operator.output.info['shape'])
            elif operator.output.type == OutputType.TUPLE:
                output_dtype_content = '\n'.join([
                    Toolkit.PLACEHOLDER if dtype is None else dtype
                    for dtype in operator.output.info['dtypes']
                ])
                output_shape_content = '\n'.join([
                    Toolkit.PLACEHOLDER if shape is None else str(shape)
                    for shape in operator.output.info['shapes']
                ])
        return output_dtype_content, output_shape_content

    def _get_operator_downstream_content(self, operator, mapping):
        """
        Get operator downstream content.

        Args:
            operator (Operator): Operator.
            mapping (dict): Operator mapping.

        Returns:
            str, downstream content.
        """
        content = ''
        for op_id in operator.downstream:
            op = mapping[op_id]
            content += f'{op.type}_{op.op_id}' + '\n'
        return content.strip()

    def _get_operator_stack_content(self, operator):
        """
        Get operator stack content.

        Args:
            operator (Operator): Operator.

        Returns:
            str, stack content.
        """
        content = '\n'.join([str(source) for source in operator.stack])
        return content.strip()

    def _add_operator_worksheet(self, workbook, styles):
        """
        Add operator worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        operator_mapping = dict((operator.op_id, operator) for operator in self.operators)
        input_types = {
            InputType.CONSTANT: dict((constant.name, constant) for constant in self.constants),
            InputType.PARAMETER: dict((parameter.name, parameter) for parameter in self.parameters),
            InputType.OPERATOR: operator_mapping,
        }

        worksheet = workbook.add_worksheet('operator')

        # column metas contain column names, styles and widths
        column_metas = [
            ('operator', styles['header_left_fmt'], 30),
            ('input', styles['header_left_fmt'], 30),
            ('input_dtype', styles['header_left_fmt'], 20),
            ('input_shape', styles['header_left_fmt'], 25),
            ('output_dtype', styles['header_left_fmt'], 20),
            ('output_shape', styles['header_left_fmt'], 25),
            ('downstream', styles['header_left_fmt'], 30),
            ('name', styles['header_center_fmt'], 10),
            ('attrs', styles['header_left_fmt'], 30),
            ('scope', styles['header_left_fmt'], 20),
            ('full_name', styles['header_left_fmt'], 20),
            ('rank_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
            ('stack', styles['header_left_fmt'], 150),
        ]
        self._write_columns(worksheet, column_metas)

        indices = self._convert_column_indices(column_metas)
        for index, operator in enumerate(self.operators):
            operator_type_content = self._get_operator_type_content(operator)
            worksheet.write(index + 1, indices.get('operator'), operator_type_content, styles['content_left_fmt'])

            if operator.type == 'make_tuple':
                worksheet.write(index + 1, indices.get('rank_id'), operator.rank_id, styles['content_left_fmt'])
                worksheet.write(index + 1, indices.get('graph_name'), operator.graph_name, styles['content_left_fmt'])
                continue

            input_content, input_dtype_content, input_shape_content = \
                self._get_operator_input_content(operator, input_types)
            worksheet.write(index + 1, indices.get('input'), input_content, styles['content_wrapped_fmt'])
            worksheet.write(index + 1, indices.get('input_dtype'), input_dtype_content, styles['content_wrapped_fmt'])
            worksheet.write(index + 1, indices.get('input_shape'), input_shape_content, styles['content_wrapped_fmt'])

            output_dtype_content, output_shape_content = self._get_operator_output_content(operator)
            worksheet.write(index + 1, indices.get('output_dtype'), output_dtype_content, styles['content_wrapped_fmt'])
            worksheet.write(index + 1, indices.get('output_shape'), output_shape_content, styles['content_wrapped_fmt'])

            downstream_content = self._get_operator_downstream_content(operator, operator_mapping)
            worksheet.write(index + 1, indices.get('downstream'), downstream_content, styles['content_wrapped_fmt'])

            worksheet.write(index + 1, indices.get('name'), operator.name, styles['content_center_fmt'])
            worksheet.write(index + 1, indices.get('attrs'), str(operator.attrs), styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('scope'), operator.scope, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('full_name'), operator.full_name, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('rank_id'), operator.rank_id, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('graph_name'), operator.graph_name, styles['content_left_fmt'])

            stack_content = self._get_operator_stack_content(operator)
            worksheet.write(index + 1, indices.get('stack'), stack_content, styles['content_wrapped_fmt'])

    def _add_parameter_worksheet(self, workbook, styles):
        """
        Add parameter worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        worksheet = workbook.add_worksheet('parameter')

        # column metas contain column names, styles and widths
        column_metas = [
            ('name', styles['header_left_fmt'], 50),
            ('output_dtype', styles['header_left_fmt'], 20),
            ('output_shape', styles['header_left_fmt'], 25),
            ('downstream', styles['header_left_fmt'], 30),
            ('rank_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        self._write_columns(worksheet, column_metas)

        indices = self._convert_column_indices(column_metas)
        operator_mapping = dict((operator.op_id, operator) for operator in self.operators)
        for index, parameter in enumerate(self.parameters):
            worksheet.write(index + 1, indices.get('name'), parameter.name, styles['content_left_fmt'])
            worksheet.write(
                index + 1, indices.get('output_dtype'),
                parameter.output.info['dtype'], styles['content_left_fmt'])
            worksheet.write(
                index + 1, indices.get('output_shape'),
                str(parameter.output.info['shape']), styles['content_left_fmt'])

            downstream_nodes = [operator_mapping[op_id] for op_id in parameter.downstream]
            downstream_content = ''
            for op in downstream_nodes:
                # Load is virtual operator for network parameters.
                # It is recommended to export its name rather than its op_id.
                if op.type == 'Load':
                    downstream_content += f'{op.type}_{op.name}' + '\n'
                else:
                    downstream_content += f'{op.type}_{op.op_id}' + '\n'
            worksheet.write(
                index + 1, indices.get('downstream'),
                downstream_content.strip(), styles['content_wrapped_fmt'])

            worksheet.write(index + 1, indices.get('rank_id'), parameter.rank_id, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('graph_name'), parameter.graph_name, styles['content_left_fmt'])

    def _add_constant_worksheet(self, workbook, styles):
        """
        Add constant worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        worksheet = workbook.add_worksheet('constant')

        # column metas contain column names, styles and widths
        column_metas = [
            ('name', styles['header_left_fmt'], 10),
            ('value', styles['header_left_fmt'], 30),
            ('downstream', styles['header_left_fmt'], 30),
            ('rank_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        self._write_columns(worksheet, column_metas)

        indices = self._convert_column_indices(column_metas)
        operator_mapping = dict((operator.op_id, operator) for operator in self.operators)
        for index, constant in enumerate(self.constants):
            worksheet.write(index + 1, indices.get('name'), constant.name, styles['content_left_fmt'])

            if constant.output.type == OutputType.NONE:
                value_content = 'NONE'
            elif constant.output.type == OutputType.TENSOR:
                value_content = 'TENSOR'
            else:
                value_content = constant.output.info['value']
            worksheet.write(index + 1, indices.get('value'), value_content, styles['content_left_fmt'])

            downstream_nodes = [operator_mapping[op_id] for op_id in constant.downstream]
            downstream_content = ''
            for op in downstream_nodes:
                if op.type == 'Load':
                    downstream_content += f'{op.type}_{op.name}' + '\n'
                else:
                    downstream_content += f'{op.type}_{op.op_id}' + '\n'
            worksheet.write(
                index + 1, indices.get('downstream'),
                downstream_content.strip(), styles['content_wrapped_fmt'])

            worksheet.write(index + 1, indices.get('rank_id'), constant.rank_id, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('graph_name'), constant.graph_name, styles['content_left_fmt'])

    def _add_statistics_worksheet(self, workbook, styles):
        """
        Add statistics worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        worksheet = workbook.add_worksheet('statistics')

        # column metas contain column names, styles and widths
        column_metas = [
            ('operator', styles['header_left_fmt'], 30),
            ('count', styles['header_center_fmt'], 20),
        ]
        self._write_columns(worksheet, column_metas)

        operator_type_set = set()
        for operator in self.operators:
            operator_type_set.add(operator.type)

        operator_types = sorted(list(operator_type_set))
        stats = dict(zip(operator_types, [0]*len(operator_types)))
        for operator in self.operators:
            stats[operator.type] += 1

        indices = self._convert_column_indices(column_metas)
        for index, operator_type in enumerate(operator_types):
            worksheet.write(index + 1, indices.get('operator'), operator_type, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('count'), stats[operator_type], styles['content_center_fmt'])

    def _add_source_worksheet(self, workbook, styles):
        """
        Add source worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        worksheet = workbook.add_worksheet('source')

        # column metas contain column names, styles and widths
        column_metas = [
            ('stack', styles['header_left_fmt'], 150),
            ('operator', styles['header_left_fmt'], 30),
            ('full_name', styles['header_left_fmt'], 20),
            ('rank_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        self._write_columns(worksheet, column_metas)

        source_mapping = {}
        for operator in self.operators:
            if not operator.stack:
                continue
            stack = [str(source) for source in operator.stack if source.file_path]
            key = '\n'.join(stack)
            if key in source_mapping:
                source_mapping[key].append(operator)
            else:
                source_mapping[key] = [operator]

        def compare_op(op1, op2):
            if op1.op_id.isdigit() and op2.op_id.isdigit():
                return int(op1.op_id) - int(op2.op_id)
            if op1.op_id < op2.op_id:
                return -1
            if op1.op_id > op2.op_id:
                return 1
            return 0

        row = 0
        indices = self._convert_column_indices(column_metas)
        for key in source_mapping:
            operators = source_mapping[key]
            operators.sort(key=cmp_to_key(compare_op))

            if len(operators) == 1:
                worksheet.write(row + 1, indices.get('stack'), key, styles['content_wrapped_fmt'])
            else:
                worksheet.merge_range(
                    row + 1, indices.get('stack'),
                    row+len(operators), 0, key, styles['content_wrapped_fmt'])

            for index, operator in enumerate(operators):
                operator_content = f'{operator.type}_{operator.op_id}'
                worksheet.write(
                    row + index + 1, indices.get('operator'),
                    operator_content, styles['content_left_fmt'])
                worksheet.write(
                    row + index + 1, indices.get('full_name'),
                    operator.full_name, styles['content_left_fmt'])
                worksheet.write(
                    row + index + 1, indices.get('rank_id'),
                    operator.rank_id, styles['content_left_fmt'])
                worksheet.write(
                    row + index + 1, indices.get('graph_name'),
                    operator.graph_name, styles['content_left_fmt'])

            row += len(operators)
