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
from mindinsight.wizard.create_project import CreateProject


def cli_entry():
    """Entry point for mindwizard CLI."""

    permissions = os.R_OK | os.W_OK | os.X_OK
    os.umask(permissions << 3 | permissions)

    parser = argparse.ArgumentParser(
        prog='mindwizard',
        description='MindWizard CLI entry point (version: {})'.format(mindinsight.__version__))

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ({})'.format(mindinsight.__version__))
    command = CreateProject()
    command.add_arguments(parser)
    argv = sys.argv[1:]
    if not argv or argv[0] == 'help':
        argv = ['-h']

    args = parser.parse_args(argv)
    command.invoke(vars(args))


if __name__ == '__main__':
    cli_entry()
