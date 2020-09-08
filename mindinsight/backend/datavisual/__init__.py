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
"""Datavisual."""

from mindinsight.backend.datavisual.static_resource_api import init_module as static_init_module
from mindinsight.backend.datavisual.task_manager_api import init_module as task_init_module
from mindinsight.backend.datavisual.train_visual_api import init_module as train_init_module


def init_module(app):
    """
    Interface to init module.

    Args:
        app (Flask): An instance of Flask.

    """
    static_init_module(app)
    task_init_module(app)
    train_init_module(app)
