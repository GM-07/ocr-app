"""OpenCV camera adapter. A missing camera is an error result, not an exception."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import cv2
import numpy as np

from ocr_app.application.ports import CameraCapture

_MISSING = "No camera is available."


class OpenCvCamera:
    """Capture one RGB frame from a video device."""

    def __init__(
        self,
        device_index: int = 0,
        opener: Callable[[int], cv2.VideoCapture] | None = None,
    ) -> None:
        self._index = device_index
        self._opener = opener if opener is not None else cv2.VideoCapture
        self._check_device_node = opener is None

    def capture(self) -> CameraCapture:
        if self._check_device_node and not _linux_device_exists(self._index):
            return CameraCapture(image=None, error=_MISSING)
        capture = None
        try:
            capture = self._opener(self._index)
            if capture is None or not capture.isOpened():
                return CameraCapture(image=None, error=_MISSING)
            ok, frame = capture.read()
            if not ok or frame is None:
                return CameraCapture(image=None, error=_MISSING)
            if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
                return CameraCapture(image=None, error="The camera returned an unexpected image.")
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return CameraCapture(image=np.ascontiguousarray(rgb), error=None)
        except Exception as exc:
            return CameraCapture(image=None, error=f"{_MISSING} {exc}")
        finally:
            if capture is not None:
                release = getattr(capture, "release", None)
                if callable(release):
                    try:
                        release()
                    except Exception:
                        pass


def _linux_device_exists(index: int) -> bool:
    if not sys.platform.startswith("linux"):
        return True
    return Path(f"/dev/video{index}").exists()
