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
import re
from typing import Dict

import numpy as np

from mindconverter.common.log import MindConverterLogger
from mindconverter.graph_based_converter.common.global_context import GlobalContext
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, WeightType, \
    UNKNOWN_SHAPE_WITHOUT_PRECURSOR_NODES

# Define global func name.
GET_OP_NAME = "_operation_name_in_ms"
GET_OP_PARAMS = "_convert_params"
GET_OP_WEIGHTS = "_convert_trained_weights"
GET_OP_SETTINGS = "_convert_settings"
GET_OP_TEMPLATE = "_generate_snippet_template"


def get_table(framework):
    config_json = f"{framework}_to_ms.json"
    operation_table = os.path.join(os.path.abspath(os.path.dirname(__file__)), config_json)
    table = {}
    if os.path.exists(operation_table):
        with open(operation_table) as f:
            table = json.load(f)
    return table


def get_module_name(op_name):
    """Get module_name."""
    framework_file = op_name.split("::")[0]
    config_json = f"{framework_file}_to_ms.json"
    operation_table = os.path.join(os.path.abspath(os.path.dirname(__file__)), config_json)
    module_name = None
    if os.path.exists(operation_table):
        with open(operation_table) as f:
            table = json.load(f)
        module_name = table.get(op_name)
    return module_name


def flatten_list(input_list):
    """Flatten multi-layer list ot one-layer."""
    flattened_result = list()
    for ipt in input_list:
        if isinstance(ipt, (tuple, list)):
            flattened_result.extend(flatten_list(ipt))
        else:
            flattened_result.append(ipt)
    return flattened_result


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

    @staticmethod
    def _generate_exchange_msg(**kwargs):
        """Generate exchange msg."""
        exchange_msg = {
            kwargs["variable_slot"]: {
                ExchangeMessageKeywords.VariableScope.value.OPERATION.value: kwargs.get("op"),
                ExchangeMessageKeywords.VariableScope.value.VARIABLE_NAME.value: None,
                ExchangeMessageKeywords.VariableScope.value.OUTPUT_TYPE.value:
                    ExchangeMessageKeywords.VariableScope.value.TSR_TYPE.value,
                ExchangeMessageKeywords.VariableScope.value.INPUTS.value: [],
                ExchangeMessageKeywords.VariableScope.value.ARGS.value: kwargs.get("args"),
                ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: kwargs.get("weights", list()),
                ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value:
                    kwargs.get("trainable_params", dict())
            }
        }
        return exchange_msg

    @staticmethod
    def is_tensor(data):
        """Get whether data is tensor or not."""
        return isinstance(data, np.ndarray) and data.shape


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
        module_name = get_module_name(op_name)

        if not module_name:
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )
            return code_template, exchange_msg, outputs_list, outputs_mapping

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
            MindConverterLogger.error(err_msg)
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )
            return code_template, exchange_msg, outputs_list, outputs_mapping

        try:
            converter_name = op_name_converter(params=params, weights=weights, op_name=op_name)
            converted_params = params_converter(params=params, weights=weights)

            if "input_shape" in converted_params:
                converted_params.pop("input_shape")
            if "output_shape" in converted_params:
                converted_params.pop("output_shape")
            # set to converted_weights to enable weight migration
            converted_weights = weights_converter(params=params, weights=weights) if weights else dict()
            code_template, exchange_msg, outputs_list, outputs_mapping = template_generator(
                operation=converter_name,
                converted_params=converted_params,
                raw_params=params,
                weights=weights,
                trainable_params=converted_weights
            )

        except (AttributeError, KeyError, ValueError, TypeError, IndexError) as e:
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            MindConverterLogger.error(err_msg)
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
        op = kwargs.get("operation").replace("::", ".")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        trainable_params = kwargs.get("trainable_params", dict())
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
        exchange_msg = ONNXToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args,
                                                                    weights=weights, trainable_params=trainable_params)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _find_val_by_index(loc_index, weights_list, default_val=None):
        """Find value by location index of weights_list."""
        result = default_val
        if loc_index < 0:
            return weights_list[loc_index].value

        for idx, weight in enumerate(weights_list):
            if idx == loc_index:
                result = weight.value
                break
        return result

    @staticmethod
    def _generate_snippet_template_for_math_operation(**kwargs):
        """Generate code snippet for math operation."""
        op = kwargs.get("operation").replace("onnx::", "onnx.")
        args = kwargs.get("converted_params", dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")
        variable_slot = "var_0"
        construct_template = f"opt_{{{variable_slot}}} = {op}()" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}})"
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: [],
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = ONNXToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _find_location_by_index(loc_index, weights_list):
        """Find weight location in inputs of Node."""
        result = -1
        if loc_index < 0:
            return weights_list[loc_index].location

        for idx, weight in enumerate(weights_list):
            if idx == loc_index:
                result = weight.location
                break
        return result

    @staticmethod
    def _find_onnx_name_by_index(loc_index, weights_list):
        """Find weight onnx name in inputs of Node."""
        result = -1
        if loc_index < 0:
            return weights_list[loc_index].name

        for idx, weight in enumerate(weights_list):
            if idx == loc_index:
                result = weight.name
                break
        return result


class AtenToMindSporeMapper(Mapper, abc.ABC):
    """X operation to MindSpore."""

    global_context = GlobalContext()

    @classmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        """
        Convert third party operation's param into MindSpore operation.

        Args:
            op_name (str): Operation name in X.
            params (dict): Params in X.
            weights (dict): Weights in X.

        Returns:
            Tuple[str, dict, dict], operation name and params and settings.
        """
        module_name = cls._get_mapper(op_name)
        if not module_name:
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )
            return code_template, exchange_msg, outputs_list, outputs_mapping

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
            MindConverterLogger.error(err_msg)
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )
            return code_template, exchange_msg, outputs_list, outputs_mapping

        try:
            converter_name = op_name_converter(params=params, weights=weights, op_name=op_name)
            converted_params = params_converter(params=params, weights=weights)

            if "input_shape" in converted_params:
                converted_params.pop("input_shape")
            if "output_shape" in converted_params:
                converted_params.pop("output_shape")
            # set to converted_weights to enable weight migration
            converted_weights = weights_converter(params=params, weights=weights)
            code_template, exchange_msg, outputs_list, outputs_mapping = template_generator(
                operation=converter_name,
                converted_params=converted_params,
                raw_params=params,
                weights=weights,
                trainable_params=converted_weights
            )

        except (AttributeError, KeyError, ValueError, TypeError, IndexError) as e:
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            MindConverterLogger.error(err_msg)
            code_template, exchange_msg, outputs_list, outputs_mapping = template_generator(
                operation=op_name,
                params=params,
                weights=weights
            )

        return code_template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_mapper(op_name):
        """Get mapper class."""
        framework_file = op_name.split("::")[0]
        config_json = f"{framework_file}_to_ms.json"
        operation_table = os.path.join(os.path.abspath(os.path.dirname(__file__)), config_json)
        module_name = None
        if os.path.exists(operation_table):
            with open(operation_table) as f:
                table = json.load(f)
            module_name = table.get(op_name)
        return module_name

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        raise NotImplementedError

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation").replace("::", ".")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        trainable_params = kwargs.get("trainable_params", dict())
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

        exchange_msg = AtenToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args,
                                                                    weights=weights, trainable_params=trainable_params)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def get_args_name_list(**kwargs):
        """Get args_name_list according to number params in node."""
        params = kwargs.get("params", dict()).copy() or kwargs.get("raw_params", dict())
        params.pop("input_shape")
        params.pop("output_shape")
        num_aten_inputs = len(params)

        existing_packs = dict()
        for name in params.copy():
            ret = re.match(r"(.*)\[(.*)\((.*)\)]", name)
            if ret:
                param_name, pack_id, pack_struct_pattern = ret.groups()
                pack_struct = [symbol for symbol in pack_struct_pattern.split(",")]
                param_idx = pack_struct.index("*")
                existing_packs.setdefault(pack_id, pack_struct)[param_idx] = param_name
                params[param_name] = params.pop(name)
            else:
                existing_packs.setdefault(name, None)

        for existing_packs_inst in existing_packs.values():
            if existing_packs_inst:
                num_aten_inputs -= len(existing_packs_inst) - 1

        def get_extend_args_name_list(name_list):
            """Get args_name_list extended."""
            for existing_pack_id_, existing_pack_inst_ in existing_packs.items():
                if existing_pack_inst_ and len(existing_pack_inst_) > 1:
                    pack_name_ = name_list[int(existing_pack_id_)]
                    extend_num_ = len(existing_pack_inst_)
                    name_list[int(existing_pack_id_)] = [f"{pack_name_}{extend_idx}" for extend_idx in
                                                         range(extend_num_)]
            return name_list

        args_name = kwargs.get("args_name")
        if isinstance(args_name, list):
            args_name_list = get_extend_args_name_list(args_name)
        elif isinstance(args_name, dict):
            args_name_list = args_name.get(num_aten_inputs)
            if not args_name_list:
                raise ValueError(
                    f"Number of params is required to be one of "
                    f"[{', '.join([str(num) for num in args_name])}], but {num_aten_inputs} is gotten.")
            args_name_list = get_extend_args_name_list(args_name_list.copy())
        else:
            raise ValueError(f"Type of args_name should be Union<list, tuple>, but {type(args_name)} is gotten.")
        if kwargs.get("return_raw"):
            return args_name_list
        return flatten_list(args_name_list)

    @staticmethod
    def _params_parser(raw_params, args_name, trainable_params):
        """Parse params in Node."""
        variable_slot = "var_0"
        input_symbol = ExchangeMessageKeywords.VariableScope.value.INPUTS.value
        args_name_list = AtenToMindSporeMapper.get_args_name_list(raw_params=raw_params,
                                                                  weights=trainable_params,
                                                                  args_name=args_name)

        num_params = len(args_name_list)
        raw_params = {name: value for name, value in raw_params.items() if value != "from_input"}

        if trainable_params:
            constant_inputs_dict = {value.get("location", 0): name for name, value in trainable_params.items()}
            inputs = list()
            for idx in range(num_params):
                inputs.append(
                    constant_inputs_dict[idx] if idx in constant_inputs_dict else raw_params.get(f"constant_{idx}",
                                                                                                 f"{{{input_symbol}}}"))
        else:
            inputs = [raw_params.get(f"constant_{idx}", f"{{{input_symbol}}}") for idx in range(num_params)]

        args = dict()
        for idx, (arg_name, arg_val) in enumerate(zip(args_name_list, inputs)):
            if arg_val != f"{{{input_symbol}}}" and arg_name not in trainable_params:
                inputs[idx] = arg_name
                args[arg_name] = tuple(arg_val) if isinstance(arg_val, list) else arg_val

        num_inputs = inputs.count(f"{{{input_symbol}}}")

        input_idx = 0
        group_inputs = list()
        for idx, ipt in enumerate(inputs):
            if ipt == f"{{{input_symbol}}}":
                if num_inputs == 1:
                    inputs[idx] = f"{{{input_symbol}}}"
                else:
                    group_inputs.append((input_idx, input_idx))
                    inputs[idx] = f"{{{input_symbol}_{input_idx}}}"
                input_idx += 1
            else:
                inputs[idx] = f"self.{{{variable_slot}}}_{args_name_list[idx]}"
        return inputs, args, group_inputs

    @staticmethod
    def has_precursor_nodes(input_shape):
        """The node has precursor nodes or not."""
        return not isinstance(input_shape, int) or input_shape != UNKNOWN_SHAPE_WITHOUT_PRECURSOR_NODES

    @staticmethod
    def generate_parameters_declared(variable_slot, init_template_list, args, trainable_params):
        """Generate parameters_declared."""
        parameters_declared = dict()
        for name, trainable_param in trainable_params.copy().items():
            value = trainable_param["data"]
            if AtenToMindSporeMapper.is_tensor(value):
                variable_slot_param_name = f"{variable_slot}/{name}"
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{variable_slot_param_name}}}")
                parameters_declared[name] = ""
            else:
                args[name] = value.tolist()
                init_template_list.append(f"self.{{{variable_slot}}}_{name} = {{{name}}}")
                trainable_params.pop(name)
        return parameters_declared


class SelfDefinedPatternToMindSporeMapper(Mapper, abc.ABC):
    """Self-defined-pattern operation to MindSpore."""

    @classmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        """
        Convert third party operation's param into MindSpore operation.

        Args:
            op_name (str): Operation name in X.
            params (dict): Params in X.
            weights (dict): Weights in X.

        Returns:
            Tuple[str, dict, dict], operation name and params and settings.
        """
        module_name = cls._get_mapper(op_name)
        if not module_name:
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )
            return code_template, exchange_msg, outputs_list, outputs_mapping

        pos = module_name.rfind(".")

        try:
            pattern_obj = getattr(importlib.import_module(module_name[:pos]), module_name[pos + 1:])()
            converter_name = cls._operation_name_in_ms(params=params, weights=weights, op_name=op_name)
            converted_params = cls._convert_params(params=params, weights=weights)

            if "input_shape" in converted_params:
                converted_params.pop("input_shape")
            if "output_shape" in converted_params:
                converted_params.pop("output_shape")
            # set to converted_weights to enable weight migration
            converted_weights = cls._convert_trained_weights(params=params, weights=weights) if weights else dict()
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=converter_name,
                converted_params=converted_params,
                raw_params=params,
                weights=weights,
                trainable_params=converted_weights,
                pattern_obj=pattern_obj
            )

        except (AttributeError, KeyError, ValueError, TypeError, IndexError) as e:
            err_msg = f"Converting {op_name} failed, see {str(e)}"
            MindConverterLogger.error(err_msg)
            code_template, exchange_msg, outputs_list, outputs_mapping = cls._generate_snippet_template(
                operation=op_name,
                params=params,
                weights=weights
            )

        return code_template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _get_mapper(op_name):
        """Get mapper class."""
        self_pass_module = "mindconverter.graph_based_converter.third_party_graph.self_patterns"
        pattern_name = op_name.replace('self_defined_pattern::', '')
        return f"{self_pass_module}.{pattern_name}.{pattern_name.capitalize()}"

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return kwargs["op_name"].replace("::", ".")

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        params = kwargs["params"]
        weights = kwargs["weights"]

        trainable_params = dict()
        for _, param_value in params.items():
            inputs_list = param_value["inputs"] if isinstance(param_value, Dict) else list()
            for weight in weights:
                if weight.name in inputs_list and isinstance(weight.value, np.ndarray) and weight.value.shape:
                    trainable_params[f"pattern_weight_{len(trainable_params)}"] = \
                        {"data": weight.value,
                         "type": WeightType.PARAMETER.value,
                         "onnx_name": weight.name}
        return trainable_params

    @staticmethod
    def _generate_snippet_template(**kwargs):
        template, exchange_msg, outputs_list, outputs_mapping = \
            SelfDefinedPatternToMindSporeMapper._generate_snippet_template_default(**kwargs)
        op = kwargs.get("operation")
        args = kwargs.get("converted_params")
        weights = kwargs.get("weights")
        raw_params = kwargs.get("raw_params")
        trainable_params = kwargs.get("trainable_params", dict())
        if not raw_params:
            return template, exchange_msg, outputs_list, outputs_mapping

        pattern_obj = kwargs["pattern_obj"]

        variable_slot = "var_0"
        init_template_list = pattern_obj.generate_init_template_list(variable_slot=variable_slot, raw_params=raw_params,
                                                                     weights=weights)
        construct_template_list = pattern_obj.generate_construct_template_list(variable_slot=variable_slot,
                                                                               raw_params=raw_params, weights=weights)

        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: init_template_list,
                TemplateKeywords.CONSTRUCT.value: construct_template_list
            }
        }
        exchange_msg = SelfDefinedPatternToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot,
                                                                                  op=op, args=args, weights=weights,
                                                                                  trainable_params=trainable_params)
        if trainable_params:
            exchange_msg[variable_slot][ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value] = {
                name: "" for name in trainable_params
            }
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _generate_snippet_template_default(**kwargs):
        """Generate default snippet template."""
        op = kwargs.get("operation").replace("::", ".")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        trainable_params = kwargs.get("trainable_params", dict())
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

        exchange_msg = SelfDefinedPatternToMindSporeMapper._generate_exchange_msg(variable_slot=variable_slot, op=op,
                                                                                  args=args,
                                                                                  weights=weights,
                                                                                  trainable_params=trainable_params)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping


class PytorchToMindSporeMapper(AtenToMindSporeMapper, SelfDefinedPatternToMindSporeMapper, abc.ABC):
    """Pytorch operation to MindSpore."""

    @classmethod
    def convert(cls, op_name: str, params: Dict, weights: Dict = None):
        if op_name.startswith("aten::"):
            return AtenToMindSporeMapper.convert(op_name=op_name, params=params, weights=weights)
        if op_name.startswith("self_defined_pattern::"):
            return SelfDefinedPatternToMindSporeMapper.convert(op_name=op_name, params=params, weights=weights)
        raise ValueError("Unsupported op_type.")

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return kwargs["op_name"].replace("::", ".")

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()
