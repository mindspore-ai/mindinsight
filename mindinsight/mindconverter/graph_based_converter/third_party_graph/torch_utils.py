# Copyright 2020 Huawei Technologies Co., Ltd.All Rights Reserved.
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
"""Define pytorch tracer context manager."""
import importlib

from torch.nn import Module
from torch.onnx.utils import _trace
from torch.onnx.utils import _node_getitem
from torch.onnx.symbolic_helper import _set_opset_version


SCRIPT_METHOD = getattr(importlib.import_module("torch._C"),
                        "ScriptMethod")
onnx_tracer = _trace
getitem_of_node = _node_getitem
set_opset_version = _set_opset_version


def unique_state_dict(model):
    """
    Wrapper of torch.jit._unique_state_dict.

    Args:
        model (Module): Torch model.

    Returns:
        dict, params.
    """
    from torch.jit import _unique_state_dict

    return _unique_state_dict(model)


def create_autograd_variable(tensor):
    """
    Create autograd variable to trace the whole graph.

    Args:
        tensor (torch.Tensor): Tensor.

    Returns:
        torch.autograd.Variable, variable.
    """
    variable = getattr(importlib.import_module("torch.autograd"), "Variable")
    return variable(tensor, requires_grad=False)


class OverloadTorchModuleTemporarily:
    """
    Fix bugs in new version of pytorch.
    PyTorch official solution.
    """

    def __init__(self):
        self.backup = None

    def __enter__(self):
        def _tracing_name(traced_module, tracing_state):
            traced_module_stack = getattr(tracing_state, "_traced_module_stack")
            if not traced_module_stack:
                return None
            module = traced_module_stack[-1]
            for name, child in module.named_children():
                if child is traced_module:
                    return name
            return None

        def _slow_forward(self_, *inputs, **kwargs):
            tracing_state = getattr(importlib.import_module("torch._C"),
                                    "_get_tracing_state")()
            if not tracing_state or isinstance(self_.forward, SCRIPT_METHOD):
                return self_.forward(*inputs, **kwargs)
            if not hasattr(tracing_state, '_traced_module_stack'):
                tracing_state._traced_module_stack = []
            name = _tracing_name(self_, tracing_state)
            get_name_func = getattr(self_, "_get_name")
            if name:
                tracing_state.push_scope('%s[%s]' % (get_name_func(), name))
            else:
                tracing_state.push_scope(get_name_func())
            tracing_state._traced_module_stack.append(self_)
            try:
                result = self_.forward(*inputs, **kwargs)
            finally:
                tracing_state.pop_scope()
                tracing_state._traced_module_stack.pop()
            return result

        self.backup = getattr(Module, "_slow_forward")
        setattr(Module, '_slow_forward', _slow_forward)

    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(Module, '_slow_forward', self.backup)
