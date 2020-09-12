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
"""Mapper module."""
import abc
import importlib
import json
import os
from typing import Dict

CONFIG_JSON = "onnx_to_ms.json"
OPERATION_TABLE = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    CONFIG_JSON
)

with open(OPERATION_TABLE) as file:
    # Load mapping table which key is operation name in ONNX and
    # value is corresponding module path.
    TABLE = json.load(file)

# Define global func name.
GET_OP_NAME = "_operation_name_in_ms"
GET_OP_PARAMS = "_convert_params"
GET_OP_WEIGHTS = "_convert_trained_weights"


class Mapper(metaclass=abc.ABCMeta):
    """Mapper between third-party-operation and MindSpore."""

    @staticmethod
    @abc.abstractmethod
    def _operation_name_in_ms(*args, **kwargs):
        """Corresponding operation name in mindspore."""

    @staticmethod
    @abc.abstractmethod
    def _convert_params(params, weights):
        """Convert third party operation's param into MindSpore operation."""

    @staticmethod
    @abc.abstractmethod
    def _convert_trained_weights(weights):
        """Convert third party operation's weights into MindSpore operation."""

    @classmethod
    @abc.abstractmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        """Convert third party operation's param into MindSpore operation."""


class ONNXToMindSporeMapper(Mapper, abc.ABC):
    """ONNX operation to MindSpore."""

    @classmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        """
        Convert third party operation's param into MindSpore operation.

        Args:
            op_name (str): Operation name in ONNX.
            params (dict): Params in onnx.
            weights (dict): Weights in onnx.

        Returns:
            Tuple[str, dict], operation name and params.
        """
        global TABLE
        module_name = TABLE.get(op_name)

        if not module_name:
            return None, dict()

        pos = module_name.rfind(".")
        try:
            converter = getattr(importlib.import_module(module_name[:pos]),
                                module_name[pos + 1:])
            op_name_converter = getattr(converter, GET_OP_NAME)
            params_converter = getattr(converter, GET_OP_PARAMS)
            weights_converter = getattr(converter, GET_OP_WEIGHTS)
        except (ModuleNotFoundError,) as e:
            # If mapper can not be found, then skip it.
            print(f"Converting {op_name} failed, see {e}")
            return None, dict()

        try:
            converter_name = op_name_converter(params=params, weights=weights, op_name=op_name)
            converted_params = params_converter(params, weights)
            converted_weights = weights_converter(weights) if weights else dict()
            converted_params.update(converted_weights)
        except (AttributeError,) as _:
            print(f"Converting {op_name} failed.")
            return None, dict()

        return converter_name, converted_params

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _convert_params(params, weights):
        raise NotImplementedError

    @staticmethod
    def _convert_trained_weights(weights):
        raise NotImplementedError
