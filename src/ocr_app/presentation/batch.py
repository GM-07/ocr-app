"""The document list the window shows. Selecting files replaces it."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from ocr_app.application.extract_text import InputDocument


class DocumentBatch:
    """Files and camera frames waiting for extraction."""

    def __init__(self) -> None:
        self._items: list[InputDocument] = []
        self._camera_count = 0

    @property
    def items(self) -> list[InputDocument]:
        return list(self._items)

    def replace_with_files(self, paths: Sequence[Path]) -> None:
        """A new selection replaces the current batch, including camera frames."""
        self._items = [
            InputDocument(name=Path(path).stem, path=Path(path)) for path in paths
        ]

    def add_camera_frame(self, image: np.ndarray) -> InputDocument:
        self._camera_count += 1
        item = InputDocument(name=f"camera-{self._camera_count}", image=image)
        self._items.append(item)
        return item
