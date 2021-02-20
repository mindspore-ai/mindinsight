# Copyright 2021 Huawei Technologies Co., Ltd
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

"""Utility functions for hierarchcial occlusion image generation."""

import re

import PIL
from PIL import ImageDraw, ImageEnhance, ImageFilter

MASK_GAUSSIAN_RE = r'^gaussian:(\d+)$'


class EditStep:
    """
    Class that represents an edit step.

    Args:
        layer (int): Layer index.
        x (int): Left pixel coordinate.
        y (int): Top pixel coordinate.
        width (int): Width in pixels.
        height (int): Height in pixels.
    """
    def __init__(self,
                 layer: int,
                 x: int,
                 y: int,
                 width: int,
                 height: int):
        self.layer = layer
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def to_coord_box(self):
        """
        Convert to pixel coordinate box.

        Returns:
            tuple[int, int, int, int], tuple of left, top, right, bottom pixel coordinate.
        """
        return self.x, self.y, self.x + self.width, self.y + self.height


def pil_apply_edit_steps(image, mask, edit_steps, by_masking=False, inplace=False):
    """
    Apply edit steps on a PIL image.

    Args:
        image (PIL.Image): The input image in RGB mode.
        mask (Union[str, int, tuple[int, int, int], PIL.Image.Image]): The mask to apply on the image, could be string
            e.g. 'gaussian:9', a single, grey scale intensity [0, 255], an RBG tuple or a PIL Image object.
        edit_steps (list[EditStep]): Edit steps to be drawn.
        by_masking (bool): Whether to use masking method. Default: False.
        inplace (bool): True to draw on the input image, otherwise draw on a cloned image.

    Returns:
        PIL.Image, the result image.
    """
    if isinstance(mask, str):
        mask = pil_compile_str_mask(mask, image)
    if by_masking:
        return _pil_apply_edit_steps_mask(image, mask, edit_steps, inplace)
    return _pil_apply_edit_steps_unmask(image, mask, edit_steps, inplace)


def pil_compile_str_mask(mask, image):
    """Concert string mask to PIL Image."""
    match = re.match(MASK_GAUSSIAN_RE, mask)
    if match:
        radius = int(match.group(1))
        if radius > 0:
            image_filter = ImageFilter.GaussianBlur(radius=radius)
            mask_image = image.filter(image_filter)
            mask_image = ImageEnhance.Brightness(mask_image).enhance(0.7)
            mask_image = ImageEnhance.Color(mask_image).enhance(0.0)
            return mask_image
    raise ValueError(f"Invalid string mask: '{mask}'.")


def _pil_apply_edit_steps_unmask(image, mask, edit_steps, inplace=False):
    """
    Apply edit steps from unmasking method on a PIL image.

    Args:
        image (PIL.Image): The input image.
        mask (Union[int, tuple[int, int, int], PIL.Image]): The mask to apply on the image, could be a single grey
            scale intensity [0, 255], an RBG tuple or a PIL Image.
        edit_steps (list[EditStep]): Edit steps to be drawn.
        inplace (bool): True to draw on the input image, otherwise draw on a cloned image.

    Returns:
        PIL.Image, the result image.
    """
    if isinstance(mask, PIL.Image.Image):
        if inplace:
            bg = mask
        else:
            bg = mask.copy()
    else:
        if inplace:
            raise ValueError('Argument inplace cannot be True when mask is not a PIL Image.')
        if isinstance(mask, int):
            mask = (mask, mask, mask)
        bg = PIL.Image.new(mode="RGB", size=image.size, color=mask)

    for step in edit_steps:
        box = step.to_coord_box()
        cropped = image.crop(box)
        bg.paste(cropped, box=box)
    return bg


def _pil_apply_edit_steps_mask(image, mask, edit_steps, inplace=False):
    """
    Apply edit steps from unmasking method on a PIL image.

    Args:
        image (PIL.Image): The input image.
        mask (Union[int, tuple[int, int, int], PIL.Image]): The mask to apply on the image, could be a single grey
            scale intensity [0, 255], an RBG tuple or a PIL Image.
        edit_steps (list[EditStep]): Edit steps to be drawn.
        inplace (bool): True to draw on the input image, otherwise draw on a cloned image.

    Returns:
        PIL.Image, the result image.
    """
    if not inplace:
        image = image.copy()

    if isinstance(mask, PIL.Image.Image):
        for step in edit_steps:
            box = step.to_coord_box()
            cropped = mask.crop(box)
            image.paste(cropped, box=box)
    else:
        if isinstance(mask, int):
            mask = (mask, mask, mask)
        draw = ImageDraw.Draw(image)
        for step in edit_steps:
            draw.rectangle(step.to_coord_box(), fill=mask)
    return image
