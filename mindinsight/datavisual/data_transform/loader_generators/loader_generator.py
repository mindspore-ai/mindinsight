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
"""Base loader generator."""
from abc import abstractmethod

MAX_DATA_LOADER_SIZE = 15


class LoaderGenerator:
    """Base loader generator for loader generators."""
    @abstractmethod
    def generate_loaders(self, loader_pool):
        """
        Abstract method for generating loaders.

        Args:
            loader_pool (dict[str, LoaderStruct]): Current loader pool in data_manager.

        Returns:
            dict[str, LoaderStruct], a dict of `Loader`.

        """

    @abstractmethod
    def check_train_job_exist(self, train_id):
        """
        Abstract method for checking if train job exists.

        Args:
            train_id (str): Train ID.

        Returns:
            bool, if train job exists, return True.

        """

    @abstractmethod
    def generate_loader_by_train_id(self, train_id):
        """
        Abstract method for generating loader by train id.

        Args:
            train_id (str): Train ID.

        Returns:
            dict[str, LoaderStruct], a dict of `Loader`.

        """
