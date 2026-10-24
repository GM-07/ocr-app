"""Extract text from files without opening the window.

Camera capture stays in the desktop app. This command reads JPG, JPEG, PNG,
GIF, and PDF paths only.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from ocr_app.application.extract_text import ExtractText, InputDocument
from ocr_app.application.ports import Reader
from ocr_app.composition import build_extract_text, build_reader
from ocr_app.domain.models import ExportFormat

ReaderFactory = Callable[[], Reader]
ExtractFactory = Callable[[Reader], ExtractText]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocr",
        description=(
            "Extract text from images and PDFs. One PDF or Word file is written "
            "per input. PDF is the default."
        ),
        epilog=(
            "examples:\n"
            "  ocr scan.jpg --output-dir out\n"
            "  ocr diagram.png --output-dir out\n"
            "  ocr frames.gif --output-dir out\n"
            "  ocr report.pdf --output-dir out\n"
            "  ocr scan.jpg diagram.png frames.gif report.pdf --output-dir out\n"
            "  ocr report.pdf --output-dir out --format docx\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="One or more JPG, JPEG, PNG, GIF, or PDF files.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory where the extracted files are written.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=("pdf", "docx"),
        default="pdf",
        help="pdf (default) or docx for Word.",
    )
    return parser


def run(
    argv: Sequence[str] | None = None,
    *,
    reader_factory: ReaderFactory = build_reader,
    extract_factory: ExtractFactory = build_extract_text,
    stdout: object | None = None,
    stderr: object | None = None,
) -> int:
    """Run extraction and return a process status. 0 means every file succeeded."""
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 1

    documents = [InputDocument(name=path.stem, path=path) for path in args.paths]
    try:
        reader = reader_factory()
        use_case = extract_factory(reader)
        result = use_case.execute(
            documents,
            args.output_dir,
            ExportFormat(args.format),
            on_progress=lambda message: print(message, file=out),
        )
    except Exception as exc:
        print(f"Extraction failed: {exc}", file=err)
        return 1

    for outcome in result.outcomes:
        if outcome.error:
            print(f"{outcome.source_name}: {outcome.error}", file=err)
        elif outcome.output_path is not None:
            print(outcome.output_path, file=out)
    print(
        f"Finished. Saved {len(result.successes)} file(s) to {args.output_dir}.",
        file=out,
    )
    if result.failures:
        print(f"{len(result.failures)} file(s) failed.", file=err)
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """Console script entry point."""
    raise SystemExit(run(argv))


if __name__ == "__main__":
    main()
