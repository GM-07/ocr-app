"""Opening the window does not construct the OCR reader on the UI thread."""

import threading
import time

import pytest

from ocr_app.domain.models import ExportFormat
from ocr_app.presentation.main_window import MainWindow
from tests.helpers import FakeReader


class _IdleCamera:
    def capture(self):
        raise AssertionError("camera is not used while the window opens")


def test_window_opens_before_the_reader_is_constructed() -> None:
    pytest.importorskip("tkinter")
    caller = threading.current_thread()
    seen: list[threading.Thread] = []
    started = threading.Event()
    release = threading.Event()

    def factory() -> FakeReader:
        seen.append(threading.current_thread())
        started.set()
        if not release.wait(5):
            raise TimeoutError("reader factory was left blocked")
        return FakeReader([])

    def extract_factory(reader):
        raise AssertionError("extraction is not started while the window opens")

    started_at = time.perf_counter()
    window = MainWindow(
        reader_factory=factory,
        extract_factory=extract_factory,
        camera=_IdleCamera(),
    )
    try:
        elapsed = time.perf_counter() - started_at
        assert elapsed < 1.0
        window.update_idletasks()
        assert window.geometry().startswith("800x600")
        assert window.winfo_width() == 800
        assert window.winfo_height() == 600
        origin_x = window.winfo_rootx()
        origin_y = window.winfo_rooty()
        widgets = (*window._actions, window._status_label, window._files)
        for widget in widgets:
            right = widget.winfo_rootx() + widget.winfo_width() - origin_x
            bottom = widget.winfo_rooty() + widget.winfo_height() - origin_y
            assert 0 <= right <= 800
            assert 0 < bottom <= 600
        assert window.format_var.get() == ExportFormat.PDF.value
        assert "Loading OCR engine" in window._status_var.get()
        assert started.wait(2)
        assert seen and seen[0] is not caller
        assert seen[0].name == "ocr-engine"
        release.set()
        window._engine_thread.join(2)
        deadline = time.perf_counter() + 2
        while window._status_var.get() != "Ready" and time.perf_counter() < deadline:
            window.update()
            time.sleep(0.05)
        assert window._reader is not None
        assert window._status_var.get() == "Ready"
    finally:
        release.set()
        window._engine_thread.join(2)
        window.destroy()


def test_importing_the_app_does_not_import_easyocr() -> None:
    import sys

    import ocr_app.composition  # noqa: F401
    import ocr_app.infrastructure.easyocr_reader  # noqa: F401

    assert "easyocr" not in sys.modules
