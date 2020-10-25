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
"""Parse summary file."""

import argparse
import os
import datetime

from mindinsight.utils.command import BaseCommand
from mindinsight.datavisual.data_transform.summary_parser.event_parser import EventParser


class FilepathAction(argparse.Action):
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
        summary_dir = values
        if summary_dir.startswith('~'):
            summary_dir = os.path.realpath(os.path.expanduser(summary_dir))

        if not summary_dir.startswith('/'):
            summary_dir = os.path.realpath(os.path.join(os.getcwd(), summary_dir))

        summary_dir = os.path.realpath(summary_dir)
        setattr(namespace, self.dest, summary_dir)


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
        output = values
        if output.startswith('~'):
            output = os.path.realpath(os.path.expanduser(output))

        if not output.startswith('/'):
            output = os.path.realpath(os.path.join(os.getcwd(), output))

        output = os.path.realpath(output)
        setattr(namespace, self.dest, output)


class Command(BaseCommand):
    """Start mindinsight service."""

    name = 'parse_summary'
    description = 'Parse summary file'

    def add_arguments(self, parser):
        """
        Add arguments to parser.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            '--summary-dir',
            type=str,
            action=FilepathAction,
            default=os.path.realpath(os.getcwd()),
            help="""
                    Optional, specify path for summary file directory. 
                    Default directory is the current working directory.
                """)

        parser.add_argument(
            '--output',
            type=str,
            action=OutputDirAction,
            default=os.path.realpath(os.getcwd()),
            help="""
                    Optional, specify path for converted file directory. Default output 
                    directory is `output` folder in the current working directory.
                """)

    def run(self, args):
        """
        Execute for start command.

        Args:
            args (Namespace): Parsed arguments to hold customized parameters.
        """
        date_time = datetime.datetime.now().strftime('output_%Y%m%d_%H%M%S_%f')
        date_time = os.path.join(args.output, date_time)
        eventparser = EventParser(args.summary_dir, date_time)
        eventparser.parse()
