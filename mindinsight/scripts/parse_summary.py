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
from mindinsight.utils.exceptions import UnknownError
from mindinsight.datavisual.common.log import parse_summary_logger
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.ms_data_loader import _SummaryParser
from mindinsight.datavisual.data_transform.summary_parser.event_parser import EventParser


class DirAction(argparse.Action):
    """File directory action class definition."""

    @staticmethod
    def check_path(file_path):
        """
        Check argument for file path.

        Args:
            file_path (str): File path.
        """
        if file_path.startswith('~'):
            file_path = os.path.realpath(os.path.expanduser(file_path))

        if not file_path.startswith('/'):
            file_path = os.path.realpath(FileHandler.join(os.getcwd(), file_path))

        return os.path.realpath(file_path)

    def __call__(self, parser_in, namespace, values, option_string=None):
        """
        Inherited __call__ method from argparse.Action.

        Args:
            parser_in (ArgumentParser): Passed-in argument parser.
            namespace (Namespace): Namespace object to hold arguments.
            values (object): Argument values with type depending on argument definition.
            option_string (str): Optional string for specific argument name. Default: None.
        """
        summary_dir = self.check_path(values)

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
        output = DirAction.check_path(values)

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
            action=DirAction,
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
        Execute for parse_summary command.

        Args:
            args (Namespace): Parsed arguments to hold customized parameters.
        """
        try:
            date_time = datetime.datetime.now().strftime('output_%Y%m%d_%H%M%S_%f')
            output_path = os.path.join(args.output, date_time)

            summary_dir = args.summary_dir
            if not self._check_dirpath(summary_dir):
                return

            summary_parser = _SummaryParser(summary_dir)
            summary_files = summary_parser.filter_files(os.listdir(summary_dir))

            if not summary_files:
                parse_summary_logger.error('Path %s has no summary file.', summary_dir)
                return

            summary_files = summary_parser.sort_files(summary_files)
            filename = summary_files[-1]

            summary_file = FileHandler.join(summary_dir, filename)

            if not (self._check_filepath(summary_file) and self._check_create_filepath(output_path)
                    and self._check_create_filepath(FileHandler.join(output_path, 'image'))):
                return

            eventparser = EventParser(summary_file, output_path)
            eventparser.parse()

        except Exception as ex:
            parse_summary_logger.error("Parse summary file failed, detail: %r.", str(ex))
            raise UnknownError(str(ex))

    @staticmethod
    def _check_filepath(filepath):
        """
        Check file path existence, accessible and available

        Args:
            filepath (str): File path.
        """
        if not os.path.isfile(filepath):
            parse_summary_logger.error('Summary file %s is not a valid file.', filepath)
            return False
        if not os.access(filepath, os.R_OK):
            parse_summary_logger.error('Path %s is not accessible, please check the file-authority.', filepath)
            return False
        return True

    @staticmethod
    def _check_dirpath(filepath):
        """
        Check file path existence, accessible and available

        Args:
            filepath (str): File path.
        """
        if os.path.exists(filepath):
            if not os.path.isdir(filepath):
                parse_summary_logger.error('Summary directory %s is not a valid directory.', filepath)
                return False
            if not os.access(filepath, os.R_OK | os.X_OK):
                parse_summary_logger.error('Path %s is not accessible, please check the file-authority.', filepath)
                return False
            return True
        parse_summary_logger.error('Summary directory %s not exists.', filepath)
        return False

    @staticmethod
    def _check_create_filepath(filepath):
        """
        Check file path existence, accessible and available, if not exist create the file

        Args:
            filepath (str): File path.
        """
        permissions = os.R_OK | os.W_OK | os.X_OK
        os.umask(permissions << 3 | permissions)
        if os.path.exists(filepath):
            parse_summary_logger.error('Path %s has already existed, please choose a new output path.', filepath)
            return False
        mode = permissions << 6
        os.makedirs(filepath, mode=mode)
        return True
