"""Locate the DejaVu font embedded in exported PDFs."""

from __future__ import annotations

from pathlib import Path

_FONT_NAME = "DejaVuSans"


def dejavu_path() -> Path:
    """Return the bundled DejaVu Sans file shipped with this package."""
    path = Path(__file__).resolve().parents[1] / "fonts" / f"{_FONT_NAME}.ttf"
    if not path.is_file():
        raise FileNotFoundError(
            f"Bundled font {path.name} is missing. Reinstall the application "
            "so PDF export can embed Unicode."
        )
    return path


def dejavu_font_name() -> str:
    return _FONT_NAME
