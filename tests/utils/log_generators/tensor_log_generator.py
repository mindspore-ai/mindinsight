# Copyright 2020 Huawei Technologies Co., Ltd
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
# ============================================================================
"""Log generator for tensor data."""
import time

from operator import mul
from functools import reduce
import numpy as np
from mindinsight.datavisual.proto_files import mindinsight_anf_ir_pb2 as anf_ir_pb2
from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2

from .log_generator import LogGenerator


class TensorLogGenerator(LogGenerator):
    """
    Log generator for tensor data.

    This is a log generator writing tensor data. User can use it to generate fake
    summary logs about tensor.
    """

    def generate_event(self, values):
        """
        Method for generating tensor event.

        Args:
            values (dict): A dict contains:
                {
                    wall_time (float): Timestamp.
                    step (int): Train step.
                    value (float): Tensor value.
                    tag (str): Tag name.
                }

       Returns:
            summary_pb2.Event.

        """
        tensor_event = summary_pb2.Event()
        tensor_event.wall_time = values.get('wall_time')
        tensor_event.step = values.get('step')

        value = tensor_event.summary.value.add()
        value.tag = values.get('tag')
        tensor = values.get('value')

        value.tensor.dims[:] = tensor.get('dims')
        value.tensor.data_type = tensor.get('data_type')
        value.tensor.float_data[:] = tensor.get('float_data')
        print(tensor.get('float_data'))

        return tensor_event

    def generate_log(self, file_path, steps_list, tag_name):
        """
        Generate log for external calls.

        Args:
            file_path (str): Path to write logs.
            steps_list (list): A list consists of step.
            tag_name (str): Tag name.

        Returns:
            list[dict], generated tensor metadata.
            list, generated tensors.

        """
        tensor_metadata = []
        tensor_values = dict()
        for step in steps_list:
            tensor = dict()

            wall_time = time.time()
            tensor.update({'wall_time': wall_time})
            tensor.update({'step': step})
            tensor.update({'tag': tag_name})
            dims = list(np.random.randint(1, 10, 4))
            mul_value = reduce(mul, dims)
            tensor.update({'value': {
                "dims": dims,
                "data_type": anf_ir_pb2.DataType.DT_FLOAT32,
                "float_data": np.random.randn(mul_value)
            }})
            tensor_metadata.append(tensor)
            tensor_values.update({step: tensor})

            self._write_log_one_step(file_path, tensor)

        return tensor_metadata, tensor_values


if __name__ == "__main__":
    tensor_log_generator = TensorLogGenerator()
    test_file_name = '%s.%s.%s' % ('tensor', 'summary', str(time.time()))
    test_steps = [1, 3, 5]
    test_tag = "test_tensor_tag_name"
    tensor_log_generator.generate_log(test_file_name, test_steps, test_tag)
