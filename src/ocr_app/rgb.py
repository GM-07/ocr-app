"""Convert arrays to the 3-channel RGB images the recognizer expects."""

from __future__ import annotations

import numpy as np


def ensure_rgb_uint8(image: np.ndarray) -> np.ndarray:
    """Return a contiguous HxWx3 uint8 image.

    Grayscale and alpha inputs are expanded here so recognition never receives
    a single-channel matrix.
    """
    if not isinstance(image, np.ndarray):
        raise TypeError("Expected an image array")
    if image.size == 0:
        raise ValueError("Image has no pixels")

    if image.ndim == 2:
        expanded = np.stack((image, image, image), axis=-1)
    elif image.ndim == 3 and image.shape[2] == 1:
        expanded = np.repeat(image, 3, axis=2)
    elif image.ndim == 3 and image.shape[2] == 4:
        color = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        white = np.full_like(color, 255.0)
        expanded = color * alpha + white * (1.0 - alpha)
    elif image.ndim == 3 and image.shape[2] == 3:
        expanded = image
    else:
        raise ValueError(f"Expected an image array, got shape {image.shape}")

    if expanded.dtype != np.uint8:
        expanded = np.clip(expanded, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(expanded)
