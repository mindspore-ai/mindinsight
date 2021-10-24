# Copyright 2021 Huawei Technologies Co., Ltd.All Rights Reserved.
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
import numpy as np

from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords, \
    WeightType


class SelectMapper(ONNXToMindSporeMapper):
    """Select mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Select"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        weights = kwargs.get('weight', list())
        onnx_location_tensors = [(SelectMapper._find_onnx_name_by_index(i, weights),
                                  SelectMapper._find_location_by_index(i, weights),
                                  SelectMapper._find_val_by_index(i, weights)) for i, _ in enumerate(weights)]
        input_shape = kwargs.get('params').get('input_shape')
        trainable_weights = dict()
        for onnx_location_tensor in onnx_location_tensors:
            if isinstance(onnx_location_tensor[2], np.ndarray) and onnx_location_tensor[2].shape:
                value = onnx_location_tensor[2]

                if input_shape != value.shape:
                    idx_diffs = [idx for idx, v in enumerate(input_shape) if v != value.shape[idx]]
                    if len(idx_diffs) == 1:
                        idx_diff = idx_diffs[0]
                        data = value.repeat(input_shape[idx_diff], idx_diff)
                    else:
                        raise AttributeError('Unsupported attributes in SelectMapper.')
                else:
                    data = value

                location = onnx_location_tensor[1]
                trainable_weights[f"input_{location}"] = {'data': data,
                                                          'type': WeightType.PARAMETER.value,
                                                          'onnx_name': onnx_location_tensor[0]}
        return trainable_weights

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get('operation')
        args = kwargs.get('converted_params', dict())
        weights = kwargs.get('weights', list())
        trainable_params = kwargs.get('trainable_params', dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        onnx_location_tensors = [(SelectMapper._find_onnx_name_by_index(i, weights),
                                  SelectMapper._find_location_by_index(i, weights),
                                  SelectMapper._find_val_by_index(i, weights)) for i, _ in enumerate(weights)]
        input_shape = kwargs.get('raw_params').get('input_shape')

        variable_slot = 'var_0'
        init_template = f"self.{{{variable_slot}}} = {op}()"
        inputs_in_construct = [f"{{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}"]
        init_template_list, construct_template = SelectMapper._generate_init_construct(variable_slot, args, input_shape,
                                                                                       init_template,
                                                                                       inputs_in_construct,
                                                                                       onnx_location_tensors)
        template = {
            variable_slot: {
                TemplateKeywords.INIT.value: init_template_list,
                TemplateKeywords.CONSTRUCT.value: [construct_template]
            }
        }
        exchange_msg = SelectMapper._generate_exchange_msg_select(variable_slot, op, args, weights, trainable_params,
                                                                  onnx_location_tensors)
        outputs_list = [f"opt_{{{variable_slot}}}"]
        outputs_mapping = ((0, 0),)
        return template, exchange_msg, outputs_list, outputs_mapping

    @staticmethod
    def _generate_init_construct(variable_slot, args, input_shape, init_template, inputs_in_construct,
                                 onnx_location_tensors):
        """Generate init template and construct template."""
        init_template_list = [init_template]
        for onnx_location_tensor in onnx_location_tensors:
            location = onnx_location_tensor[1]
            inputs_in_construct.insert(location, f"self.{{{variable_slot}}}_input_{location}")
            value = onnx_location_tensor[2]
            if value.shape:
                variable_slot_param_name = f"{variable_slot}/input_{location}"
                init_input = f"self.{{{variable_slot}}}_input_{location} = {{{variable_slot_param_name}}}"
            else:
                args[f"input_{location}"] = value.tolist()
                init_input = f"self.{{{variable_slot}}}_input_{location} = " \
                             f"Tensor({{input_{location}}} * np.ones({tuple(input_shape)}).astype(np.{value.dtype}))"
            init_template_list.append(init_input)

        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}({', '.join(inputs_in_construct)})"
        return init_template_list, construct_template

    @staticmethod
    def _generate_exchange_msg_select(variable_slot, op, args, weights, trainable_params, onnx_location_tensors):
        """Generate exchange_msg for select mapper."""
        exchange_msg = SelectMapper._generate_exchange_msg(variable_slot=variable_slot, op=op, args=args,
                                                           weights=weights, trainable_params=trainable_params)
        declared_key = ExchangeMessageKeywords.VariableScope.value.PARAMETERS_DECLARED.value
        for onnx_location_tensor in onnx_location_tensors:
            value = onnx_location_tensor[2]
            if value.shape:
                if not exchange_msg[variable_slot].get(declared_key):
                    exchange_msg[variable_slot][declared_key] = {f"input_{onnx_location_tensor[1]}": ""}
                else:
                    exchange_msg[variable_slot][declared_key][f"input_{onnx_location_tensor[1]}"] = ""
        return exchange_msg
