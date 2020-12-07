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
from ...base import ONNXToMindSporeMapper
from ...gen_setting import Setting, Tensor, get_dtype


class MulMapper(ONNXToMindSporeMapper):
    """Mul mapper."""

    @staticmethod
    def _operation_name_in_ms(*args, **kwargs):
        return "P.Mul"

    @staticmethod
    def _convert_params(**kwargs):
        return dict()

    @staticmethod
    def _convert_trained_weights(**kwargs):
        return dict()

    @staticmethod
    def _convert_settings(**kwargs):
        weights = kwargs.get("weights")
        if not weights:
            return Setting()
        ref, tensor = list(weights.items())[0]
        return Setting(op_extra_tensor=Tensor(shape=tensor.shape,
                                              dtype=get_dtype(tensor), reference=ref))
