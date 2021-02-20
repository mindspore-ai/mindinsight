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
"""Datafile encapsulator."""

import io
import os

import numpy as np
from PIL import Image

from mindinsight.datavisual.common.exceptions import ImageNotExistError
from mindinsight.explainer.common.enums import ImageQueryTypes
from mindinsight.explainer.encapsulator._hoc_pil_apply import EditStep, pil_apply_edit_steps
from mindinsight.explainer.encapsulator.explain_data_encap import ExplainDataEncap
from mindinsight.utils.exceptions import FileSystemPermissionError
from mindinsight.utils.exceptions import UnknownError

# Max uint8 value. for converting RGB pixels to [0,1] intensity.
_UINT8_MAX = 255

# Color of low saliency.
_SALIENCY_CMAP_LOW = (55, 25, 86, 255)

# Color of high saliency.
_SALIENCY_CMAP_HI = (255, 255, 0, 255)

# Channel modes.
_SINGLE_CHANNEL_MODE = "L"
_RGBA_MODE = "RGBA"
_RGB_MODE = "RGB"

_PNG_FORMAT = "PNG"


def _clean_train_id_b4_join(train_id):
    """Clean train_id before joining to a path."""
    if train_id.startswith("./") or train_id.startswith(".\\"):
        return train_id[2:]
    return train_id


class DatafileEncap(ExplainDataEncap):
    """Datafile encapsulator."""

    def query_image_binary(self, train_id, image_path, image_type):
        """
        Query image binary content.

        Args:
            train_id (str): Job ID.
            image_path (str): Image path relative to explain job's summary directory.
            image_type (str): Image type, Options: 'original', 'overlay' or 'outcome'.

        Returns:
            bytes, image binary content for UI to demonstrate.
        """
        if image_type == ImageQueryTypes.OUTCOME.value:
            return self._get_hoc_image(image_path, train_id)

        abs_image_path = os.path.join(self.job_manager.summary_base_dir,
                                      _clean_train_id_b4_join(train_id),
                                      image_path)

        if self._is_forbidden(abs_image_path):
            raise FileSystemPermissionError("Forbidden.")

        try:

            if image_type != ImageQueryTypes.OVERLAY.value:
                # no need to convert
                with open(abs_image_path, "rb") as fp:
                    return fp.read()

            image = Image.open(abs_image_path)

            if image.mode == _RGBA_MODE:
                # It is RGBA already, do not convert.
                with open(abs_image_path, "rb") as fp:
                    return fp.read()

        except FileNotFoundError:
            raise ImageNotExistError(f"train_id:{train_id} path:{image_path} type:{image_type}")
        except PermissionError:
            raise FileSystemPermissionError(f"train_id:{train_id} path:{image_path} type:{image_type}")
        except OSError:
            raise UnknownError(f"Invalid image file: train_id:{train_id} path:{image_path} type:{image_type}")

        if image.mode == _SINGLE_CHANNEL_MODE:
            saliency = np.asarray(image) / _UINT8_MAX
        elif image.mode == _RGB_MODE:
            saliency = np.asarray(image)
            saliency = saliency[:, :, 0] / _UINT8_MAX
        else:
            raise UnknownError(f"Invalid overlay image mode:{image.mode}.")

        saliency_stack = np.empty((saliency.shape[0], saliency.shape[1], 4))
        for c in range(3):
            saliency_stack[:, :, c] = saliency
        rgba = saliency_stack * _SALIENCY_CMAP_HI
        rgba += (1 - saliency_stack) * _SALIENCY_CMAP_LOW
        rgba[:, :, 3] = saliency * _UINT8_MAX

        overlay = Image.fromarray(np.uint8(rgba), mode=_RGBA_MODE)
        buffer = io.BytesIO()
        overlay.save(buffer, format=_PNG_FORMAT)

        return buffer.getvalue()

    def _is_forbidden(self, path):
        """Check if the path is outside summary base dir."""
        base_dir = os.path.realpath(self.job_manager.summary_base_dir)
        path = os.path.realpath(path)
        return not path.startswith(base_dir)

    def _get_hoc_image(self, image_path, train_id):
        """Get hoc image for image data demonstration in UI."""

        sample_id, label, layer = image_path.strip(".jpg").split("_")
        layer = int(layer)
        job = self.job_manager.get_job(train_id)
        samples = job.samples
        label_idx = job.labels.index(label)

        chosen_sample = samples[int(sample_id)]
        original_path_image = chosen_sample['image']
        abs_image_path = os.path.join(self.job_manager.summary_base_dir, _clean_train_id_b4_join(train_id),
                                      original_path_image)
        if self._is_forbidden(abs_image_path):
            raise FileSystemPermissionError("Forbidden.")

        image_type = ImageQueryTypes.OUTCOME.value
        try:
            image = Image.open(abs_image_path)
        except FileNotFoundError:
            raise ImageNotExistError(f"train_id:{train_id} path:{image_path} type:{image_type}")
        except PermissionError:
            raise FileSystemPermissionError(f"train_id:{train_id} path:{image_path} type:{image_type}")
        except OSError:
            raise UnknownError(f"Invalid image file: train_id:{train_id} path:{image_path} type:{image_type}")

        edit_steps = []
        boxes = chosen_sample["hierarchical_occlusion"][label_idx]["hoc_layers"][layer]["boxes"]
        mask = chosen_sample["hierarchical_occlusion"][label_idx]["mask"]

        for box in boxes:
            edit_steps.append(EditStep(layer, *box))
        image_cp = pil_apply_edit_steps(image, mask, edit_steps)
        buffer = io.BytesIO()
        image_cp.save(buffer, format=_PNG_FORMAT)

        return buffer.getvalue()
