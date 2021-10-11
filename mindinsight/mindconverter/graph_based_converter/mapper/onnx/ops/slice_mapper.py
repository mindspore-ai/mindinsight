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
import numpy as np

from mindinsight.mindconverter.graph_based_converter.common.utils import reset_init_or_construct
from mindinsight.mindconverter.graph_based_converter.constant import ExchangeMessageKeywords, TemplateKeywords
from mindinsight.mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper


class SliceMapper(ONNXToMindSporeMapper):
    """Slice mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.StridedSlice"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _generate_snippet_template(**kwargs):
        """Generate snippet template."""
        template, exchange_msg, outputs_list, outputs_mapping = ONNXToMindSporeMapper._generate_snippet_template(
            **kwargs)
        op = kwargs.get("operation")
        args = kwargs.get("converted_params", dict())
        weights = kwargs.get("weights")
        params = kwargs["raw_params"]
        ipt_shape = params["input_shape"]

        starts = SliceMapper._find_val_by_index(0, weights)
        ends = SliceMapper._find_val_by_index(1, weights)
        axes = SliceMapper._find_val_by_index(2, weights, np.array(list(range(len(ipt_shape)))))
        steps = SliceMapper._find_val_by_index(3, weights, np.array([1 for _ in range(len(ipt_shape))]))

        if not op:
            raise ValueError("Can not get MindSpore operation name.")

        if not weights:
            raise ValueError("Can not get required params from slice.")

        if axes.shape != (1,):
            ordered_begin = sorted(zip(starts.tolist(), axes.tolist()), key=lambda x: x[1], reverse=False)
            ordered_end = sorted(zip(ends.tolist(), axes.tolist()), key=lambda x: x[1], reverse=False)
            ordered_strides = sorted(zip(steps.tolist(), axes.tolist()), key=lambda x: x[1], reverse=False)
            begin = [i[0] for i in ordered_begin]
            end = [min(i[0], ipt_shape[i[1]]) for i in ordered_end]
            strides = [i[0] for i in ordered_strides]
        else:
            axis = axes.tolist()[0]
            begin = [0 for _ in range(len(ipt_shape))]
            end = list(ipt_shape)
            strides = [1 for _ in range(len(ipt_shape))]
            begin[axis] = starts.tolist()[0]
            end[axis] = min(ends.tolist()[0], end[axis])
            strides[axis] = steps.tolist()[0]

        args['begin'] = tuple(begin)
        args['end'] = tuple(end)
        args['strides'] = tuple(strides)

        variable_slot = "var_0"
        init_template = f"self.{{{variable_slot}}} = {op}()"
        init_begin = f"self.{{{variable_slot}}}_begin = {{begin}}"
        init_end = f"self.{{{variable_slot}}}_end = {{end}}"
        init_strides = f"self.{{{variable_slot}}}_strides = {{strides}}"
        construct_template = f"opt_{{{variable_slot}}} = self.{{{variable_slot}}}" \
                             f"({{{ExchangeMessageKeywords.VariableScope.value.INPUTS.value}}}, " \
                             f"self.{{{variable_slot}}}_begin, self.{{{variable_slot}}}_end, " \
                             f"self.{{{variable_slot}}}_strides)"
        template = reset_init_or_construct(template, variable_slot,
                                           [init_template, init_begin, init_end, init_strides],
                                           TemplateKeywords.INIT.value)
        template = reset_init_or_construct(template, variable_slot, [construct_template],
                                           TemplateKeywords.CONSTRUCT.value)

        return template, exchange_msg, outputs_list, outputs_mapping
