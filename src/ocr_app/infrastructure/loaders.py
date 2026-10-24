"""Load raster images, multi-frame GIFs, and PDF pages as RGB arrays."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image

from ocr_app.domain.models import Document, Page
from ocr_app.infrastructure.images import to_rgb_array
from ocr_app.settings import PDF_RENDER_DPI

RASTER_SUFFIXES = {".jpg", ".jpeg", ".png"}
GIF_SUFFIX = ".gif"
PDF_SUFFIX = ".pdf"


class ImageFileLoader:
    """JPG, JPEG, and PNG, with EXIF orientation applied."""

    def load_pages(self, path: Path) -> list[np.ndarray]:
        with Image.open(path) as image:
            return [to_rgb_array(image)]


class GifLoader:
    """Decode every GIF frame to RGB, in frame order."""

    def load_pages(self, path: Path) -> list[np.ndarray]:
        frames: list[np.ndarray] = []
        with Image.open(path) as image:
            frame_count = int(getattr(image, "n_frames", 1))
            for index in range(frame_count):
                image.seek(index)
                frames.append(to_rgb_array(image))
        return frames


class PdfLoader:
    """Rasterize PDF pages at 300 DPI without an external poppler install."""

    def __init__(self, dpi: int = PDF_RENDER_DPI) -> None:
        if dpi <= 0:
            raise ValueError("PDF render DPI must be positive")
        self._dpi = dpi

    def load_pages(self, path: Path) -> list[np.ndarray]:
        pdf = pdfium.PdfDocument(str(path))
        images: list[np.ndarray] = []
        try:
            scale = self._dpi / 72
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    bitmap = page.render(scale=scale)
                    try:
                        images.append(to_rgb_array(bitmap.to_pil()))
                    finally:
                        bitmap.close()
                finally:
                    page.close()
        finally:
            pdf.close()
        return images


class DocumentLoader:
    """Dispatch a path to the image, GIF, or PDF loader."""

    def __init__(
        self,
        images: ImageFileLoader | None = None,
        gifs: GifLoader | None = None,
        pdfs: PdfLoader | None = None,
    ) -> None:
        self._images = images or ImageFileLoader()
        self._gifs = gifs or GifLoader()
        self._pdfs = pdfs or PdfLoader()

    def load(self, path: Path) -> Document:
        if not path.is_file():
            raise FileNotFoundError(f"Cannot read {path}")
        suffix = path.suffix.lower()
        if suffix in RASTER_SUFFIXES:
            pages = self._images.load_pages(path)
        elif suffix == GIF_SUFFIX:
            pages = self._gifs.load_pages(path)
        elif suffix == PDF_SUFFIX:
            pages = self._pdfs.load_pages(path)
        else:
            raise ValueError(
                f"{path.name} is not a supported document. Use JPG, PNG, GIF, or PDF."
            )
        if not pages:
            raise ValueError(f"{path.name} has no pages.")
        return Document(
            name=path.stem,
            source=str(path),
            pages=[Page(index=index, image=image) for index, image in enumerate(pages)],
        )
