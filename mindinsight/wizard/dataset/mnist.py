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
"""BaseDataset module."""
import os

from mindinsight.wizard.base.dataset import BaseDataset
from mindinsight.wizard.base.templates import TemplateManager
from mindinsight.wizard.conf.constants import TEMPLATES_BASE_DIR


class Dataset(BaseDataset):
    """BaseDataset code generator."""
    name = 'MNIST'

    def __init__(self):
        super(Dataset, self).__init__()
        self._network = None
        self.template_manager = None

    def set_network(self, network_maker):
        self._network = network_maker
        template_dir = os.path.join(TEMPLATES_BASE_DIR,
                                    'network',
                                    network_maker.name.lower(),
                                    'dataset',
                                    self.name.lower())
        self.template_manager = TemplateManager(template_dir)

    def configure(self):
        """Configure the network options."""
        return self.settings

    def generate(self, **options):
        source_files = self.template_manager.render(**options)
        return source_files
