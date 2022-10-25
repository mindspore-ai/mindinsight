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
import stat
import argparse
import time
from importlib import import_module

import mindinsight
from mindinsight.utils.log import setup_logger
from mindinsight.utils.exceptions import MindInsightException
from mindinsight._version import VERSION


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


def _mindspore_version_check():
    """
    Do the MindSpore version check for MindSpore Reinforcement. If the
    MindSpore can not be imported, it will give a warning. If its
    version is not compatibale with current MindSpore Reinforcement verision,
    it will print a warning.

    Raise:
        ImportError: If the MindSpore can not be imported.
    """
    console = setup_logger('mindinsight', 'console', console=True, logfile=False, formatter='%(message)s')

    mi_version_x = ".".join(VERSION.split(".")[:2]) + ".x"
    try:
        import mindspore as ms
    except (ImportError, ModuleNotFoundError):

        console.warning("[WARNING] Can not find MindSpore in current environment."
                        "You can install MindSpore, by following "
                        "the instruction at https://www.mindspore.cn/install. Note that "
                        "the summary data under the `summary-base-dir` should be from "
                        "MindSpore version == %s", mi_version_x)
        return

    ms_version_x = ".".join(ms.__version__.split(".")[:2]) + ".x"

    if mi_version_x != ms_version_x:
        console.warning("[WARNING] Current version of MindSpore is not compatible with MindInsight. "
                        "The summary data under the `summary-base-dir` should be from MindSpore which "
                        "the version equal to MindInsight`s . Otherwise some functions might not "
                        "work or even raise error. Please install MindSpore "
                        "version == %s, or install MindInsight version == %s.", mi_version_x, ms_version_x)

        warning_countdown = 3
        for i in range(warning_countdown, 0, -1):
            console.warning("[WARNING] Please pay attention to the above warning, countdonw: %d", i)
            time.sleep(1)


def main():
    """Entry point for mindinsight CLI."""

    console = setup_logger('mindinsight', 'console', console=True, logfile=False, formatter='%(message)s')
    if (sys.version_info.major, sys.version_info.minor) < (3, 7):
        console.error('Python version should be at least 3.7')
        sys.exit(1)

    _mindspore_version_check()

    # set umask to 0o077
    os.umask(stat.S_IRWXG | stat.S_IRWXO)

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
