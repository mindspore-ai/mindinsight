# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Stop mindinsight service."""

import os
import sys
import argparse
import signal
import getpass

import psutil

from mindinsight.conf import settings
from mindinsight.utils.command import BaseCommand
from mindinsight.utils.hook import HookUtils


class PortAction(argparse.Action):
    """Port action class definition."""

    MIN_PORT = 1
    MAX_PORT = 65535

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


class Command(BaseCommand):
    """Stop command."""
    name = 'stop'
    description = 'stop mindinsight service'

    cmd_regex = 'mindinsight.backend.application:APP'
    access_log_path = os.path.join('gunicorn', 'access.log')

    def add_arguments(self, parser):
        """
        Add arguments to parser.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            '--port',
            type=int,
            action=PortAction,
            help="""
                Custom port ranging from %s to %s. Default value is %s
            """ % (PortAction.MIN_PORT, PortAction.MAX_PORT, settings.PORT))

    def update_settings(self, args):
        """
        Update settings.

        Args:
            args (Namespace): parsed arguments to hold customized parameters.
        """
        if args.port is None:
            args.port = settings.PORT

        pid, workspace = self.get_process(args.port)
        settings.config_workspace(workspace)
        setattr(args, 'pid', pid)

    def run(self, args):
        """
        Run to stop.

        Args:
            args (Namespace): Parsed arguments to hold customized parameters.
        """
        port, pid = args.port, args.pid
        if not pid:
            msg = f'No mindinsight service started by current user found for port {port}'
            self.console.error(msg)
            sys.exit(1)

        self.logfile.info('Stop mindinsight with port %s and pid %s.', port, pid)

        process = psutil.Process(pid)
        child_pids = [child.pid for child in process.children()]

        # kill gunicorn master process
        try:
            os.kill(pid, signal.SIGKILL)
        except PermissionError:
            self.console.info('kill pid %s failed due to permission error', pid)
            sys.exit(1)

        # cleanup gunicorn worker processes
        for child_pid in child_pids:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        for hook in HookUtils.instance().hooks():
            hook.on_shutdown(self.logfile)

        self.console.info('Stop mindinsight service successfully')

    def get_process(self, port):
        """
        Get mindinsight process

        Args:
            port (int): Specified port for mindinsight process.

        Returns:
            tuple, return mindinsight process pid and workspace.
        """
        pid, workspace = 0, settings.WORKSPACE
        user = getpass.getuser()
        connections = psutil.net_connections()
        for connection in connections:
            if connection.status != 'LISTEN':
                continue
            if connection.laddr.port != port:
                continue

            try:
                process = psutil.Process(connection.pid)
            except psutil.NoSuchProcess:
                continue

            cmds = process.cmdline()
            if ' '.join(cmds).find(self.cmd_regex) == -1:
                continue
            if user != process.username():
                continue

            pid = process.pid if process.ppid() == 1 else process.ppid()

            for open_file in process.open_files():
                if open_file.path.endswith(self.access_log_path):
                    log_base_dir = open_file.path[:-len(self.access_log_path)]
                    workspace = os.path.realpath(os.path.join(log_base_dir, os.pardir))
                    break
            break

        return pid, workspace
