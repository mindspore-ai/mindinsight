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
"""
Data Loader Generator.

This module generate loaders from summary logs.
"""
import os
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.common.exceptions import TrainJobNotExistError
from mindinsight.datavisual.data_access.file_handler import FileHandler
from mindinsight.datavisual.data_transform.data_loader import DataLoader
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import MAX_DATA_LOADER_SIZE
from mindinsight.datavisual.data_transform.loader_generators.loader_struct import LoaderStruct
from mindinsight.datavisual.data_transform.loader_generators.loader_generator import LoaderGenerator
from mindinsight.datavisual.data_transform.summary_watcher import SummaryWatcher
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.utils.exceptions import PathNotExistError


class DataLoaderGenerator(LoaderGenerator):
    """
    DataLoaderGenerator generate a loader_dict of loader from summary logs.

    Each loader helps deal the data of the events.
    It helps DataManager to generate loaders.
    """
    def __init__(self, summary_path):
        """
        Init DataLoaderGenerator.

        Args:
            summary_path (str): A directory path, e.g. '/data/ImageNet/'.
        """
        self._summary_path = self._check_and_normalize_summary_path(summary_path)
        self._summary_watcher = SummaryWatcher()

    def _check_and_normalize_summary_path(self, summary_path):
        """
        Check and normalize summary path.

        Args:
            summary_path (str): A directory path, e.g. '/data/ImageNet/'.

        Returns:
            str, normalized summary path.

        """
        if summary_path is None:
            logger.warning("Summary path is None. It will not init data loader generator.")
            raise ParamValueError("Summary path is None.")

        summary_path = os.path.realpath(summary_path)

        return summary_path

    def generate_loaders(self, loader_pool):
        """
        Generate loader from summary path, if summary path is empty, will return empty list.

        Args:
            loader_pool (dict[str, LoaderStruct]): Current loader pool in data_manager.

        Returns:
            dict[str, LoaderStruct], a dict of `Loader`.
        """
        loader_dict = {}

        if not FileHandler.exists(self._summary_path):
            logger.warning("Summary path does not exist. It will not start loading events data. "
                           "Current path is %r.", self._summary_path)
            return loader_dict

        dir_map_mtime_dict = {}
        min_modify_time = None
        summaries_info = self._summary_watcher.list_summary_directories(self._summary_path)

        for item in summaries_info:
            relative_path = item.get("relative_path")
            current_dir = FileHandler.join(self._summary_path, relative_path)
            dataloader = DataLoader(current_dir)

            if not dataloader.has_valid_files():
                logger.debug("Can not find valid train log file in folder %s , "
                             "will ignore.", relative_path)
                continue

            modify_time = item.get("update_time").timestamp()

            # if loader exists in loader pool and newer time, update its time
            loader_id = self._generate_loader_id(relative_path)
            loader = loader_pool.get(loader_id)
            if loader is not None and loader.latest_update_time > modify_time:
                modify_time = loader.latest_update_time

            if not min_modify_time:
                # The first load, init min modify time
                min_modify_time = modify_time

            # We need to find `MAX_DATA_LOADER_SIZE` newly modified folders.
            if len(dir_map_mtime_dict) < MAX_DATA_LOADER_SIZE:
                if modify_time < min_modify_time:
                    min_modify_time = modify_time
                dir_map_mtime_dict.update({relative_path: modify_time})

            else:
                if modify_time >= min_modify_time:
                    dir_map_mtime_dict.update({relative_path: modify_time})

        sorted_dir_tuple = sorted(dir_map_mtime_dict.items(),
                                  key=lambda d: d[1])[-MAX_DATA_LOADER_SIZE:]

        for relative_path, modify_time in sorted_dir_tuple:
            loader_id = self._generate_loader_id(relative_path)
            loader = self._generate_loader_by_relative_path(relative_path)
            loader_dict.update({loader_id: loader})

        return loader_dict

    def _generate_loader_by_relative_path(self, relative_path):
        """
        Generate loader by relative path.

        Args:
            relative_path (str): Relative path of a summary directory, e.g. './log1'.

        Returns:
            dict[str, LoaderStruct], a dict of `Loader`.
        """
        current_dir = os.path.realpath(FileHandler.join(self._summary_path, relative_path))
        data_loader = DataLoader(current_dir)
        loader_id = self._generate_loader_id(relative_path)
        loader = LoaderStruct(loader_id=loader_id,
                              name=self._generate_loader_name(relative_path),
                              path=current_dir,
                              latest_update_time=FileHandler.file_stat(current_dir).mtime,
                              data_loader=data_loader)
        return loader

    def _generate_loader_id(self, relative_path):
        """
        Generate loader id from relative path.

        Args:
            relative_path (str): Relative path of a summary directory, e.g. './log1'.

        Returns:
            str, loader_id for `Loader`.

        """
        loader_id = relative_path
        return loader_id

    def _generate_loader_name(self, relative_path):
        """
        Generate loader name from relative path.

        Args:
            relative_path (str): Relative path of a summary directory, e.g. './log1'.

        Returns:
            str, loader_name for `Loader`.

        """
        loader_name = relative_path
        return loader_name

    def _get_relative_path_from_train_id(self, train_id):
        """
        Get relative from train_id.

        Args:
            train_id (str): Train ID of a summary directory, e.g. './log1'.

        Returns:
            str, relative path of `Loader`.

        """
        relative_path = train_id

        return relative_path

    def check_train_job_exist(self, train_id):
        """
        Check if train job exists.

        Args:
            train_id (str): Train ID of a summary directory, e.g. './log1'.

        Returns:
            bool, if train job exists, return True.

        """
        if not self._is_train_id_valid(train_id):
            return False

        relative_path = self._get_relative_path_from_train_id(train_id)
        if self._summary_watcher.is_summary_directory(self._summary_path, relative_path):
            return True

        return False

    def _is_train_id_valid(self, train_id):
        """
        Check if train_id is valid.

        Args:
            train_id (str): Train ID of a summary directory, e.g. './log1'.

        Returns:
            bool, if train id is valid, return True.

        """
        if not train_id.startswith('./'):
            logger.warning("The train_id does not start with './'.")
            return False
        if len(train_id.split("/")) > 2:
            logger.warning("The train_id contains multiple '/'.")
            return False
        return True

    def generate_loader_by_train_id(self, train_id):
        """
        Generate loader by train_id.

        Args:
            train_id (str): Train ID of a summary directory, e.g. './log1'.

        Returns:
            dict[str, LoaderStruct], a dict of `Loader`.

        """
        relative_path = self._get_relative_path_from_train_id(train_id)
        try:
            loader = self._generate_loader_by_relative_path(relative_path)
        except PathNotExistError as ex:
            raise TrainJobNotExistError(str(ex))

        return loader
