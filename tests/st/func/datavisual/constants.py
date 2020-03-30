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
"""Constants for st."""
import tempfile

SUMMARY_BASE_DIR = tempfile.NamedTemporaryFile().name
SUMMARY_DIR_PREFIX = "summary"

SUMMARY_DIR_NUM_FIRST = 5
SUMMARY_DIR_NUM_SECOND = 11

RESERVOIR_DIR_NAME = "reservoir_dir"
RESERVOIR_TRAIN_ID = "./%s" % RESERVOIR_DIR_NAME
RESERVOIR_STEP_NUM = 15
RESERVOIR_DIR_NUM = 1

MULTIPLE_DIR_NAME = "multiple_dir"
MULTIPLE_TRAIN_ID = "./%s" % MULTIPLE_DIR_NAME
MULTIPLE_LOG_NUM = 3
MULTIPLE_DIR_NUM = 1

# Please make sure SUMMARY_DIR_NUM is greater than `MAX_DATA_LOADER_SIZE`.
# Mainly used to test caching.
SUMMARY_DIR_NUM = SUMMARY_DIR_NUM_FIRST\
                  + SUMMARY_DIR_NUM_SECOND\
                  + RESERVOIR_DIR_NUM\
                  + MULTIPLE_DIR_NUM
