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
import argparse
import os
import sys

import mindinsight
from mindinsight.optimizer.tuner import Tuner


class ConfigAction(argparse.Action):
    """Summary base dir action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Option string for specific argument name.
        """
        config_path = os.path.realpath(values)
        if not os.path.exists(config_path):
            parser_in.error(f'{option_string} {config_path} not exists.')

        setattr(namespace, self.dest, config_path)


class IterAction(argparse.Action):
    """Summary base dir action class definition."""

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Option string for specific argument name.
        """
        iter_times = values
        if iter_times <= 0:
            parser_in.error(f'{option_string} {iter_times} should be a positive integer.')

        setattr(namespace, self.dest, iter_times)


parser = argparse.ArgumentParser(
        prog='mindoptimizer',
        description='MindOptimizer CLI entry point (version: {})'.format(mindinsight.__version__))

parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s ({})'.format(mindinsight.__version__))

parser.add_argument(
        '--config',
        type=str,
        action=ConfigAction,
        required=True,
        default=os.path.join(os.getcwd(), 'output'),
        help="Specify path for config file."
)

parser.add_argument(
        '--iter',
        type=int,
        action=IterAction,
        default=1,
        help="Optional, specify run times for the command in config file."
)


def cli_entry():
    """Cli entry."""
    argv = sys.argv[1:]
    if not argv:
        argv = ['-h']
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()

    tuner = Tuner(args.config)
    tuner.optimize(max_expr_times=args.iter)
