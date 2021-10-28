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
        self.inputs = []

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


class ImageFolderDatasetV2(Dataset):
    """Mock the MindSpore ImageFolderDatasetV2 class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(ImageFolderDatasetV2, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class MnistDataset(Dataset):
    """Mock the MindSpore MnistDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(MnistDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class Cifar10Dataset(Dataset):
    """Mock the MindSpore Cifar10Dataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(Cifar10Dataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class Cifar100Dataset(Dataset):
    """Mock the MindSpore Cifar100Dataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(Cifar100Dataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class VOCDataset(Dataset):
    """Mock the MindSpore VOCDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(VOCDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class CelebADataset(Dataset):
    """Mock the MindSpore CelebADataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(CelebADataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class ManifestDataset(Dataset):
    """Mock the MindSpore ManifestDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(ManifestDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class TFRecordDataset(Dataset):
    """Mock the MindSpore TFRecordDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(TFRecordDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file


class TextFileDataset(Dataset):
    """Mock the MindSpore TextFileDataset class."""

    def __init__(self, dataset_size=None, dataset_file=None):
        super(TextFileDataset, self).__init__(dataset_size)
        self.dataset_file = dataset_file
