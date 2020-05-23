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
"""Loader struct."""
from mindinsight.datavisual.common.enums import CacheStatus


class LoaderStruct:
    """
    Loader to save summary info.

    LoaderStruct contains: loader_id, name, path, latest_update_time, status, data_loader.
    """
    def __init__(self, loader_id, name, path, latest_update_time, data_loader):
        self._loader_id = loader_id
        self._name = name
        self._path = path
        self._latest_update_time = latest_update_time
        self._data_loader = data_loader
        self._cache_status = CacheStatus.NOT_IN_CACHE

    @property
    def loader_id(self):
        """Get loader ID."""
        return self._loader_id

    @property
    def name(self):
        """Get loader name."""
        return self._name

    @property
    def latest_update_time(self):
        """Get the latest update time of loader."""
        return self._latest_update_time

    @property
    def data_loader(self):
        """Get data loader."""
        return self._data_loader

    @property
    def cache_status(self):
        """Get cache status of loader."""
        return self._cache_status

    @latest_update_time.setter
    def latest_update_time(self, latest_update_time):
        """Set the latest update time of loader."""
        self._latest_update_time = latest_update_time

    @cache_status.setter
    def cache_status(self, cache_status):
        """Set cache status of loader."""
        self._cache_status = cache_status

    def to_dict(self):
        """Transform LoaderStruct to dict."""
        return dict(
            loader_id=self._loader_id,
            name=self._name,
            path=self._path,
            latest_update_time=self._latest_update_time,
            data_loader=self._data_loader
        )
