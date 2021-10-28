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
"""Test CumSum operator mapper."""
from unittest import TestCase
import numpy as np
from mindconverter.graph_based_converter.mapper.base import ONNXToMindSporeMapper
from mindconverter.graph_based_converter.common.code_fragment import Fragment
from mindconverter.graph_based_converter.third_party_graph.base import NodeWeight


class TestCumSum(TestCase):
    """Tester of CumSun."""

    def test_mapper(self):
        """Test code generation."""
        onnx_info = {
            "op_name": "onnx::CumSum",
            "attributes": {},
            "weights": [NodeWeight(weight_name="axis", weight_value=np.int32(0), weight_location=0)]
        }
        template, exchange_msg, outputs_lists, outputs_mapping = ONNXToMindSporeMapper.convert(
            onnx_info['op_name'],
            onnx_info['attributes'],
            onnx_info['weights']
        )
        exchange_msg['var_0']['variable_name'] = 'cumsum_op'
        exchange_msg['var_0']['inputs'] = ['x']

        fragment = Fragment(data_entity=exchange_msg, code_template=template, outputs=outputs_lists,
                            outputs_mapping=outputs_mapping)

        code = fragment()
        init_code = code[0]
        construct_code = code[1]
        self.assertEqual(init_code, [
            "self.cumsum_op = P.CumSum(exclusive=False, reverse=False)",
            "self.cumsum_op_axis = 0"
        ])
        self.assertEqual(construct_code, [
            "opt_cumsum_op = self.cumsum_op(x, self.cumsum_op_axis)"
        ])
