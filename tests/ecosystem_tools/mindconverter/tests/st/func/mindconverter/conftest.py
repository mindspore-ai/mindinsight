# Copyright 2019-2021 Huawei Technologies Co., Ltd
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
"""The st config."""

import os
import shutil
import sys
import tempfile
import types

import pytest

OUTPUT_DIR = tempfile.mktemp(prefix='test_mindconverter_output_dir_')

sys.modules['torch'] = types.ModuleType('torch')
nn = types.ModuleType('torch.nn')
sys.modules['torch.nn'] = nn
nn.Module = type('Module', (object,), dict())
sys.modules['torch.nn.functional'] = types.ModuleType('torch.nn.functional')

_C = types.ModuleType("torch._C")
sys.modules["torch._C"] = _C
_C.TensorType = type("TensorType", (object,), dict())
sys.modules["torch.onnx"] = types.ModuleType("torch.onnx")
jit = types.ModuleType("torch.jit")
sys.modules["torch.jit"] = jit
jit.TracingCheckError = type("TracingCheckError", (object,), dict())


@pytest.fixture(scope='session')
def create_output_dir():
    """Create output directory."""
    try:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)
        permissions = os.R_OK | os.W_OK | os.X_OK
        mode = permissions << 6
        if not os.path.exists(OUTPUT_DIR):
            os.mkdir(OUTPUT_DIR, mode=mode)
        yield
    finally:
        if os.path.exists(OUTPUT_DIR):
            shutil.rmtree(OUTPUT_DIR)


@pytest.fixture()
def output():
    """Get the output directory."""
    return OUTPUT_DIR
