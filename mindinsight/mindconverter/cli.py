# Copyright 2020 Huawei Technologies Co., Ltd
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


class FileDirAction(argparse.Action):
    """File directory action class definition."""

    @staticmethod
    def check_path(parser, values, option_string=None):
        """
        Check argument for file path.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        outfile = values
        if outfile.startswith('~'):
            outfile = os.path.realpath(os.path.expanduser(outfile))

        if not outfile.startswith('/'):
            outfile = os.path.realpath(os.path.join(os.getcwd(), outfile))

        if os.path.exists(outfile) and not os.access(outfile, os.R_OK):
            parser.error(f'{option_string} {outfile} not accessible')
        return outfile

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        outfile_dir = self.check_path(parser, values, option_string)
        if os.path.isfile(outfile_dir):
            parser.error(f'{option_string} {outfile_dir} is a file')

        setattr(namespace, self.dest, outfile_dir)


class OutputDirAction(argparse.Action):
    """File directory action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        output = values
        if output.startswith('~'):
            output = os.path.realpath(os.path.expanduser(output))

        if not output.startswith('/'):
            output = os.path.realpath(os.path.join(os.getcwd(), output))

        if os.path.exists(output):
            if not os.access(output, os.R_OK):
                parser.error(f'{option_string} {output} not accessible')

            if os.path.isfile(output):
                parser.error(f'{option_string} {output} is a file')

        setattr(namespace, self.dest, output)


class InFileAction(argparse.Action):
    """Input File action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        outfile_dir = FileDirAction.check_path(parser, values, option_string)
        if not os.path.exists(outfile_dir):
            parser.error(f'{option_string} {outfile_dir} not exists')

        if not os.path.isfile(outfile_dir):
            parser.error(f'{option_string} {outfile_dir} is not a file')

        setattr(namespace, self.dest, outfile_dir)


class LogFileAction(argparse.Action):
    """Log file action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from FileDirAction.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        outfile_dir = FileDirAction.check_path(parser, values, option_string)
        if os.path.exists(outfile_dir) and not os.path.isdir(outfile_dir):
            parser.error(f'{option_string} {outfile_dir} is not a directory')
        setattr(namespace, self.dest, outfile_dir)


def cli_entry():
    """Entry point for mindconverter CLI."""

    permissions = os.R_OK | os.W_OK | os.X_OK
    os.umask(permissions << 3 | permissions)

    parser = argparse.ArgumentParser(
        prog='mindconverter',
        description='MindConverter CLI entry point (version: {})'.format(mindinsight.__version__))

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ({})'.format(mindinsight.__version__))

    parser.add_argument(
        '--in_file',
        type=str,
        action=InFileAction,
        required=True,
        help="""
            Specify path for script file.
        """)

    parser.add_argument(
        '--output',
        type=str,
        action=OutputDirAction,
        default=os.path.join(os.getcwd(), 'output'),
        help="""
            Specify path for converted script file directory. 
            Default is output directory in the current working directory.
        """)

    parser.add_argument(
        '--report',
        type=str,
        action=LogFileAction,
        default=os.getcwd(),
        help="""
            Specify report directory. Default is the current working directory.
        """)

    argv = sys.argv[1:]
    if not argv:
        argv = ['-h']
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()
    mode = permissions << 6
    os.makedirs(args.output, mode=mode, exist_ok=True)
    os.makedirs(args.report, mode=mode, exist_ok=True)
    _run(args.in_file, args.output, args.report)


def _run(in_files, out_dir, report):
    """
    Run converter command.

    Args:
        in_files (str): The file path or directory to convert.
        out_dir (str): The output directory to save converted file.
        report (str): The report file path.
    """
    files_config = {
        'root_path': in_files if in_files else '',
        'in_files': [],
        'outfile_dir': out_dir,
        'report_dir': report
    }
    if os.path.isfile(in_files):
        files_config['root_path'] = os.path.dirname(in_files)
        files_config['in_files'] = [in_files]
    else:
        for root_dir, _, files in os.walk(in_files):
            for file in files:
                files_config['in_files'].append(os.path.join(root_dir, file))
    main(files_config)
