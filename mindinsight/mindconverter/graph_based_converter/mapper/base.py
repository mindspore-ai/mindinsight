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
"""Mapper module."""
import abc
import importlib
import json
import os
from typing import Dict
from mindinsight.mindconverter.common.log import logger as log
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords

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
GET_OP_TEMPLATE = "_generate_snippet_template"


class Mapper(metaclass=abc.ABCMeta):
    """Mapper between third-party-operation and MindSpore."""

    @staticmethod
    @abc.abstractmethod
    def _operation_name_in_ms(*args, **kwargs):
        """Corresponding operation name in MindSpore."""

    @staticmethod
    @abc.abstractmethod
    def _convert_params(**kwargs):
        """Convert third party operation's param into MindSpore operation."""

    @staticmethod
    @abc.abstractmethod
    def _convert_trained_weights(**kwargs):
        """Convert third party operation's weights into MindSpore operation."""

    @classmethod
    @abc.abstractmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        """Convert third party operation's param into MindSpore operation."""

    @staticmethod
    @abc.abstractmethod
    def _generate_snippet_template(**kwargs):
        """Generate code template according to node info."""


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
            template_generator = getattr(converter, GET_OP_TEMPLATE)
        except (ModuleNotFoundError,) as e:
            # If mapper can not be found, then skip it.
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            log.error(err_msg)
            return None, None, None, None

        try:
            converter_name = op_name_converter(params=params, weights=weights, op_name=op_name)
            converted_params = params_converter(params=params, weights=weights)
            if "input_shape" in converted_params:
                converted_params.pop("input_shape")
            if "output_shape" in converted_params:
                converted_params.pop("output_shape")
            # set to converted_weights to enable weight migration
            _ = weights_converter(weights=weights) if weights else dict()
            code_template, exchange_msg, outputs_list, outputs_mapping = template_generator(
                operation=converter_name,
                converted_params=converted_params,
                raw_params=params,
                weights=weights
            )
        except (AttributeError, KeyError, ValueError, TypeError, IndexError) as e:
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            log.error(err_msg)
            code_template, exchange_msg, outputs_list, outputs_mapping = template_generator(
                operation=op_name,
                params=params,
                weights=weights
            )

        return code_template, exchange_msg, outputs_list, outputs_mapping

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
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        if not op:
            raise ValueError("Can not get MindSpore operation name.")
        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}({', '.join(['%s={%s}' % (p, p) for p in args])})"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [init_template],
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = {
            variable_slot: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: op,
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: args,
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: weights,
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: {}
            }
        }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _find_val_by_index(loc_index, values_dict):
        """Find value by location index of values_dict."""
        result = None
        for idx, dict_val in enumerate(values_dict.values()):
            if idx == loc_index:
                result = dict_val
                break
        return result
