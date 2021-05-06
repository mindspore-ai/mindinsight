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
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

        indices = self._convert_column_indices(column_metas)
        worksheet.write(1, indices.get('argument'), 'dump-dir', styles['content_center_fmt'])
        worksheet.write(1, indices.get('value'), self.dump_dir or '', styles['content_left_fmt'])

    def _get_operator_input_info(self, operator, input_types):
        """
        Add operator worksheet.

        Args:
            operator (Operator): Operator.
            input_types (dict): Input types.

        Returns:
            dict, input info content.
        """
        input_content = ''
        input_dtype_content = ''
        input_shape_content = ''

        for op_input in operator.inputs:
            if op_input.type == InputType.OPERATOR:
                op = input_types[InputType.OPERATOR][op_input.op_id]
                if op.type == 'Load':
                    input_content += f'{op.type}_{op.name}' + '\n'
                else:
                    input_content += f'{op.type}_{op.op_id}' + '\n'
                    if op_input.info:
                        input_dtype_content += str(op_input.info['dtype']) + '\n'
                        input_shape_content += str(op_input.info.get('shape') or Toolkit.PLACEHOLDER) + '\n'
                    else:
                        input_dtype_content += Toolkit.PLACEHOLDER + '\n'
                        input_shape_content += Toolkit.PLACEHOLDER + '\n'
            elif op_input.type == InputType.PARAMETER:
                input_content += op_input.name + '\n'
                param = input_types[InputType.PARAMETER][op_input.name]
                if param.output:
                    input_dtype_content += param.output.info['dtype'] + '\n'
                    input_shape_content += str(param.output.info.get('shape') or Toolkit.PLACEHOLDER) + '\n'
                else:
                    input_dtype_content += Toolkit.PLACEHOLDER + '\n'
                    input_shape_content += Toolkit.PLACEHOLDER + '\n'
            elif op_input.type == InputType.CONSTANT:
                input_content += op_input.name + '\n'
                cst = input_types[InputType.CONSTANT][op_input.name]
                if cst.output.type == OutputType.TENSOR:
                    input_dtype_content += cst.output.info.get('dtype') or Toolkit.PLACEHOLDER + '\n'
                    input_shape_content += str(cst.output.info.get('shape') or Toolkit.PLACEHOLDER) + '\n'
                else:
                    input_dtype_content += Toolkit.PLACEHOLDER + '\n'
                    input_shape_content += Toolkit.PLACEHOLDER + '\n'
            else:
                input_content += op_input.name + '\n'
                input_dtype_content += Toolkit.PLACEHOLDER + '\n'
                input_shape_content += Toolkit.PLACEHOLDER + '\n'

        return {
            'input': input_content.strip(),
            'input_dtype': input_dtype_content.strip(),
            'input_shape': input_shape_content.strip(),
        }

    def _add_operator_worksheet(self, workbook, styles):
        """
        Add operator worksheet.

        Args:
            workbook (WorkBook): Excel workbook.
            styles (dict): Workbook styles.
        """
        constant_mapping = dict((constant.name, constant) for constant in self.constants)
        parameter_mapping = dict((parameter.name, parameter) for parameter in self.parameters)
        operator_mapping = dict((operator.op_id, operator) for operator in self.operators)
        input_types = {
            InputType.CONSTANT: constant_mapping,
            InputType.PARAMETER: parameter_mapping,
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
            ('full_name', styles['header_left_fmt'], 20),
            ('device_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
            ('stack', styles['header_left_fmt'], 150),
        ]
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

        indices = self._convert_column_indices(column_metas)
        for index, operator in enumerate(self.operators):
            if operator.type == 'Load':
                operator_content = f'{operator.type}_{operator.name}'
            else:
                operator_content = f'{operator.type}_{operator.op_id}'

            worksheet.write(index + 1, indices.get('operator'), operator_content, styles['content_left_fmt'])

            if operator.type == 'make_tuple':
                worksheet.write(index + 1, indices.get('device_id'), operator.device_id, styles['content_left_fmt'])
                worksheet.write(index + 1, indices.get('graph_name'), operator.graph_name, styles['content_left_fmt'])
                continue

            input_info = self._get_operator_input_info(operator, input_types)
            worksheet.write(index + 1, indices.get('input'), input_info['input'], styles['content_wrapped_fmt'])
            worksheet.write(
                index + 1, indices.get('input_dtype'),
                input_info['input_dtype'], styles['content_wrapped_fmt'])
            worksheet.write(
                index + 1, indices.get('input_shape'),
                input_info['input_shape'], styles['content_wrapped_fmt'])

            output_dtype_content = ''
            output_shape_content = ''
            if operator.output and operator.output.type == OutputType.TENSOR:
                output_dtype_content = operator.output.info['dtype']
                output_shape_content = str(operator.output.info['shape'])
            elif operator.output and operator.output.type == OutputType.TUPLE:
                output_dtype_content = '\n'.join([
                    Toolkit.PLACEHOLDER if dtype is None else dtype
                    for dtype in operator.output.info['dtypes']
                ])
                output_shape_content = '\n'.join([
                    Toolkit.PLACEHOLDER if shape is None else str(shape)
                    for shape in operator.output.info['shapes']
                ])
            worksheet.write(
                index + 1, indices.get('output_dtype'),
                output_dtype_content, styles['content_wrapped_fmt'])
            worksheet.write(
                index + 1, indices.get('output_shape'),
                output_shape_content, styles['content_wrapped_fmt'])

            downstream_content = ''
            for op_id in operator.downstream:
                op = operator_mapping[op_id]
                downstream_content += f'{op.type}_{op.op_id}' + '\n'
            worksheet.write(
                index + 1, indices.get('downstream'),
                downstream_content.strip(), styles['content_wrapped_fmt'])

            worksheet.write(index + 1, indices.get('name'), operator.name, styles['content_center_fmt'])
            worksheet.write(index + 1, indices.get('attrs'), str(operator.attrs), styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('full_name'), operator.full_name, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('device_id'), operator.device_id, styles['content_left_fmt'])
            worksheet.write(index + 1, indices.get('graph_name'), operator.graph_name, styles['content_left_fmt'])

            stack_content = ''
            for source in operator.stack:
                stack_content += f'{source.file_path}:{source.line_no}\n{source.code_line}\n'
            worksheet.write(index + 1, indices.get('stack'), stack_content.strip(), styles['content_wrapped_fmt'])

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
            ('device_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

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
                if op.type == 'Load':
                    downstream_content += f'{op.type}_{op.name}' + '\n'
                else:
                    downstream_content += f'{op.type}_{op.op_id}' + '\n'
            worksheet.write(
                index + 1, indices.get('downstream'),
                downstream_content.strip(), styles['content_wrapped_fmt'])

            worksheet.write(index + 1, indices.get('device_id'), parameter.device_id, styles['content_left_fmt'])
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
            ('device_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

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

            worksheet.write(index + 1, indices.get('device_id'), constant.device_id, styles['content_left_fmt'])
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
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

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
            ('device_id', styles['header_left_fmt'], 20),
            ('graph_name', styles['header_left_fmt'], 30),
        ]
        for index, (column, fmt, width) in enumerate(column_metas):
            worksheet.set_column(index, index, width)
            worksheet.write(0, index, column, fmt)
        worksheet.autofilter(0, 0, 0, len(column_metas) - 1)

        source_mapping = {}
        for operator in self.operators:
            if not operator.stack:
                continue
            stack = [f'{source.file_path}:{source.line_no}\n{source.code_line}' for source in operator.stack]
            key = '\n'.join(stack)
            if key in source_mapping:
                source_mapping[key].append(operator)
            else:
                source_mapping[key] = [operator]

        row = 0
        indices = self._convert_column_indices(column_metas)
        for key in source_mapping:
            operators = source_mapping[key]
            operators.sort(key=lambda x: int(x.op_id))

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
                    row + index + 1, indices.get('device_id'),
                    operator.device_id, styles['content_left_fmt'])
                worksheet.write(
                    row + index + 1, indices.get('graph_name'),
                    operator.graph_name, styles['content_left_fmt'])

            row += len(operators)
