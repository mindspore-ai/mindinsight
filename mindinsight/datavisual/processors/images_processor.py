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
"""Image Processor APIs."""
from mindinsight.datavisual.utils.tools import to_int
from mindinsight.utils.exceptions import ParamValueError
from mindinsight.datavisual.common.validation import Validation
from mindinsight.datavisual.common.exceptions import ImageNotExistError
from mindinsight.datavisual.processors.base_processor import BaseProcessor


class ImageProcessor(BaseProcessor):
    """Image Processor."""

    def get_metadata_list(self, train_id, tag):
        """
        Builds a JSON-serializable object with information about images.

        Args:
            train_id (str): The ID of the events data.
            tag (str): The name of the tag the images all belong to.

        Returns:
            list[dict], a list of dictionaries containing the `wall_time`, `step`, `width`,
                and `height` for each image.
                    [
                        {
                            "wall_time": ****,
                            "step": ****,
                            "width": ****,
                            "height": ****,
                        },
                        {...}
                    ]

        """
        Validation.check_param_empty(train_id=train_id, tag=tag)
        result = []
        try:
            tensors = self._data_manager.list_tensors(train_id, tag)
        except ParamValueError as ex:
            raise ImageNotExistError(ex.message)

        for tensor in tensors:
            # no tensor_proto in TensorEvent
            (width, height) = (tensor.value.width, tensor.value.height)
            result.append({
                'wall_time': tensor.wall_time,
                'step': tensor.step,
                'width': int(width),
                'height': int(height),
            })
        return dict(metadatas=result)

    def get_single_image(self, train_id, tag, step):
        """
        Returns the actual image bytes for a given image.

        Args:
            train_id (str): The ID of the events data the image belongs to.
            tag (str): The name of the tag the images belongs to.
            step (int): The step of the image in the current reservoir. If step = -1, return image of final step.

        Returns:
            bytes, a byte string of the raw image bytes.

        """
        Validation.check_param_empty(train_id=train_id, tag=tag, step=step)
        step = to_int(step, "step")

        try:
            tensors = self._data_manager.list_tensors(train_id, tag)
        except ParamValueError as ex:
            raise ImageNotExistError(ex.message)

        image = _find_image(tensors, step)
        if image is None:
            raise ImageNotExistError("Can not find the step with given train job id and tag.")

        return image


def _find_image(tensors, step):
    """Find the specific image by step from tensors. If step = -1, return image of final step."""
    if not tensors:
        return None
    if step == -1:
        return tensors[-1].value.encoded_image
    for tensor in tensors:
        if tensor.step == step:
            # Default value for bytes field is empty byte string normally,
            # see also "Optional Fields And Default Values" in protobuf
            # documentation.
            return tensor.value.encoded_image
    return None
