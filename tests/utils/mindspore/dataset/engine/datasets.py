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
"""Mock the MindSpore mindspore/dataset/engine/datasets.py."""


class Dataset:
    """Mock the MindSpore Dataset class."""

    def __init__(self, dataset_size=None, dataset_path=None):
        self.dataset_size = dataset_size
        self.dataset_path = dataset_path
        self.input = []

    def get_dataset_size(self):
        """Mocked get_dataset_size."""
        return self.dataset_size

    def get_batch_size(self):
        """Mocked get_batch_size"""
        return 32


class MindDataset(Dataset):
    """Mock the MindSpore MindDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(MindDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file
