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
"""Create project command module."""
import os
import re
import sys
import textwrap
from pathlib import Path

import click

from mindinsight.utils.command import BaseCommand
from mindinsight.wizard.base.utility import find_network_maker_names, load_network_maker, process_prompt_choice
from mindinsight.wizard.common.exceptions import CommandError
from mindinsight.wizard.conf.constants import SUPPORT_MINDSPORE_VERSION, QUESTION_START


class CreateProject(BaseCommand):
    """Create project class."""
    name = 'createproject'
    description = 'create project'

    def __init__(self):
        self._network_types = find_network_maker_names()

    def add_arguments(self, parser):
        """
        Add arguments to parser.

        Args:
            parser (ArgumentParser): Specify parser to which arguments are added.
        """
        parser.add_argument(
            'name',
            type=str,
            help='Specify the new project name.')

    def _make_project_dir(self, project_name):
        self._check_project_dir(project_name)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        project_dir = os.path.join(os.getcwd(), project_name)
        os.makedirs(project_dir, mode=mode, exist_ok=True)
        return project_dir

    @staticmethod
    def _check_project_dir(project_name):
        """Check project directory whether empty or exist."""
        if not re.search('^[A-Za-z0-9][A-Za-z0-9._-]*$', project_name):
            raise CommandError("'%s' is not a valid project name. Please input a valid name matching "
                               "regex ^[A-Za-z0-9][A-Za-z0-9._-]*$" % project_name)
        project_dir = os.path.join(os.getcwd(), project_name)
        if os.path.exists(project_dir):
            output_path = Path(project_dir)
            if output_path.is_dir():
                if os.path.os.listdir(project_dir):
                    raise CommandError('%s already exists, %s is not empty directory, please try another name.'
                                       % (project_name, project_dir))
            else:
                CommandError('There is a file in the current directory has the same name as the project %s, '
                             'please try another name.' % project_name)
        return True

    def ask_network(self):
        """Ask user question for selecting a network to create."""
        network_type_choices = self._network_types[:]
        network_type_choices.sort(reverse=False)
        prompt_msg = '{}:\n{}\n'.format(
            '%sPlease select a network' % QUESTION_START,
            '\n'.join(f'{idx: >4}: {choice}' for idx, choice in enumerate(network_type_choices, start=1))
        )
        prompt_type = click.IntRange(min=1, max=len(network_type_choices))
        choice = 0
        while not choice:
            choice = click.prompt(prompt_msg, default=0, type=prompt_type,
                                  hide_input=False, show_choices=False,
                                  confirmation_prompt=False, show_default=False,
                                  value_proc=lambda x: process_prompt_choice(x, prompt_type))
            if not choice:
                click.secho(textwrap.dedent("Network is required."), fg='red')

        click.secho(textwrap.dedent("Your choice is %s." % network_type_choices[choice - 1]), fg='yellow')
        return network_type_choices[choice - 1]

    @staticmethod
    def echo_notice():
        """Echo notice for depending environment."""
        click.secho(textwrap.dedent(
            "[NOTICE] The final generated scripts should be run under environment "
            "where mindspore==%s and related device drivers are installed. " % SUPPORT_MINDSPORE_VERSION), fg='yellow')

    def run(self, args):
        """Override run method to start."""
        project_name = args.get('name')
        try:
            self._check_project_dir(project_name)
        except CommandError as error:
            click.secho(error.message, fg='red')
            sys.exit(1)
        try:
            self.echo_notice()
            network_maker_name = self.ask_network()
            network_maker = load_network_maker(network_maker_name)
            network_maker.configure()
        except click.exceptions.Abort:
            sys.exit(1)

        project_dir = self._make_project_dir(project_name)
        source_files = network_maker.generate(**args)
        for source_file in source_files:
            source_file.write(project_dir)

        click.secho(f"{project_name} is generated in {project_dir}")
