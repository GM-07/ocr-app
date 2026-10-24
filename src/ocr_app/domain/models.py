"""Documents, pages, and the text blocks recognized on them."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class ExportFormat(Enum):
    """File format written for each input document."""

    PDF = "pdf"
    DOCX = "docx"

    @property
    def extension(self) -> str:
        return f".{self.value}"


@dataclass(frozen=True)
class BBox:
    """Axis-aligned bounds of a recognized block, in image pixels."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)


@dataclass(frozen=True)
class TextBlock:
    """One recognized snippet and how confident the reader was."""

    text: str
    confidence: float
    bbox: BBox


@dataclass
class Page:
    """A single raster page or GIF frame, plus the blocks read from it."""

    index: int
    image: np.ndarray
    blocks: list[TextBlock] = field(default_factory=list)


@dataclass
class Document:
    """One input file or camera frame, made of ordered pages."""

    name: str
    source: str
    pages: list[Page]
