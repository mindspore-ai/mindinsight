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
"""Defaults module for mindinsight settings."""
import os

####################################
# Global default settings.
####################################
WORKSPACE = os.path.join(os.environ['HOME'], 'mindinsight')

####################################
# Web default settings.
####################################
PORT = 8080
URL_PATH_PREFIX = ''

####################################
# Debugger default settings.
####################################
DEBUGGER_PORT = 50051
ENABLE_DEBUGGER = False
# The unit is MB
OFFLINE_DEBUGGER_MEM_LIMIT = 16 * 1024
MAX_OFFLINE_DEBUGGER_SESSION_NUM = 2

####################################
# Datavisual default settings.
####################################
RELOAD_INTERVAL = 3 # Seconds
SUMMARY_BASE_DIR = os.getcwd()

# set MAX_GRAPH_NODE_SIZE to 100000, which is able to support yolov4 with one card 11 graphs
# will increase the value after supporting to load graphs in parallel
MAX_GRAPH_NODE_SIZE = 100000
