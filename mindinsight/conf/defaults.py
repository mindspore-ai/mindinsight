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

####################################
# Datavisual default settings.
####################################
RELOAD_INTERVAL = 3 # Seconds
SUMMARY_BASE_DIR = os.getcwd()
