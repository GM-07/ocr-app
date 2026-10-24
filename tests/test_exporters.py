"""Exporters write a real PDF and a real Word file from sample blocks."""

from pathlib import Path

from ocr_app.domain.models import BBox, TextBlock
from ocr_app.infrastructure.docx_exporter import DocxExporter
from ocr_app.infrastructure.fonts import dejavu_path
from ocr_app.infrastructure.pdf_exporter import PdfExporter
from tests.helpers import docx_text, pdf_text


def _sample_blocks() -> list[TextBlock]:
    return [
        TextBlock("Café", 0.99, BBox(0, 0, 40, 12)),
        TextBlock("déjà vu", 0.91, BBox(0, 24, 80, 36)),
    ]


def test_pdf_and_docx_exporters_write_non_empty_unicode_files(tmp_path: Path) -> None:
    blocks = _sample_blocks()
    pdf_path = tmp_path / "notes.pdf"
    docx_path = tmp_path / "notes.docx"

    PdfExporter().export([blocks], pdf_path)
    DocxExporter().export([blocks], docx_path)

    assert pdf_path.is_file() and pdf_path.stat().st_size > 0
    assert docx_path.is_file() and docx_path.stat().st_size > 0
    assert dejavu_path().name.encode() in pdf_path.read_bytes() or b"DejaVu" in pdf_path.read_bytes()

    written_pdf = pdf_text(pdf_path)
    written_docx = docx_text(docx_path)
    assert "Café" in written_pdf
    assert "déjà" in written_pdf
    assert written_docx == "Café\ndéjà vu"
