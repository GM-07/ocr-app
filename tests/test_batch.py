"""Selecting files replaces the batch. A camera frame is added to it."""

from pathlib import Path

import numpy as np

from ocr_app.presentation.batch import DocumentBatch


def test_selecting_files_replaces_the_current_batch() -> None:
    batch = DocumentBatch()
    batch.add_camera_frame(np.zeros((4, 4, 3), dtype=np.uint8))
    batch.replace_with_files([Path("scans/a.png"), Path("scans/b.pdf")])

    assert [item.name for item in batch.items] == ["a", "b"]
    assert all(item.image is None for item in batch.items)
    assert [item.path.name for item in batch.items] == ["a.png", "b.pdf"]


def test_camera_frame_is_added_without_clearing_files() -> None:
    batch = DocumentBatch()
    batch.replace_with_files([Path("a.png")])
    batch.add_camera_frame(np.zeros((2, 2, 3), dtype=np.uint8))

    assert len(batch.items) == 2
    assert batch.items[1].name == "camera-1"
    assert batch.items[1].image is not None
