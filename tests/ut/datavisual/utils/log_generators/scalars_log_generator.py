# Copyright 2019 Huawei Technologies Co., Ltd
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
"""Log generator for scalars."""
import time

import numpy as np

from tests.ut.datavisual.utils.log_generators.log_generator import LogGenerator

from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2


class ScalarsLogGenerator(LogGenerator):
    """
    Log generator for scalars.

    This is a log generator writing scalars. User can use it to generate fake
    summary logs about scalar.
    """

    def generate_event(self, values):
        """
        Method for generating scalar event.

        Args:
            values (dict): A dict contains:
                {
                    wall_time (float): Timestamp.
                    step (int): Train step.
                    value (float): Scalar value.
                    tag (str): Tag name.
                }


        Returns:
            summary_pb2.Event.

        """
        scalar_event = summary_pb2.Event()
        scalar_event.wall_time = values.get('wall_time')
        scalar_event.step = values.get('step')

        value = scalar_event.summary.value.add()
        value.tag = values.get('tag')
        value.scalar_value = values.get('value')

        return scalar_event

    def generate_log(self, file_path, steps_list, tag_name):
        """
        Generate log for external calls.

        Args:
            file_path (str): Path to write logs.
            steps_list (list): A list consists of step.
            tag_name (str): Tag name.

        Returns:
            list[dict], generated scalar metadata.
            None, to be consistent with return value of ImageGenerator.

        """
        scalars_metadata = []
        for step in steps_list:
            scalar_metadata = dict()

            wall_time = time.time()
            value = np.random.rand()

            scalar_metadata.update({'wall_time': wall_time})
            scalar_metadata.update({'step': step})
            scalar_metadata.update({'value': value})

            scalars_metadata.append(scalar_metadata)

            scalar_metadata.update({"tag": tag_name})

            self._write_log_one_step(file_path, scalar_metadata)

        return scalars_metadata, None


if __name__ == "__main__":
    scalars_log_generator = ScalarsLogGenerator()
    test_file_name = '%s.%s.%s' % ('scalar', 'summary', str(time.time()))
    test_steps = [1, 3, 5]
    test_tag = "test_scalar_tag_name"
    scalars_log_generator.generate_log(test_file_name, test_steps, test_tag)
