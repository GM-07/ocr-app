"""Composition root. This is the only place that wires concrete adapters."""

from __future__ import annotations

import logging

from ocr_app.application.extract_text import ExtractText
from ocr_app.application.ports import Reader
from ocr_app.domain.models import ExportFormat
from ocr_app.infrastructure.docx_exporter import DocxExporter
from ocr_app.infrastructure.easyocr_reader import EasyOcrReader
from ocr_app.infrastructure.loaders import DocumentLoader
from ocr_app.infrastructure.pdf_exporter import PdfExporter
from ocr_app.infrastructure.preprocessor import ImagePreprocessor
from ocr_app.settings import OCR_LANGUAGES


def build_reader() -> EasyOcrReader:
    return EasyOcrReader(languages=OCR_LANGUAGES)


def build_extract_text(reader: Reader) -> ExtractText:
    return ExtractText(
        reader=reader,
        preprocessor=ImagePreprocessor(),
        loader=DocumentLoader(),
        exporters={
            ExportFormat.PDF: PdfExporter(),
            ExportFormat.DOCX: DocxExporter(),
        },
    )


def main() -> None:
    """Open the desktop window. The command-line tool does not call this."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    # Imported here so `ocr` can run on a machine without Tk.
    from ocr_app.infrastructure.camera import OpenCvCamera
    from ocr_app.presentation.main_window import MainWindow

    window = MainWindow(
        reader_factory=build_reader,
        extract_factory=build_extract_text,
        camera=OpenCvCamera(),
    )
    window.run()
