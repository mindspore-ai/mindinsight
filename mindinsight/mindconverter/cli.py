# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Command module."""
import os
import sys
import argparse

import mindinsight
from mindinsight.mindconverter.converter import main
from mindinsight.mindconverter.graph_based_converter.common.utils import get_framework_type
from mindinsight.mindconverter.graph_based_converter.constant import ARGUMENT_LENGTH_LIMIT, \
    ARGUMENT_NUM_LIMIT, ARGUMENT_LEN_LIMIT, FrameworkType
from mindinsight.mindconverter.graph_based_converter.framework import main_graph_base_converter

from mindinsight.mindconverter.common.log import logger as log, logger_console as log_console


class ArgsCheck:
    """Args check."""

    @staticmethod
    def check_repeated(namespace, dest, default, option_string, parser_in):
        """Check repeated."""
        if getattr(namespace, dest, default) is not default:
            parser_in.error(f'Parameter `{option_string}` is set repeatedly.')


class FileDirAction(argparse.Action):
    """File directory action class definition."""

    @staticmethod
    def check_path(parser_in, values, option_string=None):
        """
        Check argument for file path.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        outfile = values

        if len(outfile) > ARGUMENT_LENGTH_LIMIT:
            parser_in.error(
                f"The length of {option_string}{outfile} should be no more than {ARGUMENT_LENGTH_LIMIT}.")

        if outfile.startswith('~'):
            outfile = os.path.realpath(os.path.expanduser(outfile))

        if not outfile.startswith('/'):
            outfile = os.path.realpath(os.path.join(os.getcwd(), outfile))

        if os.path.exists(outfile) and not os.access(outfile, os.R_OK):
            parser_in.error(f'{option_string} {outfile} not accessible')
        return outfile

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        outfile_dir = self.check_path(parser_in, values, option_string)
        if os.path.isfile(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} is a file')

        setattr(namespace, self.dest, outfile_dir)


class OutputDirAction(argparse.Action):
    """File directory action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        output = values

        if len(output) > ARGUMENT_LENGTH_LIMIT:
            parser_in.error(
                f"The length of {option_string}{output} should be no more than {ARGUMENT_LENGTH_LIMIT}.")

        if output.startswith('~'):
            output = os.path.realpath(os.path.expanduser(output))

        if not output.startswith('/'):
            output = os.path.realpath(os.path.join(os.getcwd(), output))

        if os.path.exists(output):
            if not os.access(output, os.R_OK):
                parser_in.error(f'{option_string} {output} not accessible')

            if os.path.isfile(output):
                parser_in.error(f'{option_string} {output} is a file')

        setattr(namespace, self.dest, output)


class InFileAction(argparse.Action):
    """Input File action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        outfile_dir = FileDirAction.check_path(parser_in, values, option_string)
        if not os.path.exists(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} not exists')

        if not os.path.isfile(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} is not a file')

        if not os.path.basename(outfile_dir).endswith("py"):
            parser_in.error(f'{option_string} {outfile_dir} is not a valid python file')

        setattr(namespace, self.dest, outfile_dir)


class ModelFileAction(argparse.Action):
    """Model File action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        outfile_dir = FileDirAction.check_path(parser_in, values, option_string)
        if not os.path.exists(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} not exists')

        if not os.path.isfile(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} is not a file')

        frame_type = get_framework_type(outfile_dir)
        if frame_type == FrameworkType.UNKNOWN.value:
            parser_in.error(f'{option_string} {outfile_dir} should be '
                            f'a valid TensorFlow(.pb) or an ONNX(.onnx) model file.')

        setattr(namespace, self.dest, outfile_dir)


class LogFileAction(argparse.Action):
    """Log file action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from FileDirAction.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        outfile_dir = FileDirAction.check_path(parser_in, values, option_string)
        if os.path.exists(outfile_dir) and not os.path.isdir(outfile_dir):
            parser_in.error(f'{option_string} {outfile_dir} is not a directory')
        setattr(namespace, self.dest, outfile_dir)


class ShapeAction(argparse.Action):
    """Shape action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from FileDirAction.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (list): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)

        def _convert_to_int(shape_list):
            return [int(num_shape) for num_shape in shape_list.split(',')]

        try:
            if len(values) > ARGUMENT_NUM_LIMIT:
                parser_in.error(f"The length of {option_string} {values} should be no more than {ARGUMENT_NUM_LIMIT}.")
            in_shape = []
            for v in values:
                shape = _convert_to_int(v)
                if len(shape) > ARGUMENT_LEN_LIMIT:
                    parser_in.error(
                        f"The length of {option_string} {shape} should be no more than {ARGUMENT_LEN_LIMIT}.")
                in_shape.append(shape)
            setattr(namespace, self.dest, in_shape)
        except ValueError:
            parser_in.error(
                f"{option_string} {values} should be list of integers split by ',', check it please.")


class NodeAction(argparse.Action):
    """Node action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from FileDirAction.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (list): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """

        ArgsCheck.check_repeated(namespace, self.dest, self.default, option_string, parser_in)
        if len(values) > ARGUMENT_NUM_LIMIT:
            parser_in.error(f"The length of {option_string} {values} should be no more than {ARGUMENT_NUM_LIMIT}.")
        deduplicated = set()
        abnormal_nodes = []
        for v in values:
            if len(v) > ARGUMENT_LENGTH_LIMIT:
                parser_in.error(
                    f"The length of {option_string} {v} should be no more than {ARGUMENT_LENGTH_LIMIT}."
                )
            if v in deduplicated:
                abnormal_nodes.append(v)
                continue
            deduplicated.add(v)
        if abnormal_nodes:
            parser_in.error(f"{', '.join(abnormal_nodes)} {'is' if len(abnormal_nodes) == 1 else 'are'} duplicated.")
        setattr(namespace, self.dest, values)


parser = argparse.ArgumentParser(
    prog='mindconverter',
    description='MindConverter CLI entry point (version: {})'.format(mindinsight.__version__),
    allow_abbrev=False)

parser.add_argument(
    '--version',
    action='version',
    version='%(prog)s ({})'.format(mindinsight.__version__))

parser.add_argument(
    '--in_file',
    type=str,
    action=InFileAction,
    required=False,
    default=None,
    help="""
            Specify path for script file to use AST schema to 
            do script conversation.
        """)

parser.add_argument(
    '--model_file',
    type=str,
    action=ModelFileAction,
    required=False,
    help="""
            Tensorflow(.pb) or ONNX(.onnx) model file path 
            is expected to do script generation based on graph schema. When 
            `--in_file` and `--model_file` are both provided, 
            use AST schema as default.
        """)

parser.add_argument(
    '--shape',
    type=str,
    action=ShapeAction,
    default=None,
    required=False,
    nargs="+",
    help="""
            Optional, expected input tensor shape of
            `--model_file`. It is required when use graph based
            schema. Both order and number should be consistent with `--input_nodes`. 
            Usage: --shape 1,512 1,512
        """)

parser.add_argument(
    '--input_nodes',
    type=str,
    action=NodeAction,
    default=None,
    required=False,
    nargs="+",
    help="""
            Optional, input node(s) name of `--model_file`. It is required when use graph based schema. 
            Both order and number should be consistent with `--shape`. Usage: --input_nodes input_1:0 input_2:0
        """)

parser.add_argument(
    '--output_nodes',
    type=str,
    action=NodeAction,
    default=None,
    required=False,
    nargs="+",
    help="""
            Optional, output node(s) name of `--model_file`. It is required when use graph based schema. 
            Usage: --output_nodes output_1:0 output_2:0
        """)

parser.add_argument(
    '--output',
    type=str,
    action=OutputDirAction,
    default=os.path.join(os.getcwd(), 'output'),
    help="""
            Optional, specify path for converted script file 
            directory. Default output directory is `output` folder 
            in the current working directory.
        """)

parser.add_argument(
    '--report',
    type=str,
    action=LogFileAction,
    default=None,
    help="""
            Optional, specify report directory. Default is 
            converted script directory.
        """)


def cli_entry():
    """Entry point for mindconverter CLI."""

    permissions = os.R_OK | os.W_OK | os.X_OK
    os.umask(permissions << 3 | permissions)

    argv = sys.argv[1:]
    if not argv:
        argv = ['-h']
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()
    mode = permissions << 6
    os.makedirs(args.output, mode=mode, exist_ok=True)
    if args.report is None:
        args.report = args.output
    os.makedirs(args.report, mode=mode, exist_ok=True)
    _run(args.in_file, args.model_file,
         args.shape,
         args.input_nodes, args.output_nodes,
         args.output, args.report)


def _run(in_files, model_file, shape, input_nodes, output_nodes, out_dir, report):
    """
    Run converter command.

    Args:
        in_files (str): The file path or directory to convert.
        model_file(str): The model to convert on graph based schema.
        shape(list): The input tensor shape of module_file.
        input_nodes(str): The input node(s) name of model.
        output_nodes(str): The output node(s) name of model.
        out_dir (str): The output directory to save converted file.
        report (str): The report file path.
    """
    if in_files:
        files_config = {
            'root_path': in_files,
            'in_files': [],
            'outfile_dir': out_dir,
            'report_dir': report if report else out_dir
        }

        if os.path.isfile(in_files):
            files_config['root_path'] = os.path.dirname(in_files)
            files_config['in_files'] = [in_files]
        else:
            for root_dir, _, files in os.walk(in_files):
                for file in files:
                    files_config['in_files'].append(os.path.join(root_dir, file))
        main(files_config)
        log_console.info("MindConverter: conversion is completed.")

    elif model_file:
        file_config = {
            'model_file': model_file,
            'shape': shape if shape else [],
            'input_nodes': input_nodes,
            'output_nodes': output_nodes,
            'outfile_dir': out_dir,
            'report_dir': report if report else out_dir
        }

        main_graph_base_converter(file_config)
        log_console.info("MindConverter: conversion is completed.")
    else:
        error_msg = "`--in_file` and `--model_file` should be set at least one."
        error = FileNotFoundError(error_msg)
        log.error(str(error))
        log_console.error(f"mindconverter: error: {str(error)}")
        sys.exit(-1)
