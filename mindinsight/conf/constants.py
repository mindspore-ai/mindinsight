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
"""Constants module for mindinsight settings."""
import logging

####################################
# Global default settings.
####################################
LOG_FORMAT = '[%(levelname)s] MI(%(process)d:%(thread)d,%(processName)s):%(asctime)s ' \
             '[%(filepath)s:%(lineno)d][%(sub_module)s] %(message)s'

GUNICORN_ACCESS_FORMAT = "'%(h)s <%(r)s> %(s)s %(b)s <%(f)s> <%(a)s> %(D)s'"

LOG_LEVEL = logging.INFO
# rotating max bytes, default is 50M
LOG_ROTATING_MAXBYTES = 52428800

# rotating backup count, default is 30
LOG_ROTATING_BACKUPCOUNT = 30

####################################
# Web default settings.
####################################
HOST = '127.0.0.1'

# Allow to support cross origin resource sharing(CORS) enable. Default is disable.
# If enable CORS, `SUPPORT_REQUEST_METHODS` should enable 'OPTIONS' method.
ENABLE_CORS = False

SUPPORT_REQUEST_METHODS = {'POST', 'GET', 'PUT', 'DELETE'}

# url prefix should not end with slash, correct format is /v1/url
URL_PREFIX = '/v1/mindinsight'

####################################
# Datavisual default settings.
####################################
MAX_THREADS_COUNT = 15

MAX_TAG_SIZE_PER_EVENTS_DATA = 300
DEFAULT_STEP_SIZES_PER_TAG = 500

MAX_GRAPH_TAG_SIZE = 10
MAX_IMAGE_STEP_SIZE_PER_TAG = 10
MAX_SCALAR_STEP_SIZE_PER_TAG = 1000
MAX_GRAPH_STEP_SIZE_PER_TAG = 1
MAX_HISTOGRAM_STEP_SIZE_PER_TAG = 50
