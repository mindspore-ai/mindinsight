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
"""Mock the MindSpore mindspore/train/callback.py."""
import os


class RunContext:
    """Mock the RunContext class."""

    def __init__(self, original_args=None):
        self._original_args = original_args
        self._stop_requested = False

    def original_args(self):
        """Mock original_args."""
        return self._original_args

    def stop_requested(self):
        """Mock stop_requested method."""
        return self._stop_requested


class Callback:
    """Mock the Callback class."""

    def __init__(self):
        pass

    def begin(self, run_context):
        """Called once before network training."""

    def epoch_begin(self, run_context):
        """Called before each epoch begin."""


class _ListCallback(Callback):
    """Mock the _ListCallabck class."""

    def __init__(self, callbacks):
        super(_ListCallback, self).__init__()
        self._callbacks = callbacks


class ModelCheckpoint(Callback):
    """Mock the ModelCheckpoint class."""

    def __init__(self, prefix='CKP', directory=None, config=None):
        super(ModelCheckpoint, self).__init__()
        self._prefix = prefix
        self._directory = directory
        self._config = config
        self._latest_ckpt_file_name = os.path.join(directory, prefix + 'test_model.ckpt')

    @property
    def model_file_name(self):
        """Get the file name of model."""
        return self._model_file_name

    @property
    def latest_ckpt_file_name(self):
        """Get the latest file name fo checkpoint."""
        return self._latest_ckpt_file_name


class SummaryStep(Callback):
    """Mock the SummaryStep class."""

    def __init__(self, summary, flush_step=10):
        super(SummaryStep, self).__init__()
        self._sumamry = summary
        self._flush_step = flush_step
        self.summary_file_name = summary.full_file_name
