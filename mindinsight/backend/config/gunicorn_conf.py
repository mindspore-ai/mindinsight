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
"""Config file for gunicorn."""

import os
import threading
from importlib import import_module

import gunicorn


gunicorn.SERVER_SOFTWARE = 'unknown'

worker_class = 'sync'
workers = 1
threads = min(30, os.cpu_count() * 2 + 1)
worker_connections = 1000

timeout = 30
graceful_timeout = 30
daemon = True

captureoutput = True

# write gunicorn default log to stream, and using mindinsight logger write gunicorn log to file.
accesslog = '-'


def on_starting(server):
    """Hook function on starting gunicorn process."""
    hook_module = import_module('mindinsight.utils.hook')
    for hook in hook_module.HookUtils.instance().hooks():
        threading.Thread(target=hook.on_startup, args=(server.log,)).start()
