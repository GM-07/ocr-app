"""Write recognized text to a PDF with DejaVu embedded."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from ocr_app.domain.models import TextBlock
from ocr_app.domain.reading_order import render_pages
from ocr_app.infrastructure.fonts import dejavu_font_name, dejavu_path

_registered = False


class PdfExporter:
    """One PDF per document. Accents survive because DejaVu is embedded."""

    def export(self, pages: list[list[TextBlock]], destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        font = _register_dejavu()
        text = render_pages(pages)
        style = ParagraphStyle(
            "ExtractedBody",
            fontName=font,
            fontSize=11,
            leading=15,
        )
        story: list[Paragraph | Spacer] = []
        lines = text.split("\n") if text else [""]
        for line in lines:
            if line:
                story.append(Paragraph(escape(line), style))
            else:
                story.append(Spacer(1, 12))
        document = SimpleDocTemplate(
            str(destination),
            pagesize=A4,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
            title=destination.stem,
        )
        document.build(story)


def _register_dejavu() -> str:
    global _registered
    name = dejavu_font_name()
    if not _registered:
        pdfmetrics.registerFont(TTFont(name, str(dejavu_path())))
        _registered = True
    return name
