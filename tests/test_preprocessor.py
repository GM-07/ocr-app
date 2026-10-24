"""The preprocessor must survive a small image and keep three channels."""

import numpy as np

from ocr_app.infrastructure.preprocessor import ImagePreprocessor


def test_preprocess_small_rgb_returns_three_channels() -> None:
    image = np.full((40, 64, 3), 240, dtype=np.uint8)
    image[8:24, 6:30] = (0, 0, 0)
    result = ImagePreprocessor().process(image)

    assert result.dtype == np.uint8
    assert result.ndim == 3
    assert result.shape[2] == 3
    assert min(result.shape[:2]) >= 1500


def test_preprocess_expands_grayscale_to_three_channels() -> None:
    image = np.full((36, 36), 255, dtype=np.uint8)
    image[4:20, 4:28] = 0
    result = ImagePreprocessor().process(image)

    assert result.ndim == 3
    assert result.shape[2] == 3
    assert result.dtype == np.uint8
