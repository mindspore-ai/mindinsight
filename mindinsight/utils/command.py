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

import sys
import os
import argparse
from importlib import import_module

import mindinsight
from mindinsight.utils.log import setup_logger
from mindinsight.utils.exceptions import MindInsightException


class BaseCommand:
    """Base command class."""

    name = ''
    description = ''

    # logger for console output instead of built-in print
    console = None

    # logger for log file recording in case audit is required
    logfile = None

    def add_arguments(self, parser):
        """
        Add arguments to parser.

        Args:
            parser (ArgumentParser): specify parser to which arguments are added.
        """

    def update_settings(self, args):
        """
        Update settings.

        Args:
            args (Namespace): parsed arguments to hold customized parameters.
        """

    def run(self, args):
        """
        Implementation of command logic.

        Args:
            args (Namespace): parsed arguments to hold customized parameters.
        """
        raise NotImplementedError('subclasses of BaseCommand must provide a run() method')

    def invoke(self, args):
        """
        Invocation of command.

        Args:
            args (Namespace): parsed arguments to hold customized parameters.
        """
        error = None
        try:
            self.update_settings(args)
        except MindInsightException as e:
            error = e

        self.console = setup_logger('mindinsight', 'console', console=True, logfile=False, formatter='%(message)s')
        if error is not None:
            self.console.error(error.message)
            sys.exit(1)

        self.logfile = setup_logger('scripts', self.name, console=False, logfile=True)
        self.run(args)


def main():
    """Entry point for mindinsight CLI."""

    console = setup_logger('mindinsight', 'console', console=True, logfile=False, formatter='%(message)s')
    if (sys.version_info.major, sys.version_info.minor) < (3, 7):
        console.error('Python version should be at least 3.7')
        sys.exit(1)

    permissions = os.R_OK | os.W_OK | os.X_OK

    # set umask to 0o077
    os.umask(permissions << 3 | permissions)

    parser = argparse.ArgumentParser(
                prog='mindinsight',
                description='MindInsight CLI entry point (version: {})'.format(mindinsight.__version__),
                allow_abbrev=False)

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ({})'.format(mindinsight.__version__))

    subparsers = parser.add_subparsers(
        dest='cli',
        title='subcommands',
        description='the following subcommands are supported',
    )

    commands = {}
    scripts_path = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, 'scripts'))
    files = os.listdir(scripts_path)
    files.sort()
    for file in files:
        if file.startswith('_') or not file.endswith('.py'):
            continue

        module = import_module('mindinsight.scripts.{}'.format(file[:-len('.py')]))
        command_cls = getattr(module, 'Command', None)
        if command_cls is None or not issubclass(command_cls, BaseCommand):
            continue

        command = command_cls()
        command_parser = subparsers.add_parser(command.name, help=command.description, allow_abbrev=False)
        command.add_arguments(command_parser)
        commands[command.name] = command

    argv = sys.argv[1:]
    if not argv or argv[0] == 'help':
        argv = ['-h']

    args = parser.parse_args(argv)
    cli = args.__dict__.pop('cli')
    command = commands[cli]
    command.invoke(args)
