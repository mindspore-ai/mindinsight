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

from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords


class PoolMapper(ONNXToMindSporeMapper):
    """Pool mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        if kwargs['op_name'] == 'onnx::AveragePool':
            op_name = 'nn.AvgPool{}d'
        else:
            op_name = 'nn.MaxPool{}d'
        dim = len(kwargs['params']['strides'])
        op_name = op_name.format(dim)
        if op_name == 'nn.MaxPool3d':
            return "P.MaxPool3D"
        if op_name == 'nn.AvgPool3d':
            return "P.AvgPool3D"
        return op_name

    @staticmethod
    def _convert_params(**kwargs):
        params = kwargs['params']
        transformed_params = dict()
        transformed_params["kernel_size"] = tuple(params['kernel_shape'])
        pad_mode = params.get('auto_pad')
        if not pad_mode:
            pad_mode = 'pad'
        elif pad_mode != 'VALID':
            pad_mode = 'same'
        transformed_params["pad_mode"] = pad_mode
        dim = len(kwargs['params']['strides'])
        if dim == 3:
            transformed_params["strides"] = tuple(params['strides'])
        else:
            transformed_params["stride"] = tuple(params['strides'])
        return transformed_params

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        if "onnx" in op or op == "P.MaxPool3D":
            return ONNXToMindSporeMapper._generate_snippet_template(**kwargs)

        if op == "nn.MaxPool2d":
            op = "P.MaxPool3D"
            kernel_size = [1] + kwargs['raw_params']['kernel_shape']
            strides = [1] + kwargs['raw_params']['strides']
            ceil_mode = kwargs['raw_params'].get('ceil_mode', False)
            pad_list = [0, 0] + kwargs['raw_params'].get('pads', [])
            args["strides"] = tuple(strides)
            args["ceil_mode"] = bool(ceil_mode)
            args["pad_list"] = tuple(pad_list)
            args["kernel_size"] = tuple(kernel_size)
            args.pop('stride')
            args_list = []
            for p, v in args.items():
                if isinstance(v, str):
                    args_list.append('%s="{%s}"' % (p, p))
                else:
                    args_list.append('%s={%s}' % (p, p))

            variable_slot = "var_0"
            init_template_expand_dims = f"self.pad_{{{variable_slot}}} = P.ExpandDims()"
            init_template = f"self.inter_{{{variable_slot}}} = {op}({', '.join(args_list)})"
            init_template_squeeze = f"self.{{{variable_slot}}} = P.Squeeze(axis=1)"

            construct_template_expand_dims = f"opt_{{{variable_slot}}} = " \
                                             f"self.pad_{{{variable_slot}}}" \
                                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, 1)"
            construct_template = f"opt_inter_{{{variable_slot}}} = " \
                                 f"self.inter_{{{variable_slot}}}(opt_{{{variable_slot}}})"
            construct_template_squeeze = f"opt_{{{variable_slot}}} = " \
                                         f"self.{{{variable_slot}}}(opt_inter_{{{variable_slot}}})"

            template = {
                variable_slot: {
                    TemplateKeywords.INIT.value: [init_template_expand_dims, init_template, init_template_squeeze],
                    TemplateKeywords.CONSTRUCT.value: [construct_template_expand_dims, construct_template,
                                                       construct_template_squeeze]
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
                    ExchangeMessageKeywords.VariableScope.value.WEIGHTS.value: dict(),
                    ExchangeMessageKeywords.VariableScope.value.TRAINABLE_PARAMS.value: dict()
                }
            }
            outputs_list = [f"opt_{{{variable_slot}}}"]
            outputs_mapping = ((0, 0),)
            return template, exchange_msg, outputs_list, outputs_mapping

        return None
