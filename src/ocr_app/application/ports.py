"""Ports the extract use case and the window depend on.

Infrastructure adapters implement these. The UI and the use case do not
import EasyOCR, OpenCV camera handles, or file writers directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np

from ocr_app.domain.models import Document, TextBlock


class Reader(Protocol):
    """Recognize text on one RGB image."""

    def read(self, image: np.ndarray) -> list[TextBlock]:
        """Return blocks for a HxWx3 RGB uint8 image."""


class Preprocessor(Protocol):
    """Prepare a page image for recognition."""

    def process(self, image: np.ndarray) -> np.ndarray:
        """Return a 3-channel RGB uint8 image."""


class DocumentLoader(Protocol):
    """Load a supported file into pages."""

    def load(self, path: Path) -> Document:
        """Load `path` or raise if it cannot be read."""


class Exporter(Protocol):
    """Write recognized pages to one output file."""

    def export(self, pages: list[list[TextBlock]], destination: Path) -> None:
        """Create `destination`, embedding Unicode text for every page."""


@dataclass
class CameraCapture:
    """One attempt to grab a frame. `error` is set when no frame is available."""

    image: np.ndarray | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.error is None and self.image is not None


class Camera(Protocol):
    """Capture a single frame. Missing hardware returns an error, it does not raise."""

    def capture(self) -> CameraCapture:
        """Return a frame or a message explaining why capture failed."""
