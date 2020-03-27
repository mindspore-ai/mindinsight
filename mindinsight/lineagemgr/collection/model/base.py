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
"""Metadata of lineage collection."""


class Metadata:
    """Initialize parameters used in model lineage management."""
    train_dataset_path = 'train_dataset_path'
    valid_dataset_path = 'valid_dataset_path'
    train_network = 'train_network'
    loss_function = 'loss_function'
    loss = 'loss'
    optimizer = 'optimizer'
    learning_rate = 'learning_rate'
    epoch = 'epoch'
    step_num = 'step_num'
    parallel_mode = 'parallel_mode'
    device_num = 'device_num'
    batch_size = 'batch_size'
    model_path = 'model_path'
    model_ckpt = 'model_ckpt'
    model_size = 'model_size'
    metrics = 'metrics'
    train_dataset_size = 'train_dataset_size'
    valid_dataset_size = 'valid_dataset_size'
