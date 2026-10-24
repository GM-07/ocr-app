"""Blocks are ordered top-to-bottom, then left-to-right."""

from ocr_app.domain.models import BBox, TextBlock
from ocr_app.domain.reading_order import render_blocks


def test_reading_order_joins_a_line_then_moves_down() -> None:
    blocks = [
        TextBlock("right", 0.9, BBox(80, 1, 120, 14)),
        TextBlock("below", 0.9, BBox(0, 40, 40, 54)),
        TextBlock("left", 0.9, BBox(0, 0, 30, 12)),
    ]
    assert render_blocks(blocks) == "left right\nbelow"
