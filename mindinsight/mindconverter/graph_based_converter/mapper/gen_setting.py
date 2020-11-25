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
"""Operation mapping setting."""
from collections import namedtuple
import numpy as np

from mindinsight.mindconverter.graph_based_converter.constant import InputType

Tensor = namedtuple("Tensor", ["shape", "dtype", "reference"])

Setting = namedtuple("Setting", ["opt_vars_suffix",
                                 "op_ipt_type",
                                 "op_extra_input",
                                 "op_extra_tensor"])
Setting.__new__.__defaults__ = ("_opt", InputType.TENSOR.value, dict(), None)


def get_dtype(tensor: np.ndarray):
    """Get tensor dtype."""
    if tensor.dtype == np.float16:
        return "mindspore.float16"
    return "mindspore.float32"
