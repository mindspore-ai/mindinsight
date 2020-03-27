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
"""Log generator for images."""
import io
import time

import numpy as np
from PIL import Image
from tests.st.func.datavisual.utils.log_generators.log_generator import LogGenerator

from mindinsight.datavisual.proto_files import mindinsight_summary_pb2 as summary_pb2


class ImagesLogGenerator(LogGenerator):
    """
    Log generator for images.

    This is a log generator writing images. User can use it to generate fake
    summary logs about images.
    """

    def generate_event(self, values):
        """
        Method for generating image event.

        Args:
            values (dict): A dict contains:
                {
                    wall_time (float): Timestamp.
                    step (int): Train step.
                    image (np.array): Pixels tensor.
                    tag (str): Tag name.
                }

        Returns:
            summary_pb2.Event.

        """

        image_event = summary_pb2.Event()
        image_event.wall_time = values.get('wall_time')
        image_event.step = values.get('step')

        height, width, channel, image_string = self._get_image_string(values.get('image'))
        value = image_event.summary.value.add()
        value.tag = values.get('tag')
        value.image.height = height
        value.image.width = width
        value.image.colorspace = channel
        value.image.encoded_image = image_string

        return image_event

    def _get_image_string(self, image_tensor):
        """
        Generate image string from tensor.

        Args:
            image_tensor (np.array): Pixels tensor.

        Returns:
            int, height.
            int, width.
            int, channel.
            bytes, image_string.

        """
        height, width, channel = image_tensor.shape
        scaled_height = int(height)
        scaled_width = int(width)

        image = Image.fromarray(image_tensor)
        image = image.resize((scaled_width, scaled_height), Image.ANTIALIAS)
        output = io.BytesIO()
        image.save(output, format='PNG')
        image_string = output.getvalue()
        output.close()
        return height, width, channel, image_string

    def _make_image_tensor(self, shape):
        """
        Make image tensor according to shape.

        Args:
            shape (list): Shape of image, consists of height, width, channel.

        Returns:
            np.array, image tensor.

        """
        image = np.prod(shape)
        image_tensor = (np.arange(image, dtype=float)).reshape(shape)
        image_tensor = image_tensor / np.max(image_tensor) * 255
        image_tensor = image_tensor.astype(np.uint8)

        return image_tensor

    def generate_log(self, file_path, steps_list, tag_name):
        """
        Generate log for external calls.

        Args:
            file_path (str): Path to write logs.
            steps_list (list): A list consists of step.
            tag_name (str): Tag name.

        Returns:
            list[dict], generated image metadata.
            dict, generated image tensors.

        """

        images_values = dict()
        images_metadata = []
        for step in steps_list:
            wall_time = time.time()

            # height, width, channel
            image_tensor = self._make_image_tensor([5, 5, 3])

            image_metadata = dict()
            image_metadata.update({'wall_time': wall_time})
            image_metadata.update({'step': step})
            image_metadata.update({'height': image_tensor.shape[0]})
            image_metadata.update({'width': image_tensor.shape[1]})
            images_metadata.append(image_metadata)
            images_values.update({step: image_tensor})

            values = dict(
                wall_time=wall_time,
                step=step,
                image=image_tensor,
                tag=tag_name
            )

            self._write_log_one_step(file_path, values)

        return images_metadata, images_values


if __name__ == "__main__":
    images_log_generator = ImagesLogGenerator()
    test_file_name = '%s.%s.%s' % ('image', 'summary', str(time.time()))
    test_steps = [1, 3, 5]
    test_tags = "test_image_tag_name"
    images_log_generator.generate_log(test_file_name, test_steps, test_tags)
