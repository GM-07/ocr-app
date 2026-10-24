"""Top-to-bottom, then left-to-right order for recognized blocks."""

from __future__ import annotations

import statistics
from collections.abc import Sequence

from ocr_app.domain.models import TextBlock


def ordered_blocks(blocks: Sequence[TextBlock]) -> list[TextBlock]:
    """Return blocks in reading order, dropping empty text."""
    return [block for line in group_lines(blocks) for block in line]


def render_pages(pages: Sequence[Sequence[TextBlock]]) -> str:
    """Join pages with a blank line. Lines within a page use reading order."""
    if not pages:
        return ""
    return "\n\n".join(render_blocks(page) for page in pages)


def render_blocks(blocks: Sequence[TextBlock]) -> str:
    """Join words on the same line with spaces and lines with newlines."""
    rendered: list[str] = []
    for line in group_lines(blocks):
        words = [block.text.strip() for block in line if block.text.strip()]
        if words:
            rendered.append(" ".join(words))
    return "\n".join(rendered)


def group_lines(blocks: Sequence[TextBlock]) -> list[list[TextBlock]]:
    """Cluster blocks into visual lines, each line sorted left to right."""
    usable = [block for block in blocks if block.text.strip()]
    if not usable:
        return []
    ordered = sorted(usable, key=lambda block: (block.bbox.y_min, block.bbox.x_min))
    heights = [block.bbox.height for block in ordered if block.bbox.height > 0]
    tolerance = max(8.0, (statistics.median(heights) if heights else 12.0) * 0.5)
    lines: list[list[TextBlock]] = [[ordered[0]]]
    anchor_y = ordered[0].bbox.y_min
    for block in ordered[1:]:
        if abs(block.bbox.y_min - anchor_y) <= tolerance:
            lines[-1].append(block)
        else:
            lines.append([block])
            anchor_y = block.bbox.y_min
    return [sorted(line, key=lambda block: block.bbox.x_min) for line in lines]
