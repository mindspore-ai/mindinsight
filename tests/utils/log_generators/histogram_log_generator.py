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
"""Log generator for histogram data."""
import time

import numpy as np

from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2

from .log_generator import LogGenerator


class HistogramLogGenerator(LogGenerator):
    """
    Log generator for histogram data.

    This is a log generator writing histogram data. User can use it to generate fake
    summary logs about histogram.
    """

    def generate_event(self, values):
        """
        Method for generating histogram event.

        Args:
            values (dict): A dict contains:
                {
                    wall_time (float): Timestamp.
                    step (int): Train step.
                    value (float): Histogram value.
                    tag (str): Tag name.
                }

       Returns:
            summary_pb2.Event.

        """
        histogram_event = summary_pb2.Event()
        histogram_event.wall_time = values.get('wall_time')
        histogram_event.step = values.get('step')

        value = histogram_event.summary.value.add()
        value.tag = values.get('tag')

        buckets = values.get('buckets')
        for bucket in buckets:
            left, width, count = bucket
            bucket = value.histogram.buckets.add()
            bucket.left = left
            bucket.width = width
            bucket.count = count

        return histogram_event

    def generate_log(self, file_path, steps_list, tag_name):
        """
        Generate log for external calls.

        Args:
            file_path (str): Path to write logs.
            steps_list (list): A list consists of step.
            tag_name (str): Tag name.

        Returns:
            list[dict], generated histogram metadata.
            None, to be consistent with return value of HistogramGenerator.

        """
        histogram_metadata = []
        for step in steps_list:
            histogram = dict()

            wall_time = time.time()
            histogram.update({'wall_time': wall_time})
            histogram.update({'step': step})
            histogram.update({'tag': tag_name})

            # Construct buckets
            buckets = []
            leftmost = list(np.random.randn(11))
            leftmost.sort()
            for i in range(10):
                left = leftmost[i]
                width = leftmost[i+1] - left
                count = np.random.randint(20)
                bucket = [left, width, count]
                buckets.append(bucket)

            histogram.update({'buckets': buckets})
            histogram_metadata.append(histogram)

            self._write_log_one_step(file_path, histogram)

        return histogram_metadata, None


if __name__ == "__main__":
    histogram_log_generator = HistogramLogGenerator()
    test_file_name = '%s.%s.%s' % ('histogram', 'summary', str(time.time()))
    test_steps = [1, 3, 5]
    test_tag = "test_histogram_tag_name"
    histogram_log_generator.generate_log(test_file_name, test_steps, test_tag)
