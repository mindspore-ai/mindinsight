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
from mindconverter.graph_based_converter.constant import FIRST_LEVEL_INDENT, SECOND_LEVEL_INDENT, NEW_LINE
from mindconverter.graph_based_converter.mapper.base import AtenToMindSporeMapper


class GELUMapper(AtenToMindSporeMapper):
    """GELU mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        GELUMapper.global_context.hard_template["GELU"] = [
            f"class GELU(nn.Cell):",
            f"{FIRST_LEVEL_INDENT}def __init__(self):",
            f"{SECOND_LEVEL_INDENT}super().__init__()",
            f"{SECOND_LEVEL_INDENT}self.erf = P.Erf()",
            f"{SECOND_LEVEL_INDENT}self.sqrt = P.Sqrt()",
            f"{SECOND_LEVEL_INDENT}self.const0 = Tensor(0.5, mindspore.float32)",
            f"{SECOND_LEVEL_INDENT}self.const1 = Tensor(1.0, mindspore.float32)",
            f"{SECOND_LEVEL_INDENT}self.const2 = Tensor(2.0, mindspore.float32)",
            f"{NEW_LINE}",
            f"{FIRST_LEVEL_INDENT}def construct(self, x):",
            f"{SECOND_LEVEL_INDENT}return x * self.const0 * (self.const1 + self.erf(x / self.sqrt(self.const2)))",
            f"{NEW_LINE}"
        ]
        return "GELU"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()
