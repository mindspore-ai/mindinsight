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
"""Trigger data manager load."""
import time

from mindinsight.conf import settings
from mindinsight.datavisual.common.log import logger
from mindinsight.datavisual.data_transform.data_manager import DATA_MANAGER
from mindinsight.lineagemgr.cache_item_updater import LineageCacheItemUpdater


def init_module(app):
    """
    Interface to init module.

    Args:
        app (Flask): An instance of Flask.

    """
    # Just to suppress pylint warning about unused arg.
    logger.debug("App: %s", type(app))
    DATA_MANAGER.register_brief_cache_item_updater(LineageCacheItemUpdater())
    # Let gunicorn load other modules first.
    time.sleep(1)

    DATA_MANAGER.start_load_data(reload_interval=settings.RELOAD_INTERVAL)
