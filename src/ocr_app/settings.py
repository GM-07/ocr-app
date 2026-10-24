"""Process-wide OCR settings.

`OCR_LANGUAGES` is the only language list. Add a language here when the
recognition backend should load another model. The default is English.
"""

from __future__ import annotations

OCR_LANGUAGES: tuple[str, ...] = ("en",)
DEFAULT_CONFIDENCE_THRESHOLD: float = 0.4
PDF_RENDER_DPI: int = 300
MIN_SHORT_SIDE_PX: int = 1500
DESKEW_MIN_DEGREES: float = 0.5
DESKEW_MAX_DEGREES: float = 15.0
