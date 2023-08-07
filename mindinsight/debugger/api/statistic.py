# Copyright 2023 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""TensorStatistic for DebuggerTensor."""


class TensorStatistic:
    """The tensor statistic class."""

    def __init__(self, op_type='', op_name='', task_id=0, stream_id=0, time_stamp=0,
                 io='', slot=0, data_size=0, data_type='', shape=(),
                 max_value=float('-inf'), min_value=float('inf'), avg_value=0, count=0,
                 negative_zero_count=0,
                 positive_zero_count=0, nan_count=0, negative_inf_count=0,
                 positive_inf_count=0, zero_count=0):
        self.op_type = op_type
        self.op_name = op_name
        self.task_id = task_id
        self.stream_id = stream_id
        self.time_stamp = time_stamp
        self.io = io
        self.slot = slot
        self.data_size = data_size
        self.data_type = data_type
        self.shape = shape
        self.max_value = max_value
        self.min_value = min_value
        self.avg_value = avg_value
        self.count = count
        self.negative_zero_count = negative_zero_count
        self.positive_zero_count = positive_zero_count
        self.nan_count = nan_count
        self.negative_inf_count = negative_inf_count
        self.positive_inf_count = positive_inf_count
        self.zero_count = zero_count


class SummaryStatistic:
    """The tensor statistic class."""

    def __init__(self, op_type='', op_name='', tensor_name='', inf_iterations=0, nan_iterations=0,
                 out_of_range_iterations=0, total_dump_iterations=0, normal_iterations=0):
        self.op_type = op_type
        self.op_name = op_name
        self.tensor_name = tensor_name
        self.inf_iterations = inf_iterations
        self.nan_iterations = nan_iterations
        self.out_of_range_iterations = out_of_range_iterations
        self.total_dump_iterations = total_dump_iterations
        self.normal_iterations = normal_iterations
