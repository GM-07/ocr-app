"""Write recognized text to a Word document."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from ocr_app.domain.models import TextBlock
from ocr_app.domain.reading_order import render_pages


class DocxExporter:
    """One .docx per document. The document XML is UTF-8."""

    def export(self, pages: list[list[TextBlock]], destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = render_pages(pages)
        lines = text.split("\n") if text else [""]
        document = Document()
        document.core_properties.title = destination.stem
        for line in lines:
            document.add_paragraph(line)
        document.save(destination)
