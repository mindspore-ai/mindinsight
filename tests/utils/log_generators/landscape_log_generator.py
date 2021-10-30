# Copyright 2020-2021 Huawei Technologies Co., Ltd
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


class LandscapeLogGenerator(LogGenerator):
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
        landscape_event = summary_pb2.Event()
        landscape_event.wall_time = values.get('wall_time')
        landscape_event.step = values.get('step')

        value = landscape_event.summary.value.add()
        value.tag = values.get('tag')
        landscape = values.get('value')

        self.generate_point_event(value.loss_landscape.landscape, landscape)
        self.generate_point_event(value.loss_landscape.loss_path.points, landscape)
        self.generate_point_event(value.loss_landscape.convergence_point, landscape)
        value.loss_landscape.loss_path.intervals[:] = landscape.get("intervals")
        value.loss_landscape.metadata.decomposition = landscape.get("decomposition")
        value.loss_landscape.metadata.unit = landscape.get("unit")
        value.loss_landscape.metadata.step_per_epoch = landscape.get("step_per_epoch")

        return landscape_event

    def generate_point_event(self, point, value):
        """Generate point event."""
        self.generate_tensor_event(point.x, value.get('x'))
        self.generate_tensor_event(point.y, value.get('y'))
        self.generate_tensor_event(point.z, value.get('z'))

    @staticmethod
    def generate_tensor_event(tensor, value):
        """Generate tensor event."""
        tensor.dims[:] = value.get('dims')
        tensor.data_type = value.get('data_type')
        tensor.float_data[:] = value.get('float_data')

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
        landscape_metadata = []
        dims = list(np.random.randint(1, 10, 4))
        mul_value = reduce(mul, dims)
        x = {
            "dims": dims,
            "data_type": anf_ir_pb2.DataType.DT_FLOAT32,
            "float_data": np.random.randn(mul_value)
        }
        y = x
        z = x

        landscape = dict()

        wall_time = time.time()
        landscape.update({'wall_time': wall_time})
        landscape.update({'step': steps_list[-1]})
        landscape.update({'tag': tag_name})

        landscape.update({
            'value': {
                "x": x,
                "y": y,
                "z": z,
                "intervals": [1, 3],
                "decomposition": "decomposition",
                "unit": "unit",
                "step_per_epoch": 3
            }
        })
        landscape_metadata.append(landscape)

        self._write_log_one_step(file_path, landscape)

        return landscape_metadata, None
