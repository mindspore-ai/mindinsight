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
"""NetworkUtility module."""
from importlib import import_module


from mindinsight.wizard.common.exceptions import CommandError


def find_network_maker_names():
    return ['lenet', 'alexnet', 'resnet50']


def load_network_maker(network_name):
    module = import_module(f'mindinsight.wizard.network.{network_name.lower()}')
    return module.Network()


def load_dataset_maker(dataset_name, **kwargs):
    module = import_module(f'mindinsight.wizard.dataset.{dataset_name.lower()}')
    return module.Dataset(**kwargs)


def process_prompt_choice(value, prompt_type):
    """Convert command value to business value."""
    if value is not None:
        idx = prompt_type(value)
        return idx
    raise CommandError("The choice is not exist, please choice again.")
