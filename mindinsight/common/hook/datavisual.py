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
"""Datavisual hook."""

import argparse
import os

from mindinsight.conf import settings
from mindinsight.utils.hook import BaseHook


class ReloadIntervalAction(argparse.Action):
    """Reload interval action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Option string for specific argument name.
        """
        reload_interval = values
        if reload_interval < 0 or reload_interval > settings.MAX_RELOAD_INTERVAL:
            parser.error(f'{option_string} should be greater than or equal to 0 or less than or equal to 300 ')
        setattr(namespace, self.dest, reload_interval)


class SummaryBaseDirAction(argparse.Action):
    """Summary base dir action class definition."""

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Option string for specific argument name.
        """
        summary_base_dir = os.path.realpath(values)
        setattr(namespace, self.dest, summary_base_dir)


class Hook(BaseHook):
    """Hook class definition."""

    def register_startup_arguments(self, parser):
        """
        Hook function to register startup arguments.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            '--reload-interval',
            type=int,
            action=ReloadIntervalAction,
            help="""
                data reload time(Seconds). It should be greater than 0 or equal to 0.
                If it equals 0, load data only once. Default value is %s seconds.
            """ % settings.RELOAD_INTERVAL)

        parser.add_argument(
            '--summary-base-dir',
            type=str,
            action=SummaryBaseDirAction,
            help="""
                directory where MindInsight will walk through its direct subdirectories
                and look for summary files naming with regex 'summary.\\d+' or '\\.pb$'. Any direct
                subdirectory containing summary files will turn out to be the summary
                file directory. Summary file existing in summary-base-dir indicates that
                sumamry-base-dir is one of the summary file directories as well. Default
                value is current directory.""")
