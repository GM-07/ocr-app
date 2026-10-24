"""Upscale, denoise, contrast-stretch, and deskew a page before OCR."""

from __future__ import annotations

import math

import cv2
import numpy as np

from ocr_app.rgb import ensure_rgb_uint8
from ocr_app.settings import DESKEW_MAX_DEGREES, DESKEW_MIN_DEGREES, MIN_SHORT_SIDE_PX


class ImagePreprocessor:
    """Turn a page into a 3-channel image that is easier to recognize."""

    def __init__(self, min_short_side: int = MIN_SHORT_SIDE_PX) -> None:
        self._min_short_side = min_short_side

    def process(self, image: np.ndarray) -> np.ndarray:
        rgb = ensure_rgb_uint8(image)
        rgb = self._upscale(rgb)
        rgb = self._denoise(rgb)
        rgb = self._clahe(rgb)
        rgb = self._deskew(rgb)
        rgb = ensure_rgb_uint8(rgb)
        if rgb.ndim != 3 or rgb.shape[2] != 3:
            raise RuntimeError("Preprocessor must return a 3-channel image")
        return rgb

    def _upscale(self, image: np.ndarray) -> np.ndarray:
        height, width = image.shape[:2]
        short_side = min(height, width)
        if short_side >= self._min_short_side:
            return image
        scale = self._min_short_side / short_side
        return cv2.resize(
            image,
            (max(1, int(round(width * scale))), max(1, int(round(height * scale)))),
            interpolation=cv2.INTER_CUBIC,
        )

    def _denoise(self, image: np.ndarray) -> np.ndarray:
        # Edge-preserving denoise. Colored NL-means is stronger but too slow
        # once a short page has been scaled up for recognition.
        if min(image.shape[:2]) < 3:
            return image
        return cv2.bilateralFilter(image, d=5, sigmaColor=35, sigmaSpace=35)

    def _clahe(self, image: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        lightness, green_red, blue_yellow = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        stretched = clahe.apply(lightness)
        merged = cv2.merge((stretched, green_red, blue_yellow))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        try:
            angle = _skew_angle(image)
        except cv2.error:
            return image
        if angle is None or abs(angle) < DESKEW_MIN_DEGREES or abs(angle) > DESKEW_MAX_DEGREES:
            return image
        height, width = image.shape[:2]
        matrix = cv2.getRotationMatrix2D((width / 2.0, height / 2.0), angle, 1.0)
        return cv2.warpAffine(
            image,
            matrix,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )


def _skew_angle(image: np.ndarray) -> float | None:
    """Estimate skew in degrees. ``None`` means there is nothing to measure."""
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    inverted = cv2.bitwise_not(gray)
    _threshold, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    points = cv2.findNonZero(binary)
    if points is None or len(points) < 50:
        return None
    angle = float(cv2.minAreaRect(points)[-1])
    if not math.isfinite(angle):
        return None
    # minAreaRect reports [-90, 0). Fold that into a small correction.
    if angle < -45.0:
        angle = -(90.0 + angle)
    else:
        angle = -angle
    if not math.isfinite(angle):
        return None
    return angle
