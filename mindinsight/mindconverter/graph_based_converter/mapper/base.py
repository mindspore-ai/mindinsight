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
from mindinsight.mindconverter.common.log import logger as log

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
GET_OP_SETTINGS = "_convert_settings"


class Mapper(metaclass=abc.ABCMeta):
    """Mapper between third-party-operation and MindSpore."""

    @staticmethod
    @abc.abstractmethod
    def _operation_name_in_ms(*args, **kwargs):
        """Corresponding operation name in mindspore."""

    @staticmethod
    @abc.abstractmethod
    def _convert_params(**kwargs):
        """Convert third party operation's param into MindSpore operation."""

    @staticmethod
    @abc.abstractmethod
    def _convert_trained_weights(**kwargs):
        """Convert third party operation's weights into MindSpore operation."""

    @staticmethod
    @abc.abstractmethod
    def _convert_settings(**kwargs):
        """Convert third party operation's params into MindSpore OP operator."""

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
            Tuple[str, dict, dict], operation name and params and settings.
        """
        global TABLE
        module_name = TABLE.get(op_name)

        if not module_name:
            return None, dict(), None, dict()

        pos = module_name.rfind(".")
        try:
            converter = getattr(importlib.import_module(module_name[:pos]),
                                module_name[pos + 1:])
            op_name_converter = getattr(converter, GET_OP_NAME)
            params_converter = getattr(converter, GET_OP_PARAMS)
            weights_converter = getattr(converter, GET_OP_WEIGHTS)
            settings_converter = getattr(converter, GET_OP_SETTINGS)
        except (ModuleNotFoundError,) as e:
            # If mapper can not be found, then skip it.
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            log.error(err_msg)
            return None, dict(), None, dict()

        try:
            converter_name = op_name_converter(params=params, weights=weights, op_name=op_name)
            converted_params = params_converter(params=params, weights=weights)
            converted_weights = weights_converter(weights=weights) if weights else dict()
            converted_params.update(converted_weights)
            converted_settings = settings_converter(params=params, weights=weights)
        except (AttributeError, KeyError, ValueError, TypeError, IndexError) as e:
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            log.error(err_msg)
            return None, dict(), None, dict()

        return converter_name, converted_params, converted_settings, converted_weights

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _convert_params(**kwargs):
        raise NotImplementedError

    @staticmethod
    def _convert_trained_weights(**kwargs):
        raise NotImplementedError

    @staticmethod
    def _convert_settings(**kwargs):
        raise NotImplementedError
