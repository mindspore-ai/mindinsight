# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Modelarts notebook Registry."""

class Registry:
    """
    Registry to map strings to classes.

    Args:
        name (str): Registry name.
    """

    def __init__(self, name):
        self.name = name
        self._modules = dict()

    @property
    def modules(self):
        return self._modules

    def get(self, key):
        return self._modules.get(key, None)

    def _register_module(self, module, name=None, force=False):
        """
        Register a module.
        """
        if not isinstance(module, type):
            raise ValueError(f'Not supported type: {type(module)} [type]')

        if name is None:
            name = module.__name__
        if not isinstance(name, str):
            raise ValueError(f'Not supported type: {type(name)} [str]')

        if not (force or name not in self._modules):
            raise ValueError(f'Name({name}) is already registered in registry({self.name})')

        self._modules[name] = module

    def register_module(self, name=None, force=False, module=None):
        """
        Register a module.

        Args:
            name (str): The name to be registered. If `None`, the module name
                will be used.
            force (bool): Whether to override an existing module with the same
                name. Default: False.
            module (type): Module to be registered.
        """
        if module is not None:
            self._register_module(
                module=module, name=name, force=force)
            return module

        # Used as a decorator: @xxx.register_module()
        def _register(cls):
            self._register_module(module=cls, name=name, force=force)
            return cls

        return _register
