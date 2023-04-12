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
"""Debugger hook."""

import argparse

from mindinsight.conf import settings
from mindinsight.utils.hook import BaseHook


def enable_debugger_string(string):
    """Convert str to bool"""
    if string.lower() in ('false', '0'):
        return False
    if string.lower() in ('true', '1'):
        return True
    raise ValueError


class EnableDebuggerAction(argparse.Action):
    """Enable debugger action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        enable_debugger = values
        setattr(namespace, self.dest, enable_debugger)


class PortAction(argparse.Action):
    """Port action class definition."""

    MIN_PORT = 1
    MAX_PORT = 65535

    OPEN_PORT_LIMIT = 1024

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        port = values
        if not self.MIN_PORT <= port <= self.MAX_PORT:
            parser.error(f'{option_string} should be chosen from {self.MIN_PORT} to {self.MAX_PORT}')

        setattr(namespace, self.dest, port)


class SessionNumAction(argparse.Action):
    """Session number action class definition."""

    MIN_NUM = 1
    MAX_NUM = 2

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        sesson_num = values
        if not self.MIN_NUM <= sesson_num <= self.MAX_NUM:
            parser.error(f'{option_string} should be chosen from {self.MIN_NUM} to {self.MAX_NUM}')

        setattr(namespace, self.dest, sesson_num)


class MemLimitAction(argparse.Action):
    """Memory limit action class definition."""

    # The unit is MB
    MIN_VALUE = 6 * 1024
    # The limit for int32.
    MAX_VALUE = 2147483647

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        mem_limit = values
        if not self.MIN_VALUE <= mem_limit <= self.MAX_VALUE:
            parser.error(f'{option_string} should be chosen from {self.MIN_VALUE} to {self.MAX_VALUE}')

        setattr(namespace, self.dest, mem_limit)


class MaxGraphNodeSizeAction(argparse.Action):
    """Graph Node limit action class definition."""
    MIN_VALUE = 1
    # The limit for 2000000.
    MAX_VALUE = 2000000

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        max_graph_node_size = values
        if not self.MIN_VALUE <= max_graph_node_size <= self.MAX_VALUE:
            parser.error(f'{option_string} should be chosen from {self.MIN_VALUE} to {self.MAX_VALUE}, default is '
                         f'{settings.MAX_GRAPH_NODE_SIZE}')
        setattr(namespace, self.dest, max_graph_node_size)


class Hook(BaseHook):
    """Hook class definition."""

    def register_startup_arguments(self, parser):
        """
        Hook function to register startup arguments.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            '--enable-debugger',
            type=enable_debugger_string,
            action=EnableDebuggerAction,
            default=False,
            help="""
                Enable debugger or not. The value can be True/False/1/0 (case insensitive).
                Default is False.""")

        parser.add_argument(
            '--debugger-port',
            type=int,
            action=PortAction,
            help="""
                Debugger port ranging from %s to %s. Default value is %s.
            """ % (PortAction.MIN_PORT, PortAction.MAX_PORT, settings.DEBUGGER_PORT))

        parser.add_argument(
            '--offline-debugger-mem-limit',
            type=int,
            action=MemLimitAction,
            help="""
                Offline debugger memory limit ranging from %s to %s MB. Default value is %s MB.
            """ % (MemLimitAction.MIN_VALUE, MemLimitAction.MAX_VALUE, settings.OFFLINE_DEBUGGER_MEM_LIMIT))

        parser.add_argument(
            '--max-offline-debugger-session-num',
            type=int,
            action=SessionNumAction,
            help="""
                Max offline debugger session number ranging from %s to %s. Default value is %s.
            """ % (SessionNumAction.MIN_NUM, SessionNumAction.MAX_NUM, settings.MAX_OFFLINE_DEBUGGER_SESSION_NUM))

        parser.add_argument(
            '--max-graph-node-size',
            type=int,
            action=MaxGraphNodeSizeAction,
            help="""
                Offline debugger graph node limit ranging from %s to %s MB. Default value is %s.
            """ % (MaxGraphNodeSizeAction.MIN_VALUE, MaxGraphNodeSizeAction.MAX_VALUE, settings.MAX_GRAPH_NODE_SIZE))
