"""PIL conversions shared by the file loaders."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageOps


def to_rgb_array(image: Image.Image) -> np.ndarray:
    """Honor EXIF orientation and return a contiguous RGB uint8 array.

    Transparency is flattened onto white so text stays dark-on-light.
    """
    oriented = ImageOps.exif_transpose(image)
    if oriented is None:
        oriented = image
    if oriented.mode == "RGBA" or (
        oriented.mode == "P" and "transparency" in oriented.info
    ):
        rgba = oriented.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgb = background
    else:
        rgb = oriented.convert("RGB")
    return np.ascontiguousarray(rgb, dtype=np.uint8)
