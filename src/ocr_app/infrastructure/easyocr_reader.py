"""EasyOCR adapter.

The library is imported inside the constructor so importing this module does
not download recognition models. The window constructs the reader on a
background thread.
"""

from __future__ import annotations

from collections.abc import Sequence

import cv2
import numpy as np

from ocr_app.domain.models import BBox, TextBlock
from ocr_app.rgb import ensure_rgb_uint8
from ocr_app.settings import OCR_LANGUAGES


class EasyOcrReader:
    """Recognize text with EasyOCR. The language list comes from settings."""

    def __init__(
        self,
        languages: Sequence[str] = OCR_LANGUAGES,
        gpu: bool = False,
    ) -> None:
        try:
            import easyocr
        except ImportError as exc:
            raise RuntimeError(
                "EasyOCR is not installed. Install the project dependencies and try again."
            ) from exc
        self._engine = easyocr.Reader(list(languages), gpu=gpu, verbose=False)

    def read(self, image: np.ndarray) -> list[TextBlock]:
        rgb = ensure_rgb_uint8(image)
        # EasyOCR treats a 3-channel array as BGR and converts it with
        # COLOR_BGR2GRAY. Pass BGR. Never pass a single-channel matrix.
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        raw = self._engine.readtext(bgr, detail=1, paragraph=False)
        blocks: list[TextBlock] = []
        for entry in raw:
            if len(entry) < 3:
                continue
            points, text, confidence = entry[0], entry[1], entry[2]
            blocks.append(
                TextBlock(
                    text=str(text),
                    confidence=float(confidence),
                    bbox=_bbox_from_points(points),
                )
            )
        return blocks


def _bbox_from_points(points: Sequence[Sequence[float]]) -> BBox:
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    if not xs or not ys:
        return BBox(0.0, 0.0, 0.0, 0.0)
    return BBox(min(xs), min(ys), max(xs), max(ys))
