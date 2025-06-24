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
"""Start mindinsight service."""

import argparse
import os
import re
import sys
from importlib import import_module

import psutil

from mindinsight.conf import settings, get_web_address
from mindinsight.utils.command import BaseCommand
from mindinsight.utils.exceptions import PortNotAvailableError, SettingValueError
from mindinsight.modelarts.exceptions import PortReuseException
from mindinsight.utils.hook import HookUtils
from mindinsight.utils.hook import init

MIN_SESSION_NUM = 1
MAX_SESSION_NUM = 2
# The unit is MB
MIN_MEM_LIMIT_VALUE = 6 * 1024
# The limit for int32.
MAX_MEM_LIMIT_VALUE = 2147483647


class WorkspaceAction(argparse.Action):
    """Workspace action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        workspace = os.path.realpath(values)
        setattr(namespace, self.dest, workspace)


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


class UrlPathPrefixAction(argparse.Action):
    """Url Path prefix action class definition."""

    INVALID_SEGMENTS = ('.', '..')
    REGEX = r'^[a-zA-Z0-9_\-\.]+$'

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        prefix = values
        segments = prefix.split('/')
        for index, segment in enumerate(segments):
            if not segment and index in (0, len(segments) - 1):
                continue
            if segment in self.INVALID_SEGMENTS or not re.match(self.REGEX, segment):
                parser.error(f'{option_string} value is invalid url path prefix')

        setattr(namespace, self.dest, prefix)

class HostAction(argparse.Action):
    """Host action class definition."""

    LOCALHOST = '127.0.0.1'
    BIND_ALL = '0.0.0.0'
    
    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        def isIPv4(s):
            try:
                return str(int(s)) == s and 0 <= int(s) <= 255
            except: 
                return False
        def isIPv6(s):
            if len(s) > 4:
                return False
            try : 
                return int(s, 16) >= 0 and s[0] != '-'
            except:
                return False
        host = values
        validIPv4 = host.count(".") == 3 and all(isIPv4(i) for i in host.split("."))
        validIPv6 = host.count(":") == 7 and all(isIPv6(i) for i in host.split(":"))
        if (host != self.LOCALHOST or host != self.BIND_ALL) and not validIPv6 and not validIPv4:
            parser.error(f'{option_string} should be chosen between {self.LOCALHOST}, {self.BIND_ALL} and any other valid specific IPv6 or IPv4 address.')
        setattr(namespace, self.dest, host)
class Command(BaseCommand):
    """
    Start mindinsight service.
    """

    name = 'start'
    description = 'startup mindinsight service'

    def add_arguments(self, parser):
        """
        Add arguments to parser.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            '--workspace',
            type=str,
            action=WorkspaceAction,
            help="""
                Specify path for user workspace. Default is
                $HOME/mindinsight.
            """)

        parser.add_argument(
            '--port',
            type=int,
            action=PortAction,
            help="""
                Custom port ranging from %s to %s. Default value is %s.
            """ % (PortAction.MIN_PORT, PortAction.MAX_PORT, settings.PORT))
        
        parser.add_argument(
            '--host',
            type=str,
            action=HostAction,
            help="""
                Custom host to bind process to e.g. %s - %s or specific IP. Default value is %s.
            """ % (HostAction.LOCALHOST,HostAction.BIND_ALL, settings.HOST))
        
        parser.add_argument(
            '--url-path-prefix',
            type=str,
            action=UrlPathPrefixAction,
            help="""
                Custom URL path prefix for web page address. URL path prefix 
                consists of segments separated by slashes. Each segment supports
                alphabets / digits / underscores / dashes / dots, but not single 
                dot or double dots. Default value is ''.
            """)

        for hook in HookUtils.instance().hooks():
            hook.register_startup_arguments(parser)

    def update_settings(self, args):
        """
        Update settings.

        Args:
            args (Namespace): parsed arguments to hold customized parameters.
        """
        kwargs = {}
        for key, value in args.__dict__.items():
            if value is not None:
                kwargs[key] = value

        init(**kwargs)

    def run(self, args):
        """
        Execute for start command.

        Args:
            args (Namespace): Parsed arguments to hold customized parameters.
        """
        for key, value in args.__dict__.items():
            if value is not None:
                self.logfile.info('%s = %s', key, value)

        try:
            self.check_port()
        except (PortNotAvailableError, SettingValueError) as error:
            self.console.error(error.message)
            self.logfile.error(error.message)
            sys.exit(1)
        except PortReuseException as ex:
            self.console.error(ex.message)
            self.logfile.error(ex.message)
            sys.exit(2)

        self.console.info('Workspace: %s', os.path.realpath(settings.WORKSPACE))
        self.console.info('Summary base dir: %s', os.path.realpath(settings.SUMMARY_BASE_DIR))

        run_module = import_module('mindinsight.backend.run')
        state_result = run_module.start()

        self.logfile.info('Start mindinsight done. Workspace is %s,', settings.WORKSPACE)
        self.logfile.info('Port is %s,', settings.PORT)
        self.logfile.info('Summary base dir is %s', settings.SUMMARY_BASE_DIR)
        return state_result

    def check_port(self):
        """Check port."""
        if os.getuid() != 0 and settings.PORT < PortAction.OPEN_PORT_LIMIT:
            raise PortNotAvailableError(
                f'Port {settings.PORT} below {PortAction.OPEN_PORT_LIMIT} is not allowed by current user.')

        connections = psutil.net_connections()
        for connection in connections:
            if connection.status != 'LISTEN':
                continue
            if connection.laddr.port == settings.PORT:
                last_log_base_dir = self._get_log_base_dir(settings.PORT)
                web_address = get_web_address()
                if last_log_base_dir == settings.SUMMARY_BASE_DIR:
                    raise PortReuseException(
                        f'Reusing MindInsight on port {settings.PORT}. (pid {connection.pid}, ' \
                        f'Use "mindinsight stop --port {settings.PORT}" to stop it.)\n' \
                        f'{web_address}')
                raise PortNotAvailableError(
                    f'MindInsight could not bind to port {settings.PORT}, ' \
                    f'it was already in use (pid {connection.pid})')

    def _get_log_base_dir(self, port):
        """Get log base dir."""
        log_base_dir = ''
        log_path = os.path.join(settings.WORKSPACE, 'log/scripts/start.{}.log'.format(port))
        log_key_word = 'Summary base dir is '
        try:
            with open(log_path) as f:
                logs = f.readlines()
                for line in reversed(logs):
                    if log_key_word in line:
                        log_base_dir = line.split(log_key_word)[1].strip()
                        break
        except (FileNotFoundError, PermissionError) as error:
            log.info("Get log base dir error.")
            log.info(str(error))

        return log_base_dir
