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
"""Image container."""
from mindinsight.datavisual.proto_files.mindinsight_summary_pb2 import Summary


class ImageContainer:
    """
    Container for image to allow pickling.

    Args:
        image_message (Summary.Image): Image proto buffer message.
    """
    def __init__(self, image_message: Summary.Image):
        self.height = image_message.height
        self.width = image_message.width
        self.colorspace = image_message.colorspace
        self.encoded_image = image_message.encoded_image
