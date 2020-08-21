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
"""GenericNetwork module."""
import os
import textwrap

import click

from mindinsight.wizard.base.network import BaseNetwork
from mindinsight.wizard.base.templates import TemplateManager
from mindinsight.wizard.base.utility import process_prompt_choice, load_dataset_maker
from mindinsight.wizard.conf.constants import TEMPLATES_BASE_DIR
from mindinsight.wizard.conf.constants import QUESTION_START


class GenericNetwork(BaseNetwork):
    """BaseNetwork code generator."""
    name = 'GenericNetwork'
    supported_datasets = []
    supported_loss_functions = []
    supported_optimizers = []

    def __init__(self):
        self._dataset_maker = None
        template_dir = os.path.join(TEMPLATES_BASE_DIR, 'network', self.name.lower())
        self.network_template_manager = TemplateManager(os.path.join(template_dir, 'src'))
        self.common_template_manager = TemplateManager(template_dir, ['src', 'dataset'])

    def configure(self, settings=None):
        """
        Configure the network options.

        If settings is not None, then use the input settings to configure the network.

        Args:
            settings (dict): Settings to configure, format is {'options': value}.
                Example:
                    {
                        "loss": "SoftmaxCrossEntropyWithLogits",
                        "optimizer": "Momentum",
                        "dataset": "Cifar10"
                    }

        Returns:
            dict, configuration value to network.
        """
        if settings:
            config = dict(settings)
            dataset_name = settings['dataset']
            self._dataset_maker = load_dataset_maker(dataset_name)
        else:
            loss = self.ask_loss_function()
            optimizer = self.ask_optimizer()
            dataset_name = self.ask_dataset()
            self._dataset_maker = load_dataset_maker(dataset_name)
            dataset_config = self._dataset_maker.configure()

            config = {'loss': loss,
                      'optimizer': optimizer,
                      'dataset': dataset_name}
            config.update(dataset_config)
        self._dataset_maker.set_network(self)
        self.settings.update(config)
        return config

    @staticmethod
    def ask_choice(prompt_head, content_list, default_value=None):
        """Ask user to get selected result."""
        if default_value is None:
            default_choice = 1  # start from 1 in prompt message.
            default_value = content_list[default_choice - 1]

        choice_contents = content_list[:]
        choice_contents.sort(reverse=False)
        default_choice = choice_contents.index(default_value) + 1  # start from 1 in prompt message.

        prompt_msg = '{}:\n{}\n'.format(
            prompt_head,
            '\n'.join(f'{idx: >4}: {choice}' for idx, choice in enumerate(choice_contents, start=1))
        )
        prompt_type = click.IntRange(min=1, max=len(choice_contents))
        choice = click.prompt(prompt_msg, type=prompt_type, hide_input=False, show_choices=False,
                              confirmation_prompt=False, default=default_choice,
                              value_proc=lambda x: process_prompt_choice(x, prompt_type))
        click.secho(textwrap.dedent("Your choice is %s." % choice_contents[choice - 1]), fg='yellow')
        return choice_contents[choice - 1]

    def ask_loss_function(self):
        """Select loss function by user."""
        return self.ask_choice('%sPlease select a loss function' % QUESTION_START, self.supported_loss_functions)

    def ask_optimizer(self):
        """Select optimizer by user."""
        return self.ask_choice('%sPlease select an optimizer' % QUESTION_START, self.supported_optimizers)

    def ask_dataset(self):
        """Select dataset by user."""
        return self.ask_choice('%sPlease select a dataset' % QUESTION_START, self.supported_datasets)

    def generate(self, **options):
        """Generate network definition scripts."""
        context = self.get_generate_context(**options)
        network_source_files = self.network_template_manager.render(**context)
        for source_file in network_source_files:
            source_file.file_relative_path = os.path.join('src', source_file.file_relative_path)
        dataset_source_files = self._dataset_maker.generate(**options)
        for source_file in dataset_source_files:
            source_file.file_relative_path = os.path.join('src', source_file.file_relative_path)

        assemble_files = self._assemble(**options)
        source_files = network_source_files + dataset_source_files + assemble_files
        return source_files

    def get_generate_context(self, **options):
        """Get detailed info based on settings to network files."""
        context = dict(options)
        context.update(self.settings)
        return context

    def get_assemble_context(self, **options):
        """Get detailed info based on settings to assemble files."""
        context = dict(options)
        context.update(self.settings)
        return context

    def _assemble(self, **options):
        # generate train.py & eval.py & assemble scripts.
        assemble_files = []
        context = self.get_assemble_context(**options)
        common_source_files = self.common_template_manager.render(**context)
        assemble_files.extend(common_source_files)
        return assemble_files
