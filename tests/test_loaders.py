"""Tiny PDF and GIF fixtures load as ordered RGB pages."""

from pathlib import Path

import numpy as np
from PIL import Image
from reportlab.pdfgen import canvas

from ocr_app.infrastructure.loaders import DocumentLoader


def _write_gif(path: Path) -> None:
    frames = [
        Image.new("RGB", (12, 8), (255, 0, 0)),
        Image.new("RGB", (12, 8), (0, 255, 0)),
    ]
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=80,
        loop=0,
        format="GIF",
    )


def _write_pdf(path: Path, pages: int) -> None:
    writer = canvas.Canvas(str(path), pagesize=(72, 72))
    for index in range(pages):
        writer.drawString(18, 36, f"p{index}")
        if index < pages - 1:
            writer.showPage()
    writer.save()


def test_tiny_gif_loads_rgb_frames_in_order(tmp_path: Path) -> None:
    path = tmp_path / "frames.gif"
    _write_gif(path)
    document = DocumentLoader().load(path)

    assert len(document.pages) >= 1
    assert len(document.pages) == 2
    first, second = (page.image for page in document.pages)
    assert first.shape[2] == 3 and second.shape[2] == 3
    assert first.dtype == np.uint8
    assert int(first[:, :, 0].mean()) > int(first[:, :, 1].mean())
    assert int(second[:, :, 1].mean()) > int(second[:, :, 0].mean())


def test_tiny_pdf_loads_an_rgb_page_at_about_300_dpi(tmp_path: Path) -> None:
    path = tmp_path / "page.pdf"
    _write_pdf(path, pages=1)
    document = DocumentLoader().load(path)

    assert len(document.pages) >= 1
    image = document.pages[0].image
    assert image.ndim == 3 and image.shape[2] == 3
    assert image.dtype == np.uint8
    # A 72-point page at 300 DPI is 300 px on each side.
    assert 295 <= image.shape[0] <= 305
    assert 295 <= image.shape[1] <= 305


def test_multipage_pdf_keeps_page_order(tmp_path: Path) -> None:
    path = tmp_path / "two.pdf"
    _write_pdf(path, pages=2)
    document = DocumentLoader().load(path)
    assert [page.index for page in document.pages] == [0, 1]
    assert all(page.image.shape[2] == 3 for page in document.pages)


def test_jpeg_exif_orientation_is_applied(tmp_path: Path) -> None:
    path = tmp_path / "turned.jpg"
    image = Image.new("RGB", (60, 20), (0, 0, 255))
    exif = Image.Exif()
    exif[274] = 6  # 90 degrees clockwise; width and height swap on load
    image.save(path, format="JPEG", exif=exif)

    loaded = DocumentLoader().load(path).pages[0].image
    assert loaded.shape[0] == 60
    assert loaded.shape[1] == 20
    assert loaded.shape[2] == 3
