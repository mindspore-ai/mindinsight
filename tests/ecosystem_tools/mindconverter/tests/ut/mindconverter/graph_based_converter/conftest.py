# Copyright 2020-2021 Huawei Technologies Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Constant definition in unit tests."""
import sys
import types

TEST_BASE_PATH = 'mindconverter.graph_based_converter'

sys.modules["torch"] = types.ModuleType("torch")
_C = types.ModuleType("torch._C")
sys.modules["torch._C"] = _C
_C.TensorType = type("TensorType", (object,), dict())
sys.modules["torch.onnx"] = types.ModuleType("torch.onnx")
jit = types.ModuleType("torch.jit")
sys.modules["torch.jit"] = jit
jit.TracingCheckError = type("TracingCheckError", (object,), dict())
