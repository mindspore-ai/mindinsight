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
"""Module init file."""
from mindinsight.conf import settings
from mindinsight.backend.explainer.explainer_api import init_module as init_query_module
from mindinsight.explainer.manager.explain_manager import EXPLAIN_MANAGER


def init_module(app):
    """
    Init module entry.

    Args:
        app (Flask): A Flask instance.

    Returns:

    """
    init_query_module(app)
    EXPLAIN_MANAGER.start_load_data(reload_interval=settings.RELOAD_INTERVAL)
